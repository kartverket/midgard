"""A Dataset sigma field
"""
# Third party imports
import numpy as np

# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.sigma import SigmaArray
from midgard.dev import exceptions
from midgard.dev import plugins
from midgard.math.unit import Unit


@plugins.register
class SigmaField(FieldType):

    _factory = staticmethod(SigmaArray)

    def _post_init(self, val, **field_args):
        """Initialize sigma field"""
        if isinstance(val, SigmaArray):
            data = val
        else:
            try:
                sigma = field_args.pop("sigma")
            except KeyError:
                raise exceptions.InitializationError(
                    f"{self._factory.__name__}() missing 1 required positional argument: 'sigma'"
                ) from None

            if field_args:
                raise exceptions.InitializationError(
                    f"{self._factory.__name__}() received unknown argument {','.join(field_args.keys())}"
                )

            data = self._factory(val, sigma)

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
            self._unit = self._validate_unit(data, self._unit)
            data.set_unit(self._unit)

        # Store the data as a SigmaArray
        self.data = data

    def set_unit(self, subfield, new_unit):
        """Update unit(s) of field"""
        if not subfield:
            self._unit = self._validate_unit(self.data, new_unit)
            self.data.set_unit(self._unit)
        else:
            raise exceptions.UnitError(f"Can not change unit of the subfields of a sigma field. Subfields are the same unit as the sigma field")

    def _prepend_empty(self, num_obs, memo):
        empty_shape = (num_obs, *self.data.shape[1:])
        empty = SigmaArray(np.full(empty_shape, np.nan), sigma=None)

        empty_id = id(empty)
        self.data = SigmaArray.insert(self.data, 0, empty, memo)
        memo.pop(empty_id, None)

    def _append_empty(self, num_obs, memo):
        empty_shape = (num_obs, *self.data.shape[1:])
        empty = SigmaArray(np.full(empty_shape, np.nan), sigma=None)

        empty_id = id(empty)
        self.data = SigmaArray.insert(self.data, self.num_obs, empty, memo)
        memo.pop(empty_id, None)

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

        self.data = SigmaArray.insert(self.data, self.num_obs, other_field.data * factors, memo)

    @classmethod
    def _read(cls, h5_group, memo) -> "SigmaField":
        """Read a SigmaField from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        if name in memo:
            val = memo[name]
        else:
            val = h5_group[name][...]
            sigma = h5_group["sigma"][...]
        return cls(num_obs=len(val), name=name.split(".")[-1], val=val, sigma=sigma)

    def _write(self, h5_group, _) -> None:
        """Write a SigmaField to a HDF5 data source"""
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.data.shape, dtype=self.data.dtype)
        h5_field[...] = self.data
        h5_field = h5_group.create_dataset("sigma", self.data.shape, dtype=self.data.sigma.dtype)
        h5_field[...] = self.data.sigma
