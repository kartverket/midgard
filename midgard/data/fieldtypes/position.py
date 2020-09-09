"""A Dataset position field

"""
# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.position import Position
from midgard.data._position import PositionArray
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class PositionField(FieldType):

    _factory = staticmethod(Position)

    def _post_init(self, val, **field_args):
        """Initialize float field"""

        if isinstance(val, PositionArray):
            if val.cls_name != "PositionArray":
                raise exceptions.InitializationError(
                    f"Argument 'val' cannot be of type '{val.cls_name}', must be of type 'PositionArray' or numpy/list"
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
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for positions")
        self._unit = data.unit()

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a PositionArray
        self.data = data


    def plot_values(self, field=None) -> np.array:
        """Return values of the field in a form that can be plotted"""
        if not field:
            return self.data.val

        values = getattr(self.data, field)
        if isinstance(values, PositionArray):
            return values.val
        else:
            return values

    def set_unit(self, subfield, new_unit):
        """Update unit(s) of field"""
        raise exceptions.UnitError(f"Can not change the unit of a position field")

    def _prepend_empty(self, num_obs, memo):
        empty = Position(np.full((num_obs, 3), np.nan), system=self.data.system, ellipsoid=self.data.ellipsoid)
        id_empty = id(empty)
        self.data = PositionArray.insert(self.data, 0, empty, memo)
        memo.pop(id_empty, None)

    def _append_empty(self, num_obs, memo):
        empty = Position(np.full((num_obs, 3), np.nan), system=self.data.system, ellipsoid=self.data.ellipsoid)
        id_empty = id(empty)
        self.data = PositionArray.insert(self.data, self.num_obs, empty, memo)
        memo.pop(id_empty, None)

    def _extend(self, other_field, memo) -> None:
        """Add observations from another field"""
        if self.data.ellipsoid != other_field.data.ellipsoid:
            raise ValueError(
                f"Field '{self.name}' cannot be extended. Ellipsoid must be equal. ({other_field.data.ellipsoid} != {self.data.ellipsoid})"
            )
        self.data = PositionArray.insert(self.data, self.num_obs, other_field.data, memo)

    def _subset(self, idx, memo):
        self.data = self.data.subset(idx, memo)

    @classmethod
    def _read(cls, h5_group, memo) -> "PositionField":
        """Read a PositionField from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        if name in memo:
            pos = memo[name]
        else:
            pos = PositionArray._read(h5_group, memo)
        return cls(num_obs=len(pos), name=name.split(".")[-1], val=pos)

    def _write(self, h5_group, memo) -> None:
        """Write a PositionField to a HDF5 data source"""
        self.data._write(h5_group, memo)
