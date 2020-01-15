"""A dataset for handling time series data

Description:
------------

"""
# Standard library imports
from collections import UserDict
import copy
import pathlib
from typing import Any, Callable, Dict, List, Optional, Union, Hashable, Collection

# Third party imports
import h5py
import numpy as np
import pandas as pd

# Midgard imports
import midgard
from midgard.collections import enums
from midgard.dev import console
from midgard.dev import exceptions
from midgard.dev import log
from midgard.data import _h5utils
from midgard.data import fieldtypes
from midgard.data.time import Time
from midgard.math.unit import Unit

# Version of Dataset
__version__ = "3.0"


class Dataset:
    """A dataset representing fields of data arrays"""

    version = f"Dataset v{__version__}, Midgard v{midgard.__version__}"

    def __init__(self, num_obs: int = 0) -> None:
        """Initialize an empty dataset"""
        self.meta = Meta()
        self.vars = dict()

        self._fields = dict()
        self._num_obs = num_obs
        self._default_field_suffix = None

    @classmethod
    def read(cls, file_path: Union[str, pathlib.Path]) -> "Dataset":
        """Read a dataset from file"""

        log.debug(f"Read dataset from {file_path}")

        # Dictionary to keep track of references in the data structure
        # key: field_name, value: object (TimeArray, PositionArray, etc)
        memo = {}

        # Read fields from file
        with h5py.File(file_path, mode="r") as h5_file:
            num_obs = h5_file.attrs["num_obs"]
            dset = cls(num_obs=num_obs)
            dset.vars.update(_h5utils.decode_h5attr(h5_file.attrs["vars"]))

            # Read fields
            for fieldname, fieldtype in _h5utils.decode_h5attr(h5_file.attrs["fields"]).items():
                field = fieldtypes.function(fieldtype).read(h5_file[fieldname], memo)
                dset._fields[fieldname] = field
                memo[fieldname] = field.data

            # Read meta
            dset.meta.read(h5_file["__meta__"])
        return dset

    def _construct_memo(self):
        """ Constructs dictionary

        Dictionary to keep track of object references
            key: object(TimeArray, PostionArray, etc) id,
            value: field_name
        """
        memo = dict()
        for field in self._fields.values():
            field.fill_memo(memo)
        return memo

    def write(self, file_path: Union[str, pathlib.Path], write_level: Optional[enums.WriteLevel] = None) -> None:
        """Write a dataset to file"""
        write_level = (
            min(enums.get_enum("write_level")) if write_level is None else enums.get_value("write_level", write_level)
        )
        log.debug(f"Write dataset to {file_path} with {write_level}")

        # Make sure directory exists
        file_path = pathlib.Path(file_path).resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)

        memo = self._construct_memo()
        with h5py.File(file_path, mode="w") as h5_file:

            # Write each field
            for field_name, field in self._fields.items():
                if field.write_level >= write_level:
                    h5_group = h5_file.create_group(field_name)
                    field.write(h5_group, memo, write_level=write_level)

            # Write meta-information
            self.meta.write(h5_file.create_group("__meta__"))

            # Write information about dataset
            fields = {fn: f.fieldtype for fn, f in self._fields.items() if f.write_level >= write_level}
            h5_file.attrs["fields"] = _h5utils.encode_h5attr(fields)
            h5_file.attrs["num_obs"] = self.num_obs
            h5_file.attrs["vars"] = _h5utils.encode_h5attr(self.vars)
            h5_file.attrs["version"] = self.version

    def subset(self, idx: np.array) -> None:
        """Remove observations from all fields based on index"""
        # Dictionary to keep track of object references
        # key: object id before slicing, value: object after slicing
        memo = dict()

        for field in self._fields.values():
            field.subset(idx, memo)

        self._num_obs = int(np.sum(idx))

    def extend(self, other_dataset: "Dataset", meta_key=None) -> None:
        """Add observations from another dataset to the end of this dataset"""

        # Dictionary to keep track of object references
        # key: object id before extending, value: (object before extending, object after extending)
        # object before extending is kept in the memo dict to make sure it is not garbage collected during the
        # extension process.
        memo = dict()

        only_in_other = set(other_dataset._fields.keys()) - set(self._fields.keys())
        only_in_self = set(self._fields.keys()) - set(other_dataset._fields.keys())

        for field_name, field in other_dataset._fields.items():

            if field_name in only_in_other:
                # self, num_obs, name, val, unit=None, write_level=None, **field_args
                # TODO write level, unit.. make from_field?
                new_field = field.new_from_field()
                new_field.prepend_empty(self.num_obs, memo)
                self._fields[field_name] = new_field
            else:
                self._fields[field_name].extend(other_dataset._fields[field_name], memo)

        for field_name in only_in_self:
            self._fields[field_name].append_empty(other_dataset.num_obs, memo)

        self._num_obs += other_dataset.num_obs

        # Extend meta
        if meta_key is None:
            self.meta.update(other_dataset.meta)
        else:
            self.meta.setdefault(meta_key, dict()).update(other_dataset.meta)

    def merge_with(self, *dsets, sort_by=None, meta_key=None):
        """Merge in observations from other datasets 

        Note that this is quite strict in terms of which datasets can extend each other. They must have exactly the
        same tables. Tables containing several independent fields (e.g. float, text) may have different fields, in
        which case fields from both datasets are included. If a field is only defined in one dataset, it will get
        "empty" values for the observations in the dataset it is not defined.

        Args:
            other_dset (Sequence): List of Datasets
            sort_by (str):         Name of field to be used for sorting the merged data
            meta_key (str):        Dictionary key for introduction of an additional level in dictionary.
        """

        for dset in dsets:
            self.extend(dset, meta_key)

        memo = dict()
        if sort_by is not None:
            sort_idx = np.argsort(np.asarray(getattr(self, sort_by)))

            for field in self._fields.values():
                field.subset(sort_idx, memo)

    def filter(self, idx=None, collection=None, **filters) -> np.array:
        """Filter observations"""
        idx = np.ones(self.num_obs, dtype=bool) if idx is None else idx
        for field, value in filters.items():
            try:
                if collection is None:
                    field_idx = np.asarray(self[field]) == value
                else:
                    field_idx = np.asarray(self[f"{collection}.{field}"]) == value
            except AttributeError as err:
                field_idx = np.zeros(self.num_obs, dtype=bool)
                or_fields = [f for f in self._fields if f.startswith(field + "_")]
                if not or_fields:
                    raise err
                for or_field in or_fields:
                    if collection is None:
                        field_idx = np.logical_or(field_idx, self[or_field] == value)
                    else:
                        field_idx = np.logical_or(field_idx, self[collection][or_field] == value)
            idx = np.logical_and(idx, field_idx)
        return idx

    def unique(self, field, collection=None, **filters) -> np.array:
        """List unique values of a given field"""
        idx = self.filter(collection=collection, **filters)
        container = self

        if collection is not None:
            container = self[collection]

        try:
            # convert to np.ndarray and find unique index (np.unique does not work on immutable arrays like TimeArray)
            _, indicies = np.unique(np.asarray(container[field][idx]), return_index=True)
            unique_idx = np.zeros(np.sum(idx), dtype=bool)
            unique_idx[indicies] = True
            return container[field][idx][unique_idx]
        except AttributeError as err:
            or_fields = [f for f in self._fields if f.startswith(field + "_")]
            if not or_fields:
                raise err
            # TODO: test how this work for immutable arrays
            concat_field = container[or_fields[0]][idx]
            for or_field in or_fields[1:]:
                concat_field = np.concatenate((concat_field, container[or_field][idx]))
                _, indicies = np.unique(concat_field, return_index=True)
            return concat_field[indicies]

    def for_each_suffix(self, key):
        """Do something for each suffix"""
        *collections, key = key.split(".")
        container = self
        for c in collections:
            container = container._fields[c].data
        previous_field_suffix = self.default_field_suffix
        sm = [(f[len(key) :], container._fields[f].multiplier) for f in container._fields if f.startswith(key)]
        for suffix, multiplier in sm:
            if suffix and not suffix[1:].isdigit():
                continue
            self.default_field_suffix = suffix
            yield multiplier

        self.default_field_suffix = previous_field_suffix

    def for_each_fieldtype(self, fieldtype):
        for field in self._fields.values():
            module = field.__module__.split(".")[-1]
            if fieldtype == module:
                yield field.data

    def unit(self, field):
        """Unit for values in a given field"""
        mainfield, _, subfield = field.partition(".")
        try:
            return self._fields[mainfield].unit(subfield)
        except KeyError:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    def unit_short(self, field):
        units = self.unit(field)
        if units is None:
            return tuple()
        return tuple([Unit.symbol(u) for u in units])

    def plot_values(self, field: str) -> np.array:
        """Return values of a field in a form that can be plotted"""

        mainfield, _, subfield = field.partition(".")
        return self._fields[mainfield].plot_values(subfield)

    def as_dict(self, fields=None) -> Dict[str, Any]:
        """Return a representation of the dataset as a dictionary"""
        fields_dict = dict()
        for field in self._fields.values():
            field_dict = field.as_dict(fields=fields)
            fields_dict.update(field_dict)

        return fields_dict

    def as_dataframe(self, fields=None, index=None) -> pd.DataFrame:
        """Return a representation of the dataset as a Pandas DataFrame"""
        df = pd.DataFrame.from_dict(self.as_dict(fields=fields))
        if index is not None:
            df.set_index(index, drop=True, inplace=True)

        return df

    def apply(self, func: Callable, field: str, **filters: Any) -> Any:
        """Apply a function to a field"""
        idx = self.filter(**filters)
        values = []
        for _ in self.for_each_suffix(field):
            values.append(self[field][idx])
        values = np.hstack(values)
        return func(values)

    def rms(self, field: str, **filters: Any) -> float:
        """Calculate Root Mean Square of a field"""
        return self.apply(lambda val: np.sqrt(np.mean(np.square(val))), field, **filters)

    def mean(self, field: str, **filters: Any) -> float:
        """Calculate mean of a field"""
        return self.apply(np.mean, field, **filters)

    def std(self, field: str, **filters: Any) -> float:
        """Calculate the standard deviation of a field"""
        return self.apply(np.std, field, **filters)

    def count(self, field: str, **filters: Any) -> int:
        """Count the number of unique values in a field"""
        return len(self.unique(field, **filters))

    def num(self, **filters: Any) -> int:
        """Number of observations satisfying the filters"""
        return sum(self.filter(**filters))

    @property
    def num_obs(self) -> int:
        """Number of observations in dataset"""
        return self._num_obs

    @num_obs.setter
    def num_obs(self, value: int):
        """Set the number of observations in dataset"""
        if self._fields and value != self._num_obs:
            raise AttributeError(
                "Can not change number of observations after fields are added. Use 'subset' or 'extend' instead"
            )

        self._num_obs = value

    @property
    def default_field_suffix(self):
        """Default field suffix

        """
        if self._default_field_suffix is None:
            return ""
        return self._default_field_suffix

    @default_field_suffix.setter
    def default_field_suffix(self, suffix):
        """Set the default field suffix

        TODO: Could we possibly use a context manager for these things?

              E.g.:
                   with dset.suffix("1"):
                       models.calculate(dset)
        """
        if suffix:
            suffix = str(suffix)
            if not suffix.startswith("_"):
                suffix = "_" + suffix
        else:
            suffix = None

        for collection in self.for_each_fieldtype("collection"):
            collection.default_field_suffix = suffix
        self._default_field_suffix = suffix

    @property
    def fields(self):
        """Names of fields in the dataset"""
        all_fields = list()
        for field in self._fields.values():
            all_fields.extend(field.subfields)

        return sorted(all_fields)

    @property
    def plot_fields(self):
        """Names of fields in the dataset that would make sense to plot"""
        all_fields = list()
        for field in self._fields.values():
            all_fields.extend(field.plot_fields)

        return sorted(all_fields)

    def update_from(self, other: "Dataset") -> None:
        """Transfers dataset fields from other Dataset to this Dataset

        This will not create a copy of the data in the other Dataset
        """
        self.num_obs = other.num_obs
        for fieldname, field in other._fields.items():
            if fieldname in self._fields:
                raise exceptions.FieldExistsError(f"Field {fieldname!r} already exists in dataset")
            self._fields.update({fieldname: field})
        self.meta.update(other.meta)

    def __getitem__(self, key):
        """Get a field from the dataset using dict-notation"""
        mainfield, _, subfield = key.partition(".")
        if not subfield:
            return getattr(self, key)
        else:
            return getattr(getattr(self, mainfield), subfield)

    def __getattr__(self, key):
        """Get a field from the dataset using dot-notation"""
        if key == "_fields" or key == "default_field_suffix":
            return self.__getattribute__(key)

        container = self
        field = key
        if "." in key:
            collection, _, field = key.partition(".")
            container = self[collection]
        if container.default_field_suffix is not None:
            field_with_suffix = field + container.default_field_suffix
            if field_with_suffix in container._fields:
                return container._fields[field_with_suffix].data
        if field in container._fields:
            return container._fields[field].data

            # Raise error for unknown attributes
        else:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}")

    def __setattr__(self, key, value):
        """Protect dataset fields from being accidentally overwritten"""
        try:
            if key in self._fields:
                if id(value) != id(self._fields[key].data):
                    raise AttributeError(
                        "Can't set attribute '{}' on '{}' object, use dset.{}[:] instead"
                        "".format(key, type(self).__name__, key)
                    )
        except AttributeError:
            # if self._fields is not set yet
            pass
        super().__setattr__(key, value)

    def _todo__delitem__(self, key):
        """Delete a field from the dataset"""
        print("__delitem__")

    def _todo__delattr__(self, key):
        """Delete a field from the dataset"""
        print("__delattr__")

    def __dir__(self):
        """List all fields and attributes on the dataset"""
        return super().__dir__() + self.fields

    def _ipython_key_completions_(self) -> List[str]:
        """Tab completion for dict-style lookups in ipython

        See http://ipython.readthedocs.io/en/stable/config/integrating.html

        Returns:
            Fieldnames in the dataset.
        """
        return self.fields

    def __bool__(self) -> bool:
        """Dataset is truthy if it has fields with observations"""
        return self.num_obs > 0 and len(self._fields) > 0

    def __len__(self) -> int:
        """Length of dataset is equal to the number of observations"""
        return self.num_obs

    def __repr__(self) -> str:
        """A string representing the dataset"""
        info = [f"num_obs={self.num_obs}", f"num_fields={len(self.fields)}"]  # TODO: Based on some vars
        return f"{type(self).__name__}({', '.join(info)})"

    def __str__(self) -> str:
        """A string describing the dataset"""
        fields = console.fill(f"Fields: {', '.join(self.fields)}", hanging=8)
        return f"{self!r}\n{fields}"

    def __deepcopy__(self, memo):
        new_dset = Dataset(num_obs=self.num_obs)
        for fieldname, field in self._fields.items():
            new_dset._fields[fieldname] = copy.deepcopy(field, memo)
        new_dset.meta = copy.deepcopy(self.meta, memo)
        memo[id(self)] = new_dset
        return new_dset


