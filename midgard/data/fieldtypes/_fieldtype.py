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


class FieldType(abc.ABC):
    """Abstract class representing a type of field in the Dataset"""

    _subfields: List[str] = list()
    _factory = None

    def __init__(self, num_obs, name, val, unit=None, write_level=None, **field_args):
        """Create a new field"""
        self.num_obs = num_obs
        self.name = name
        self._unit = unit
        self._write_level = (
            max(enums.get_enum("write_level")) if write_level is None else enums.get_value("write_level", write_level)
        )

        # Use _post_init to set up the actual data structure
        self.data = None
        self._post_init(val, **field_args)

    @abc.abstractmethod
    def _post_init(self, val, **field_args) -> None:
        """Do post initialization and validation"""

    @property
    def fieldtype(self) -> str:
        """Get type from module name to coincide with plug-in name"""
        return self.__module__.rpartition(".")[-1]

    @classmethod
    def read(cls, h5_group, memo) -> "FieldType":
        """Read a field from a HDF5 data source"""
        field = cls._read(h5_group, memo)
        if field:  # TODO: Test can be removed when read is implemented on all fields
            field._unit = _h5utils.h5attr2tuple(h5_group.attrs["unit"])
            if not any(field._unit):
                field._unit = None
            field._write_level = enums.get_value("write_level", h5_group.attrs["write_level"])
        return field

    @classmethod
    @abc.abstractmethod
    def _read(cls, h5_group, memo) -> "FieldType":
        """Read a field from a HDF5 data source"""

    def write(self, h5_group, memo, write_level: enums.WriteLevel) -> None:
        """Write data to a HDF5 data source"""
        if self._write_level < write_level:
            return

        self._write(h5_group, memo)
        h5_group.attrs["unit"] = "" if self._unit is None else _h5utils.sequence2h5attr(self._unit)
        h5_group.attrs["write_level"] = self._write_level.name

    @abc.abstractmethod
    def _write(self, h5_group, memo) -> None:
        """Write values of field to HDF5"""

    def _fields_at_write_level(self, write_level: enums.WriteLevel) -> List[str]:
        """Names of all subfields at or above the given write level

        """
        print("at_write_level")
        return [self.name] + self._subfields

    def subset(self, idx: np.array) -> None:
        """Remove observations from a field based on index"""

    def extend(self, other_field) -> None:
        """Add observations from another field"""

    @property
    def plot_values(self) -> np.array:
        """Return values of the field in a form that can be plotted"""
        return self.data

    def as_dict(self, fields=None) -> Dict[str, Any]:
        """Return a representation of the field as a dictionary"""
        field_dict = dict()
        fields = set(self.subfields if fields is None else fields)
        for field in self.subfields:
            if field not in fields:
                continue
            name, _, attr = field.partition(".")
            if name != self.name:
                continue
            if attr:
                value = getattr(self, attr)
            else:
                value = self.values

            # Split 2-dimensional fields into separate columns
            field_name = field.replace(".", "_")
            if value.ndim == 1:
                field_dict[field_name] = value
            else:
                for i, val in enumerate(value.T):
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
