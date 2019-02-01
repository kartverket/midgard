"""A Dataset position delta field

"""

# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.position import PositionDelta, PositionDeltaArray
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class PositionDeltaField(FieldType):

    _subfields = ()  # TODO: PositionDeltaArray._fieldnames()
    _factory = staticmethod(PositionDelta)

    def _post_init(self, val):
        """Initialize position delta field"""
        data = self._factory(val, system=self._field_args.get("system"), ref_pos=self._field_args.get("ref_pos"))

        # Check that unit is not given, overwrite with system units
        if self._unit is not None:
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for position deltas")
        self._unit = data.unit()

        # Set attributes from Dataset fields
        # for attr in data._attributes:
        #    attr_field = self._field_args.get(attr)
        #    if attr_field is None:
        #        continue

        #    try:
        #        setattr(data, attr, self._master[attr_field])
        #    except KeyError:
        #        raise mg_exceptions.FieldDoesNotExistError(
        #            f"Field {attr_field!r} is not defined on the {type(self._master).__name__}"
        #        ) from None

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a PositionDeltaArray
        self.data = data

    @classmethod
    def _read(cls, h5_group, master) -> "PositionDeltaField":
        """Read a PositionDeltaField from a HDF5 data source"""
        print("PositionDeltaField._read not implemented")

    def _write(self, h5_group, subfields) -> None:
        """Write a PositionDeltaField to a HDF5 data source"""
        print("PositionDeltaField._write not implemented")
