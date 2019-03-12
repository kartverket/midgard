"""A Dataset position field

"""

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.position import PosVel
from midgard.data._position import PosVelArray
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class PositionField(FieldType):

    _subfields = PosVelArray._fieldnames()
    _factory = staticmethod(PosVel)

    def _post_init(self, val, **field_args):
        """Initialize float field"""
        if isinstance(val, PosVelArray):
            data = val
        else:
            data = self._factory(val=val, **field_args)

        # Check that unit is not given, overwrite with system units
        if self._unit is not None:
            raise exceptions.InitializationError(
                "Parameter 'unit' should not be specified for positions and velocities"
            )
        self._unit = data.unit()

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a PositionArray
        self.data = data

    @classmethod
    def _read(cls, h5_group, memo) -> "PositionField":
        """Read a PositionField from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        pos = PosVelArray._read(h5_group, memo)
        return cls(num_obs=len(pos), name=name, val=pos)

    def _write(self, h5_group, memo) -> None:
        """Write a PositionField to a HDF5 data source"""
        h5_group.attrs["fieldname"] = self.name
        self.data._write(h5_group, memo)
