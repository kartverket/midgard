"""A Dataset float field

"""
# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.dev import exceptions
from midgard.dev import plugins
from midgard.math.unit import Unit


@plugins.register
class FloatField(FieldType):

    dtype = float
    _factory = staticmethod(np.array)

    def _post_init(self, val, **field_args):
        """Initialize float field"""
        if field_args:
            raise exceptions.InitializationError(
                f"{self._factory.__name__}() received unknown argument {','.join(field_args.keys())}"
            )
        if isinstance(val, np.ndarray) and val.dtype == self.dtype:
            data = val
        else:
            data = self._factory(val, dtype=self.dtype)

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # We only support 1- and 2-dimensional arrays
        # if data.ndim < 1 or data.ndim > 2:
        #    raise ValueError(
        #        f"{self.name!r} initialized with {data.ndim}-dimensional data, "
        #        "only 1- and 2-dimensional values are supported"
        #    )

        # Handle units
        if self._unit is not None:
            self._unit = self._validate_unit(data, self._unit)

        # Store the data as a regular numpy array
        self.data = data

    def set_unit(self, _, new_unit):
        self._unit = self._validate_unit(self.data, new_unit)

    def _prepend_empty(self, num_obs, memo):
        empty_shape = (num_obs, *self.data.shape[1:])
        empty = np.full(empty_shape, np.nan)

        old_id = id(self.data)
        new_data = np.insert(self.data, 0, empty, axis=0)
        memo[old_id] = (self.data, new_data)
        self.data = new_data

    def _append_empty(self, num_obs, memo):
        empty_shape = (num_obs, *self.data.shape[1:])
        empty = np.full(empty_shape, np.nan)

        old_id = id(self.data)
        new_data = np.insert(self.data, self.num_obs, empty, axis=0)
        memo[old_id] = (self.data, new_data)
        self.data = new_data

    def _extend(self, other_field, memo) -> None:
        """Add observations from another field"""
        if other_field.data.ndim != self.data.ndim:
            raise ValueError(
                f"Field '{self.name}' cannot be extended. Dimensions must be equal. ({other_field.data.ndim} != {self.data.ndim})"
            )

        try:
            factors = [Unit(from_unit, to_unit) for from_unit, to_unit in zip(other_field._unit, self._unit)]
        except exceptions.UnitError:
            raise exceptions.UnitError(
                f"Cannot extend field '{self.name}'. {other_field._unit} cannot be converted to {self._unit}"
            )
        except TypeError:
            if self._unit == other_field._unit == None:
                factors = 1
            else:
                raise exceptions.UnitError(
                    f"Cannot extend field '{self.name}'. {other_field._unit} cannot be converted to {self._unit}"
                )
        old_id = id(self.data)
        self.data = np.insert(self.data, self.num_obs, other_field.data * factors, axis=0)
        memo[old_id] = self.data

    @classmethod
    def _read(cls, h5_group, memo) -> "FieldType":
        """Read a field from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        if name in memo:
            val = memo[name]
        else:
            val = h5_group[name][...]
        return cls(num_obs=len(val), name=name.split(".")[-1], val=val)

    def _write(self, h5_group, _) -> None:
        """Write data to a HDF5 data source"""
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.data.shape, dtype=self.data.dtype)
        h5_field[...] = self.data
