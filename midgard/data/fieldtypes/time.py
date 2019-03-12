"""A Dataset time field

"""
# Midgard imports
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.time import Time, TimeArray
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class TimeField(FieldType):

    _factory = staticmethod(Time)

    def _post_init(self, val, **field_args):
        """Initialize float field"""
        if isinstance(val, TimeArray):
            data = val
        else:
            data = self._factory(val, **field_args)

        # Check that unit is not given, overwrite with time scale
        if self._unit is not None:
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for times")
        self._unit = (data.scale,)

        # Check that the correct number of observations are given
        if len(data) != self.num_obs:
            raise ValueError(f"{self.name!r} initialized with {len(data)} values, expected {self.num_obs}")

        # Store the data as a TimeArray
        self.data = data

    @classmethod
    def _read(cls, h5_group, memo) -> "TimeField":
        """Read a TimeField from a HDF5 data source"""
        name = h5_group.attrs["fieldname"]
        time = TimeArray._read(h5_group, memo)
        return cls(num_obs=len(time), name=name, val=time)

    def _write(self, h5_group, memo) -> None:
        """Write a TimeField to a HDF5 data source"""
        h5_group.attrs["fieldname"] = self.name
        self.data._write(h5_group, memo)
