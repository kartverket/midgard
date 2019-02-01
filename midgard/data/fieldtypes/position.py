"""A Dataset position field

"""

# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.position import Position, PositionArray
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class PositionField(FieldType):

    _subfields = PositionArray._fieldnames()
    _factory = staticmethod(Position)

    def _post_init(self, val):
        """Initialize float field"""
        data = self._factory(val=val, system=self._field_args.get("system"))

        # Check that unit is not given, overwrite with system units
        if self._unit is not None:
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for positions")
        self._unit = data.unit()

        # Set attributes from Dataset fields
        for attr in data._attributes:
            attr_field = self._field_args.get(attr)
            if attr_field is None:
                continue

            try:
                setattr(data, attr, self._master[attr_field])
            except KeyError:
                raise exceptions.FieldDoesNotExistError(
                    f"Field {attr_field!r} is not defined on the {type(self._master).__name__}"
                ) from None

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a PositionArray
        self.data = data

    @classmethod
    def _read(cls, h5_group, master) -> "PositionField":
        """Read a PositionField from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        system = h5_group.attrs["system"]
        val = h5_group[name][...]
        return cls(num_obs=len(val), master=master, name=name, val=val, system=system)

    def _write(self, h5_group) -> None:
        """Write a PositionField to a HDF5 data source"""
        h5_group.attrs["fieldname"] = self.name
        h5_group.attrs["system"] = self.data.system
        h5_field = h5_group.create_dataset(self.name, self.data.shape, dtype=self.data.dtype)
        h5_field[...] = np.asarray(self.data)
