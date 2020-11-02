"""A dataset for handling time series data

Description:
------------

"""
# Standard library imports
from collections import UserDict
import copy
import numbers
import pathlib
from typing import Any, Callable, Dict, List, Optional, Union, Hashable, Collection

# Third party imports
import h5py
import numpy as np
import pandas as pd

# Midgard imports
import midgard
from midgard.collections import enums
from midgard.dev import exceptions
from midgard.dev import log
from midgard.data import _h5utils
from midgard.data import fieldtypes
from midgard.data import collection
from midgard.data.time import Time
from midgard.math.unit import Unit

# Version of Dataset
__version__ = "3.0"


class Dataset(collection.Collection):
    """A dataset representing fields of data arrays"""

    version = f"Dataset v{__version__}, Midgard v{midgard.__version__}"
    type = "dataset"

    def __init__(self, num_obs: int = 0) -> None:
        """Initialize an empty dataset"""
        super().__init__()
        self.meta = Meta()
        self.vars = dict()
        self._num_obs = num_obs

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

    @classmethod
    def from_dict(cls, data):
        """ Convert a simple data dictionary to a dataset.

        All entries in the dictionary must be of the same length
        """
        num_obs = len(data[list(data.keys()).pop()])  # Take num obs from one random field
        dset = cls(num_obs)
        for field in data.keys():
            if isinstance(data[field][0], numbers.Number):
                dset.add_float(field, val=data[field])
            elif isinstance(data[field][0], str):
                dset.add_text(field, val=data[field])
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

        self._extend(other_dataset, memo)
        self._num_obs += other_dataset.num_obs

        # Extend meta
        if meta_key is None:
            self.meta.update(other_dataset.meta)
        else:
            self.meta.setdefault(meta_key, dict()).update(other_dataset.meta)

    def merge_with(self, *dsets, sort_by=None, meta_key=None):
        """Merge in observations from other datasets 

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

    def difference(self, other, index_by=None, copy_self_on_error=False, copy_other_on_error=False):
        """Compute the difference between two datasets: self - other

        index_by fields will be copied from self to the difference dataset and excluded from the - operation

        Args:
            other:               Dataset to substract from self
            index_by:            Comma separated text string with name of fields
                                 (columns) that will be used to find common
                                 elements (rows).
            copy_self_on_error:  Copy value of fields in self to the difference 
                                 dataset if the - operation fails for a field
            copy_other_on_error: Copy value of fields in other to the difference
                                 dataset if the - operation fails for a field
        Returns:
            A new dataset with fields that contains the differene between fields in self and other
        """
        if index_by is None:
            if len(self) != len(other):
                raise ValueError(
                    f"Cannot compute difference between datasets with different number of observations ({self.num_obs} vs {other.num_obs})"
                )
            num_obs = len(self)
            self_idx = np.ones(len(self), dtype=bool)
            other_idx = np.ones(len(other), dtype=bool)
        else:
            _index_by = index_by.split(",")
            self_index_data = [self[n.strip()] for n in _index_by]
            other_index_data = [other[n.strip()] for n in _index_by]
            A = np.rec.fromarrays(self_index_data)
            B = np.rec.fromarrays(other_index_data)
            common, self_idx, other_idx = np.intersect1d(A, B, return_indices=True)
            num_obs = len(common)

        if num_obs == 0:
            raise ValueError(f"Nothing to differentiate. No common data found for chosen option index_by '{index_by}'.")

        result = self._difference(
            other,
            num_obs,
            self_idx,
            other_idx,
            copy_self_on_error=copy_self_on_error,
            copy_other_on_error=copy_other_on_error,
        )

        # Overwrite field index_by difference with original value
        if index_by is not None:
            _index_by = index_by.split(",")
            for index_field in _index_by:
                index_field = index_field.strip()
                try:
                    del result[index_field]
                except AttributeError:
                    # Field does not exists so no need to delete
                    pass

                index_data = self[index_field][self_idx]
                fieldtype = fieldtypes.fieldtype(index_data)
                func = fieldtypes.function(fieldtype)
                field = func(
                    num_obs=num_obs,
                    name=index_field,
                    val=index_data,
                    unit = self.field(index_field)._unit,
                    write_level = self.field(index_field)._write_level.name,
                )
                result._fields[index_field] = field

        return result

    def filter(self, idx=None, collection=None, **filters) -> np.array:
        """Filter observations"""
        idx = np.ones(self.num_obs, dtype=bool) if idx is None else idx

        for field, value in filters.items():
            if collection is not None:
                field = f"{collection}.{field}"
            try:
                field_idx = np.asarray(self[field]) == value
            except AttributeError as err:
                field_idx = np.zeros(self.num_obs, dtype=bool)
                mainfield, _, subfield = field.rpartition(".")
                container = self[mainfield] if mainfield else self
                or_fields = [f for f in container._fields if f.startswith(subfield + "_")]
                or_fields = [f"{mainfield}.{f}" if mainfield else f for f in or_fields]
                if not or_fields:
                    raise err
                for or_field in or_fields:
                    field_idx = np.logical_or(field_idx, self[or_field] == value)
            idx = np.logical_and(idx, field_idx)
        return idx

    def unique(self, field, **filters) -> np.array:
        """List unique values of a given field"""
        idx = self.filter(**filters)
        try:
            # convert to np.ndarray and find unique index (np.unique does not work on immutable arrays like TimeArray)
            _, indicies = np.unique(np.asarray(self[field][idx]), return_index=True)
            unique_idx = np.zeros(np.sum(idx), dtype=bool)
            unique_idx[indicies] = True
            return self[field][idx][unique_idx]
        except AttributeError as err:
            mainfield, _, subfield = field.rpartition(".")
            container = self[mainfield] if mainfield else self
            or_fields = [f for f in container._fields if f.startswith(subfield + "_")]
            or_fields = [f"{mainfield}.{f}" if mainfield else f for f in or_fields]
            if not or_fields:
                raise err

            def _get_idx(field_num):
                if field in filters:
                    new_filters = filters.copy()
                    value = new_filters.pop(field)
                    new_filters.update({or_fields[field_num]: value})
                    return self.filter(**new_filters)
                return idx

            idx = _get_idx(0)
            concat_field = self[or_fields[0]][idx]
            for i, or_field in enumerate(or_fields[1:], start=1):
                idx = _get_idx(i)
                concat_field = np.concatenate((concat_field, self[or_field][idx]))
                _, indicies = np.unique(concat_field, return_index=True)
            return concat_field[indicies]

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

    def add_field(self, fieldname: str, field: "FieldType") -> None:
        """Update the _fields dictionary with a field"""
        self.num_obs = field.num_obs
        super().add_field(fieldname, field)

    def __len__(self) -> int:
        """Length of dataset is equal to the number of observations"""
        return self.num_obs

    def __repr__(self) -> str:
        """A string representing the dataset"""
        info = [f"num_obs={self.num_obs}", f"num_fields={len(self.fields)}"]
        return f"{type(self).__name__}({', '.join(info)})"

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

    def _add_field(self, name, val=None, unit=None, write_level=None, **field_args):
        """Add a {field_type} field to the dataset"""
        if name in self._fields:
            raise exceptions.FieldExistsError(f"Field {name!r} already exists in dataset")

        # Create collections fields
        collection, _, field_name = name.rpartition(".")
        if collection and collection not in self._fields:
            self.add_collection(collection)
        container = getattr(self, collection) if collection else self

        # Create field
        if collection and field_name in container._fields:
            field = container._fields[field_name]
        else:
            field = func(
                num_obs=self.num_obs, name=field_name, val=val, unit=unit, write_level=write_level, **field_args
            )
        # Add field to list of fields
        container._fields[field_name] = field

    _add_field.__doc__ = _add_field.__doc__.format(field_type=field_type)

    return _add_field


for field_type in fieldtypes.names():
    setattr(Dataset, f"add_{field_type}", _add_field_factory(field_type))
