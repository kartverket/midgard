"""A Dataset position delta field

"""

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.position import PosVelDelta
from midgard.data._position import PosVelDeltaArray
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class PositionDeltaField(FieldType):

    _subfields = PosVelDeltaArray._fieldnames()
    _factory = staticmethod(PosVelDelta)

    def _post_init(self, val, **field_args):
        """Initialize position delta field"""
        if isinstance(val, PosVelDeltaArray):
            data = val
        else:
            data = self._factory(val, **field_args)

        # Check that unit is not given, overwrite with system units
        if self._unit is not None:
            raise exceptions.InitializationError(
                "Parameter 'unit' should not be specified for position and velocity deltas"
            )
        self._unit = data.unit()

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a PosVelDeltaArray
        self.data = data

    @classmethod
    def _read(cls, h5_group, memo) -> "PositionDeltaField":
        """Read a PositionDeltaField from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        pos_delta = PosVelDeltaArray._read(h5_group, memo)
        return cls(num_obs=len(pos_delta), name=name, val=pos_delta)

    def _write(self, h5_group, memo) -> None:
        """Write a PositionDeltaField to a HDF5 data source"""
        h5_group.attrs["fieldname"] = self.name
        self.data._write(h5_group, memo)
