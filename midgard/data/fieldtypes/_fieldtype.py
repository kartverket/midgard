"""Abstract class used to define different types of tables for a Dataset

"""

# Standard library imports
import abc
from typing import Any, Dict, List

# Third party imports
import numpy as np
import pandas as pd

# Midgard imports
from midgard.collections import enums
from midgard.data import _h5utils
from midgard.dev import exceptions


class FieldType(abc.ABC):
    """Abstract class representing a type of field in the Dataset"""

    _subfields: List[str] = list()
    _plotfields: List[str] = list()
    _factory = None

    def __init__(self, num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args):
        """Create a new field"""
        self.num_obs = num_obs
        self.name = name
        self._unit = unit
        self._write_level = (
            max(enums.get_enum("write_level")) if write_level is None else enums.get_value("write_level", write_level)
        )

        # Use _post_init to set up the actual data structure
        self.data = None
        self.multiplier = multiplier
        self._post_init(val, **field_args)

    def new_from_field(self):
        """Create a new field with the same parameters as self

        Note: this will not create a copy of the data
        """
        cls = self.__class__
        return cls(self.num_obs, self.name, self.data, self._unit, self._write_level.name)

    @abc.abstractmethod
    def _post_init(self, val, **field_args) -> None:
        """Do post initialization and validation"""

    @property
    def fieldtype(self) -> str:
        """Get type from module name to coincide with plug-in name"""
        return self.__module__.rpartition(".")[-1]

    @property
    def write_level(self):
        return self._write_level

    @classmethod
    def read(cls, h5_group, memo) -> "FieldType":
        """Read a field from a HDF5 data source"""
        field = cls._read(h5_group, memo)
        field._unit = _h5utils.decode_h5attr(h5_group.attrs["unit"])
        if not any(field._unit):
            field._unit = None
        field._write_level = enums.get_value("write_level", h5_group.attrs["write_level"])
        try:
            # Remove try except later. Timeseries do not have multiplier for older versions
            field.multiplier = h5_group.attrs["multiplier"]
        except KeyError:
            field.multiplier = 1
        return field

    @classmethod
    @abc.abstractmethod
    def _read(cls, h5_group, memo) -> "FieldType":
        """Read a field from a HDF5 data source"""

    def write(self, h5_group, memo, write_level: enums.WriteLevel) -> None:
        """Write data to a HDF5 data source"""
        if self._write_level < write_level:
            return

        h5_group.attrs["unit"] = "" if self._unit is None else _h5utils.encode_h5attr(self._unit)
        h5_group.attrs["write_level"] = self._write_level.name
        parent_name = h5_group.parent.name[1:].replace("/", ".")
        h5_group.attrs["fieldname"] = f"{parent_name}.{self.name}" if parent_name else self.name
        h5_group.attrs["__class__"] = f"{self.data.__class__.__module__}.{self.data.__class__.__name__}"
        h5_group.attrs["multiplier"] = self.multiplier
        self._write(h5_group, memo)
        if id(self.data) not in memo:
            memo[id(self.data)] = h5_group.attrs["fieldname"]

    @abc.abstractmethod
    def _write(self, h5_group, memo) -> None:
        """Write values of field to HDF5"""

    def _fields_at_write_level(self, write_level: enums.WriteLevel) -> List[str]:
        """Names of all subfields at or above the given write level

        """
        print("at_write_level")
        return [self.name] + self._subfields

    def subset(self, idx: np.array, memo) -> None:
        """Remove observations from a field based on index"""
        self._subset(idx, memo)
        self.num_obs = len(self.data)

    def _subset(self, idx: np.array, memo) -> None:
        """Remove observations from a field based on index

            Overwrite by subclass if needed
        """
        old_id = id(self.data)
        self.data = self.data[idx]
        memo[old_id] = self.data

    def extend(self, other_field, memo) -> None:
        """Add observations from another field"""
        if not isinstance(other_field, type(self)):
            raise ValueError(f"Cannot extend field '{self.name}'. ({type(self)} != {type(other_field)})")
        self._extend(other_field, memo)
        self.num_obs = len(self.data)

    @abc.abstractmethod
    def _extend(self, other_field, memo) -> None:
        """Add observations from another field"""

    def prepend_empty(self, num_obs, memo) -> None:
        """Add num_obs empty values to the start of the field"""
        if num_obs == 0:
            return
        self._prepend_empty(num_obs, memo)
        self.num_obs = len(self.data)

    @abc.abstractmethod
    def _prepend_empty(self, num_obs, memo) -> None:
        """Add num_obs empty values to the start of the field"""

    def append_empty(self, num_obs, memo) -> None:
        """Add num_obs empty values to the start of the field"""
        if num_obs == 0:
            return
        self._append_empty(num_obs, memo)
        self.num_obs = len(self.data)

    @abc.abstractmethod
    def _append_empty(self, num_obs, memo) -> None:
        """Add num_obs empty values to the end of the field"""

    def fill_memo(self, memo):
        memo[id(self.data)] = self.name

    def plot_values(self, field=None) -> np.array:
        """Return values of the field in a form that can be plotted"""
        if not field:
            return self.data

        return getattr(self.data, field)

    def as_dict(self, fields=None) -> Dict[str, Any]:
        """Return a representation of the field as a dictionary"""
        field_dict = dict()
        fields = set(self.subfields if fields is None else fields)

        def _getattr(obj, subfield):
            name, _, attr = subfield.partition(".")
            if attr and "." in attr:
                return _getattr(getattr(obj, name), attr)
            elif attr and "." not in attr:
                return getattr(getattr(obj, name), attr)
            else:
                return getattr(obj, subfield)

        for field in self.subfields:
            if field not in fields:
                continue
            name, _, attr = field.partition(".")
            if name != self.name:
                continue

            if attr:
                try:
                    attr_value = _getattr(self.data, attr)
                    if attr_value is not None:
                        value = np.squeeze(attr_value)
                    else:
                        continue
                except exceptions.InitializationError:
                    continue
            else:
                value = np.squeeze(self.data)

            # Split 2-dimensional fields into separate columns
            field_name = field.replace(".", "_")
            if value.ndim == 1:
                field_dict[field_name] = value
            elif value.ndim == 2:
                for i, val in enumerate(value.T):
                    field_dict[f"{field_name}_{i}"] = val
            else:
                values = np.split(value.T.flatten(), value.ndim * value.ndim)
                for i, val in enumerate(values):
                    field_dict[f"{field_name}_{i}"] = val

        return field_dict

    def as_dataframe(self, fields=None, index=None) -> pd.DataFrame:
        """Return a representation of the field as a Pandas DataFrame"""
        df = pd.DataFrame.from_dict(self.as_dict(fields=fields))
        if index is not None:
            df.set_index(index, drop=True, inplace=True)

        return df

    def unit(self, subfield):
        """Unit(s) of field"""
        if not subfield:
            return self._unit
        else:
            return self.data.unit(subfield)

    @property
    def subfields(self):
        """Names of field and all subfields"""
        return [self.name] + [f"{self.name}.{f}" for f in sorted(self._subfields)]

    @property
    def plot_fields(self):
        """Name of all plotable subfields"""
        if not self._plotfields:
            return self.subfields
        return [self.name] + [f"{self.name}.{f}" for f in sorted(self._plotfields)]

    # def __getitem__(self, key):
    #     """Pass item access on to the underlying data structure"""
    #     return self.data[key]

    # def __getattr__(self, key):
    #     """Get a subfield from field or attribute from underlying data structure"""
    #     return getattr(self.data, key)

    # def __dir__(self):
    #     """List all subfields and attributes on the field"""
    #     return dir(super()) + dir(self.data)

    # def __len__(self) -> int:
    #     """Length of dataset is equal to number of observations"""
    #     return self.num_obs

    # def __repr__(self) -> str:
    #     """A string representing the field

    #     """
    #     return repr(self.data)

    # def __str__(self) -> str:
    #     """A string describing the field

    #     """
    #     return str(self.data)
