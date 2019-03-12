"""A dataset for handling time series data

Description:
------------

"""
# Standard library imports
from collections import UserDict
import copy
import pathlib
from typing import Any, Callable, Dict, List, Optional, Union

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

# Version of Dataset
__version__ = "3.0"


class Dataset:
    """A dataset representing fields of data arrays"""

    version = f"Dataset v{__version__}, Midgard v{midgard.__version__}"

    def __init__(self, num_obs: int = 0) -> None:
        """Initialize an empty dataset"""
        self._fields = dict()
        self.meta = Meta()
        self.vars = dict()

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
            dset.vars.update(_h5utils.h5attr2dict(h5_file.attrs["vars"]))

            # Read fields
            for fieldname, fieldtype in _h5utils.h5attr2dict(h5_file.attrs["fields"]).items():
                field = fieldtypes.function(fieldtype).read(h5_file[fieldname], memo)
                if field:  # TODO: Test can be removed when all fieldtypes implement read
                    dset._fields[fieldname] = field
                    setattr(dset, fieldname, field.data)
                    memo[fieldname] = field.data

            # Read meta
            dset.meta.read(h5_file["__meta__"])
        return dset

    def write(self, file_path: Union[str, pathlib.Path], write_level: Optional[enums.WriteLevel] = None) -> None:
        """Write a dataset to file"""
        write_level = (
            min(enums.get_enum("write_level")) if write_level is None else enums.get_value("write_level", write_level)
        )
        log.debug(f"Write dataset to {file_path}")

        # Make sure directory exists
        file_path = pathlib.Path(file_path).resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Dictionary to keep track of object references
        # key: object(TimeAraay, PostionArray, etc) id, value: field_name
        memo = {}
        with h5py.File(file_path, mode="w") as h5_file:

            # Write each field
            for field_name, field in self._fields.items():
                h5_group = h5_file.create_group(field_name)
                memo[id(getattr(self, field_name))] = field_name
                field.write(h5_group, memo, write_level=write_level)

            # Write meta-information
            self.meta.write(h5_file.create_group("__meta__"))

            # Write information about dataset
            fields = {fn: f.fieldtype for fn, f in self._fields.items()}
            h5_file.attrs["fields"] = _h5utils.dict2h5attr(fields)
            h5_file.attrs["num_obs"] = self.num_obs
            h5_file.attrs["vars"] = _h5utils.dict2h5attr(self.vars)
            h5_file.attrs["version"] = self.version

    def subset(self, idx: np.array) -> None:
        """Remove observations from all fields based on index

        """
        print("subset")
        import IPython

        IPython.embed()

    def extend(self, other_dataset: "Dataset") -> None:
        """Add observations from another dataset to the end of this dataset

        """
        print("extend")
        import IPython

        IPython.embed()

    def filter(self, idx=None, **filters) -> np.array:
        """Filter observations

        TODO: default_field_suffix
        """
        idx = np.ones(self.num_obs, dtype=bool) if idx is None else idx
        for field, value in filters.items():
            idx &= self[field] == value
        return idx

    def unique(self, field, **filters) -> np.array:
        """List unique values of a given field

        TODO: default_field_suffix
        """
        idx = self.filter(**filters)
        return np.unique(self[field][idx])

    def for_each(self, key):
        """Do something for each suffix

        """
        previous_field_suffix = self.default_field_suffix
        suffixes = [f[len(key) :] for f in self.fields if f.startswith(key) and "." not in f]
        multipliers = [-1, 1] if len(suffixes) == 2 else [1] * len(suffixes)
        for multiplier, suffix in zip(multipliers, suffixes):
            self.default_field_suffix = suffix
            yield multiplier

        self.default_field_suffix = previous_field_suffix

    def unit(self, field):
        """Unit for values in a given field"""
        mainfield, _, subfield = field.partition(".")
        try:
            return self._fields[mainfield].unit(subfield)
        except KeyError:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    def plot_values(self, field: str) -> np.array:
        """Return values of a field in a form that can be plotted"""
        return self._fields[field].plot_values

    def as_dict(self, fields=None) -> Dict[str, Any]:
        """Return a representation of the dataset as a dictionary"""
        fields_dict = dict()
        for field in self._fields.values():
            fields_dict.update(field.as_dict(fields=fields))

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
        values = self[field][idx]
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
        self._default_field_suffix = suffix

    @property
    def fields(self):
        """Names of fields in the dataset"""
        all_fields = list()
        for field in self._fields.values():
            all_fields.extend(field.subfields)

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
            setattr(self, fieldname, field.data)

    def _todo__setattr__(self, key, value):
        """Protect dataset fields from being accidentally overwritten"""
        print("__setattr__")

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
            setattr(new_dset, fieldname, new_dset._fields[fieldname].data)
        new_dset.meta = copy.deepcopy(self.meta, memo)
        memo[id(self)] = new_dset
        return new_dset


class Meta(UserDict):
    def read(self, h5_group):
        pass

    def write(self, h5_group):
        pass

    def add(self, section, name, value):
        """Add information to the metaset"""
        print("add")
        import IPython

        IPython.embed()

    def add_event(self, timestamp, event_type, description):
        """Add event to the metaset"""
        print(f"add_event: {timestamp} {event_type} {description}")
        events = self.setdefault("__events__", dict())
        events.setdefault(event_type, list()).append((timestamp.isoformat(), description))
        # events.setdefault(event_type, list()).append((timestamp.utc.isot, description))

    def get_events(self, *event_types):
        """Get events from the metaset"""
        print("get_event")
        all_events = self.get("__events__", dict())
        if not event_types:
            event_types = all_events.keys()

        return sorted(set((ts, k, desc) for k, v in all_events.items() for (ts, desc) in v if k in event_types))

    def copy_from(self, other):
        self.data = copy.deepcopy(other.data)


#
# Add available fieldtypes to dataset
#
def _add_field_factory(field_type: str) -> Callable:
    func = fieldtypes.function(field_type)

    def _add_field(self, name, val, unit=None, write_level=None, suffix=None, **field_args):
        """Add a {field_type} field to the dataset"""
        if name in self._fields:
            raise exceptions.FieldExistsError(f"Field {name!r} already exists in dataset")

        # Create collections for nested fields
        collection, _, field_name = name.rpartition(".")
        if collection and collection not in self._fields:
            self.add_collection(collection, val=None)

        # Create field
        field = func(num_obs=self.num_obs, name=field_name, val=val, unit=unit, write_level=write_level, **field_args)

        # Add field to list of fields
        fields = self[collection] if collection else self._fields
        fields[field_name] = field
        setattr(self, name, field.data)

    _add_field.__doc__ = _add_field.__doc__.format(field_type=field_type)

    return _add_field


for field_type in fieldtypes.names():
    setattr(Dataset, f"add_{field_type}", _add_field_factory(field_type))
