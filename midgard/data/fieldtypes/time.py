"""A Dataset time field
"""
# Standard library imports
from datetime import datetime

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.time import Time, TimeArray
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class TimeField(FieldType):

    _factory = staticmethod(Time)

    def _post_init(self, val, **field_args):
        """Initialize time field"""
        if isinstance(val, TimeArray):
            data = val
        else:
            try:
                scale = field_args.pop("scale")
            except KeyError:
                raise exceptions.InitializationError(
                    f"{self._factory.__name__}() missing 1 required positional argument: 'scale'"
                ) from None

            try:
                fmt = field_args.pop("fmt")
            except KeyError:
                raise exceptions.InitializationError(
                    f"{self._factory.__name__}() missing 1 required positional argument: 'fmt'"
                ) from None

            data = self._factory(val, scale, fmt, **field_args)

        # Check that unit is not given, overwrite with time scale
        if self._unit is not None:
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for times")
        self._unit = None

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a TimeArray
        self.data = data

    def plot_values(self, field=None):
        """Return values of the field in a form that can be plotted"""
        if not field:
            return self.data.datetime

        values = getattr(self.data, field)
        if isinstance(values, TimeArray):
            return values.datetime
        else:
            return values

    def unit(self, _):
        """Unit of fields"""
        raise exceptions.UnitError("Time fields do not have units")

    def set_unit(self, subfield, new_unit):
        """Update unit(s) of field"""
        raise exceptions.UnitError(f"Can not change the unit of a time field")

    def _prepend_empty(self, num_obs, memo):
        # Use datetime.min as "empty" value
        empty = Time([datetime.min] * num_obs, scale="utc", fmt="datetime")
        empty_id = id(empty)
        self.data = TimeArray.insert(self.data, 0, empty, memo)
        memo.pop(empty_id, None)

    def _append_empty(self, num_obs, memo):
        # Use datetime.min as "empty" value
        empty = Time([datetime.min] * num_obs, scale="utc", fmt="datetime")
        empty_id = id(empty)
        self.data = TimeArray.insert(self.data, self.num_obs, empty, memo)
        memo.pop(empty_id, None)

    def _subset(self, idx, memo):
        self.data = self.data.subset(idx, memo)

    def _extend(self, other_field, memo) -> None:
        """Add observations from another field"""
        if other_field.data.ndim != self.data.ndim:
            raise ValueError(
                f"Field '{self.name}' cannot be extended. Dimensions must be equal. ({other_field.data.ndim} != {self.data.ndim})"
            )

        self.data = TimeArray.insert(self.data, self.num_obs, other_field.data, memo)

    @classmethod
    def _read(cls, h5_group, memo) -> "TimeField":
        """Read a TimeField from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        if name in memo:
            time = memo[name]
        else:
            time = TimeArray._read(h5_group, memo)
        return cls(num_obs=len(time), name=name.split(".")[-1], val=time)

    def _write(self, h5_group, memo) -> None:
        """Write a TimeField to a HDF5 data source"""
        self.data._write(h5_group, memo)
