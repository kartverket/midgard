"""A Dataset sigma field

"""

# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.sigma import SigmaArray
from midgard.dev import plugins


@plugins.register
class SigmaField(FieldType):

    _subfields = ["sigma"]
    _factory = staticmethod(SigmaArray)

    def _post_init(self, val):
        """Initialize float field"""
        data = self._factory(val, sigma=self._field_args.get("sigma"))

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # We only support 1- and 2-dimensional arrays
        if data.ndim < 1 or data.ndim > 2:
            raise ValueError(
                f"{self.name!r} initialized with {data.ndim}-dimensional data, "
                "only 1- and 2-dimensional values are supported"
            )

        # Handle units
        if self._unit is not None:
            cols = 1 if data.ndim == 1 else data.shape[1]
            if isinstance(self._unit, str):
                self._unit = (self._unit,) * cols
            elif len(self._unit) != cols:
                raise ValueError(f"Number of units ({len(self._units)}) must equal number of columns ({cols})")

        # Store the data as a SigmaArray
        self.data = data

    @classmethod
    def _read(cls, h5_group, master) -> "SigmaField":
        """Read a SigmaField from a HDF5 data source"""
        print("SigmaField._read not implemented")

    def _write(self, h5_group, subfields) -> None:
        """Write a SigmaField to a HDF5 data source"""
        print("SigmaField._write not implemented")
