"""A Dataset position delta field

"""
# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.position import PositionDelta, Position
from midgard.data._position import PositionDeltaArray
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class PositionDeltaField(FieldType):

    _factory = staticmethod(PositionDelta)

    def _post_init(self, val, **field_args):
        """Initialize position delta field"""
        if isinstance(val, PositionDeltaArray):
            if val.cls_name != "PositionDeltaArray":
                raise exceptions.InitializationError(
                    f"Argument 'val' cannot be of type '{val.cls_name}', must be of type 'PositionDeltaArray' or numpy/list"
                )
            data = val
        else:
            try:
                system = field_args.pop("system")
            except KeyError:
                raise exceptions.InitializationError(
                    f"{self._factory.__name__}() missing 1 required positional argument: 'system'"
                ) from None

            data = self._factory(val, system, **field_args)

        # Check that unit is not given, overwrite with system units
        if self._unit is not None and self._unit != data.unit():
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for position deltas")
        self._unit = data.unit()

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a PositionDeltaArray
        self.data = data

    def plot_values(self, field=None) -> np.array:
        """Return values of the field in a form that can be plotted"""
        if not field:
            return self.data.val

        values = getattr(self.data, field)
        if isinstance(values, PositionDeltaArray):
            return values.val
        else:
            return values

    def set_unit(self, subfield, new_unit):
        """Update unit(s) of field"""
        raise exceptions.UnitError(f"Can not change the unit of a position delta field")

    def _prepend_empty(self, num_obs, memo):
        empty_ref_pos = Position(
            np.full((num_obs, 3), np.nan), system=self.data.system, ellipsoid=self.data.ref_pos.ellipsoid
        )
        empty = PositionDelta(np.full((num_obs, 3), np.nan), system=self.data.system, ref_pos=empty_ref_pos)

        id_empty = id(empty)
        id_empty_ref_pos = id(empty_ref_pos)
        self.data = PositionDeltaArray.insert(self.data, 0, empty, memo)
        memo.pop(id_empty, None)
        memo.pop(id_empty_ref_pos, None)

    def _append_empty(self, num_obs, memo):
        empty_ref_pos = Position(
            np.full((num_obs, 3), np.nan), system=self.data.system, ellipsoid=self.data.ref_pos.ellipsoid
        )
        empty = PositionDelta(np.full((num_obs, 3), np.nan), system=self.data.system, ref_pos=empty_ref_pos)

        id_empty = id(empty)
        id_empty_ref_pos = id(empty_ref_pos)
        self.data = PositionDeltaArray.insert(self.data, self.num_obs, empty, memo)
        memo.pop(id_empty, None)
        memo.pop(id_empty_ref_pos, None)

    def _subset(self, idx, memo):
        self.data = self.data.subset(idx, memo)

    def _extend(self, other_field, memo) -> None:
        """Add observations from another field"""
        self.data = PositionDeltaArray.insert(self.data, self.num_obs, other_field.data, memo)

    @classmethod
    def _read(cls, h5_group, memo) -> "PositionDeltaField":
        """Read a PositionDeltaField from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        if name in memo:
            pos_delta = memo[name]
        else:
            pos_delta = PositionDeltaArray._read(h5_group, memo)
        return cls(num_obs=len(pos_delta), name=name.split(".")[-1], val=pos_delta)

    def _write(self, h5_group, memo) -> None:
        """Write a PositionDeltaField to a HDF5 data source"""
        self.data._write(h5_group, memo)
