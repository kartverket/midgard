"""A Dataset time field

"""

# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.time import Time
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class TimeField(FieldType):

    _factory = staticmethod(Time)

    def _post_init(self, val):
        """Initialize float field"""
        data = self._factory(
            val,
            val2=self._field_args.get("val2"),
            scale=self._field_args.get("scale"),
            format=self._field_args.get("format"),
        )

        # Check that unit is not given, overwrite with time scale
        if self._unit is not None:
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for times")
        self._unit = (data.scale,)

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a TimeArray
        self.data = data

    @classmethod
    def _read(cls, h5_group, master) -> "TimeField":
        """Read a TimeField from a HDF5 data source"""
        print("TimeField._read not implemented")

    def _write(self, h5_group, subfields) -> None:
        """Write a TimeField to a HDF5 data source"""
        print("TimeField._write not implemented")
