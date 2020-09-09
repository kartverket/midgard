"""A Dataset boolean field
"""

# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class BoolField(FieldType):

    dtype = bool
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
        if data.ndim < 1 or data.ndim > 2:
            raise ValueError(
                f"{self.name!r} initialized with {data.ndim}-dimensional data, "
                "only 1- and 2-dimensional values are supported"
            )

        # Check that unit is not given
        if self._unit is not None:
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for boolean arrays")

        # Store the data as a regular numpy array
        self.data = data

    def plot_values(self, field=None):
        """Return values of a field in a form that can be plotted

        Args:
            field:   String, the field name.

        Returns:
            Numpy-array that can be plotted by for instance matplotlib.
        """
        return self.data.astype(np.float_)

    def unit(self, _):
        """Unit of fields"""
        raise exceptions.UnitError("Boolean fields do not have units")

    def set_unit(self, subfield, new_unit):
        """Update unit(s) of field"""
        raise exceptions.UnitError(f"Can not change the unit of a boolean field")

    def _prepend_empty(self, num_obs, memo):
        empty_shape = (num_obs, *self.data.shape[1:])
        empty = np.zeros(empty_shape, dtype=bool)

        old_id = id(self.data)
        new_data = np.insert(self.data, 0, empty, axis=0)
        memo[old_id] = (self.data, new_data)
        self.data = new_data

    def _append_empty(self, num_obs, memo):
        empty_shape = (num_obs, *self.data.shape[1:])
        empty = np.zeros(empty_shape, dtype=bool)

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

        old_id = id(self.data)
        new_data = np.insert(self.data, self.num_obs, other_field.data, axis=0)
        memo[old_id] = (self.data, new_data)
        self.data = new_data

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