class Meta(UserDict):
    def read(self, h5_group):
        """Read meta data from hdf5-file"""
        for k, v in h5_group.attrs.items():
            self.data[k] = _h5utils.decode_h5attr(v)

    def write(self, h5_group):
        """Write meta data to hdf5-file"""
        for k, v in self.items():
            h5_group.attrs[k] = _h5utils.encode_h5attr(v)

    def add(self, name: Hashable, value: Collection, section: Optional[Hashable] = None) -> None:
        """Add information to the metaset"""
        meta_section = self.data.setdefault(section, dict()) if section else self.data
        meta_section[name] = value

    def add_event(self, time: "Time", event_type: str, description: str) -> None:
        """Add event to the metaset"""
        events = self.setdefault("__events__", dict())
        events.setdefault(event_type, list()).append((time.utc.isot, description))

    def get_events(self, *event_types: List[str]):
        """Get events from the metaset"""
        all_events = self.get("__events__", dict())
        if not event_types:
            event_types = all_events.keys()

        return sorted(
            set(
                (Time(ts, scale="utc", fmt="isot"), k, desc)
                for k, v in all_events.items()
                for (ts, desc) in v
                if k in event_types
            )
        )


#
# Add available fieldtypes to dataset
#
def _add_field_factory(field_type: str) -> Callable:
    func = fieldtypes.function(field_type)

    def _add_field(self, name, val=None, unit=None, write_level=None, suffix=None, **field_args):
        """Add a {field_type} field to the dataset"""
        if name in self._fields:
            raise exceptions.FieldExistsError(f"Field {name!r} already exists in dataset")

        # Create collections for nested fields
        collection, _, field_name = name.rpartition(".")
        if collection and collection not in self._fields:
            self.add_collection(collection)

        # Create field
        field = func(num_obs=self.num_obs, name=field_name, val=val, unit=unit, write_level=write_level, **field_args)
        # Add field to list of fields
        fields = getattr(self, collection) if collection else self._fields
        fields[field_name] = field

    _add_field.__doc__ = _add_field.__doc__.format(field_type=field_type)

    return _add_field


for field_type in fieldtypes.names():
    setattr(Dataset, f"add_{field_type}", _add_field_factory(field_type))
