"""Array with time epochs
"""
# Standard library imports
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import exceptions
from midgard.math.unit import Unit
from midgard.data._time_formats import _FORMATS, _FORMAT_UNITS

_SCALES: Dict[str, "TimeArray"] = dict()  # Populated by register_scale()
_CONVERSIONS: Dict[Tuple[str, str], Callable] = dict()  # Populated by register_scale()
_CONVERSION_HOPS: Dict[Tuple[str, str], List[str]] = dict()  # Cache for to_scale()


def register_scale(
    convert_to: Dict[str, Callable] = None, convert_from: Dict[str, Callable] = None
) -> Callable[[Callable], Callable]:
    """Decorator used to register new time scales

    The scale name is read from the .scale attribute of the Time class.

    Args:
        convert_to:    Functions used to convert to other scales.
        convert_from:  Functions used to convert from other scales.

    Returns:
        Decorator registering scale.
    """

    def wrapper(cls: Callable) -> Callable:
        name = cls.scale
        _SCALES[name] = cls

        if convert_to:
            for to_scale, converter in convert_to.items():
                _CONVERSIONS[(name, to_scale)] = converter
        if convert_from:
            for from_scale, converter in convert_from.items():
                _CONVERSIONS[(to_scale, name)] = converter
        return cls

    return wrapper


def _find_conversion_hops(hop: Tuple[str, str]) -> List[Tuple[str, str]]:
    """Calculate the hops needed to convert between scales using breadth first search"""
    start_scale, target_scale = hop
    queue = [(start_scale, [])]
    visited = set()

    while queue:
        from_scale, hops = queue.pop(0)
        for to_scale in [t for f, t in _CONVERSIONS if f == from_scale]:
            one_hop = (from_scale, to_scale)
            if to_scale == target_scale:
                return hops + [one_hop]
            if one_hop not in visited:
                visited.add(one_hop)
                queue.append((to_scale, hops + [one_hop]))

    raise exceptions.UnknownConversionError(f"Can't convert TimeArray from {start_scale!r} to {target_scale!r}")


#
# The main Time class
#
class TimeArray(np.ndarray):

    scale = None
    _scales = _SCALES
    _formats = _FORMATS
    _unit = staticmethod(Unit.unit_factory(__name__))

    def __new__(cls, val, val2=None, format="", _jd1=None, _jd2=None):
        """Create a new TimeArray"""
        if cls.scale is None:
            raise ValueError(f"{cls.__name__} cannot be instantiated. Use Time(val=..., scale={cls.scale!r}) instead")

        if format not in cls._formats:
            formats = ", ".join(cls._formats)
            raise exceptions.UnknownSystemError(f"Format {format!r} unknown. Use one of {formats}")

        # Convert to numpy array and read format
        val = np.asarray(val)
        if val.ndim == 0:
            val.resize(1)

        if val2 is not None:
            val2 = np.asarray(val2)
            if val2.shape != val.shape:
                raise ValueError(f"'val2' must have the same shape as 'val': {val.shape}")

        fmt_values = cls._formats[format](val, val2)

        # Store values on array
        obj = np.asarray(fmt_values.value).view(cls)
        obj.format = format
        obj.jd1 = fmt_values.jd1 if _jd1 is None else _jd1
        obj.jd2 = fmt_values.jd2 if _jd2 is None else _jd2
        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new TimeArray is created"""
        if obj is None:
            return

        # Validate shape
        if self.ndim == 0:
            self.resize(1)
        if self.ndim != 1:
            raise ValueError(f"{type(self).__name__!r} must be a 1-dimensional array")

        # Copy attributes from the original object
        self.format = getattr(obj, "format", None)
        self.jd1 = getattr(obj, "jd1", None)
        self.jd2 = getattr(obj, "jd2", None)

        # Freeze
        self.flags.writeable = False
        if self.jd1 is not None and self.jd2 is not None:
            self.jd1.flags.writeable = False
            self.jd2.flags.writeable = False
            self._update_hash()

    @property
    def val(self):
        return np.asarray(self)

    @property
    def SCALES(self):
        return tuple(sorted(self._scales))

    @property
    def FORMATS(self):
        return tuple(sorted(self._formats))

    @classmethod
    def _cls_scale(cls, scale: str) -> "Type[TimeArray]":
        """Check that scale is valid and return corresponding type"""
        if scale not in cls._scales:
            scales = ", ".join(sorted(cls._scales))
            raise exceptions.UnknownSystemError(f"Scale {scale!r} unknown. Use one of {scales}")

        return cls._scales[scale]

    @classmethod
    def create(
        cls,
        val: np.ndarray,
        scale: str,
        format: str,
        val2: Optional[np.ndarray] = None,
        _jd1: Optional[np.ndarray] = None,
        _jd2: Optional[np.ndarray] = None,
    ) -> "TimeArray":
        """Factory for creating TimeArrays for different scales

        See each time class for exact optional parameters.

        Args:
            val:       Array of time values.
            scale:    Name of time scale.
            pos_args:  Additional arguments used to create the TimeArray.

        Returns:
            Array with times in the given scale.
        """
        return cls._cls_scale(scale)(val, val2=val2, format=format, _jd1=_jd1, _jd2=_jd2)

    @classmethod
    def from_jds(cls, jd1: np.ndarray, jd2: np.ndarray, format: str) -> "TimeArray":
        """Create a new time array with given Julian dates and format, keep scale
        """
        fmt_value = cls._formats[format].from_jds(jd1, jd2)
        return cls(val=fmt_value, format=format, _jd1=jd1, _jd2=jd2)

    @classmethod
    def now(cls, scale="utc", format="datetime") -> "TimeArray":
        """Create a new time representing now"""
        dt_now = np.array([datetime.now()])
        jd1, jd2 = cls._formats["datetime"].to_jds(dt_now)
        return cls._cls_scale("utc").from_jds(jd1, jd2, format=format).to_scale(scale)

    def to_scale(self, scale: str) -> "TimeArray":
        """Convert time to a different scale

        Returns a new TimeArray with the same time in the new scale.

        Args:
            scale:  Name of new scale.

        Returns:
            TimeArray representing the same times in the new scale.
        """
        # Don't convert if not necessary
        if scale == self.scale:
            return self

        # Raise error for unknown scales
        if scale not in self._scales:
            scales = ", ".join(self._scales)
            raise exceptions.UnknownSystemError(f"Scale {scale!r} unknown. Use one of {scales}")

        # Convert to new scale
        hop = (self.scale, scale)
        if hop in _CONVERSIONS:
            return self._scales[scale].from_jds(*_CONVERSIONS[hop](self.jd1, self.jd2), self.format)

        if hop not in _CONVERSION_HOPS:
            _CONVERSION_HOPS[hop] = _find_conversion_hops(hop)

        jd1, jd2 = self.jd1, self.jd2
        for one_hop in _CONVERSION_HOPS[hop]:
            jd1, jd2 = _CONVERSIONS[one_hop](jd1, jd2)
        return self._scales[scale].from_jds(jd1, jd2, self.format)

    def unit(self, field: str = "") -> Tuple[str, ...]:
        """Unit of field"""
        mainfield, _, subfield = field.partition(".")

        # Units of formats
        field = self.format if not field else field
        if field in self.FORMATS:
            return _FORMAT_UNITS[field]

        # Units of properties
        else:
            return self._unit(field)

    @property
    @Unit.register(("year",))
    def year(self):
        return np.array([d.year for d in self.datetime])

    @property
    @Unit.register(("month",))
    def month(self):
        return np.array([d.month for d in self.datetime])

    @property
    @Unit.register(("day",))
    def day(self):
        return np.array([d.day for d in self.datetime])

    @property
    @Unit.register(("hour",))
    def hour(self):
        return np.array([d.hour for d in self.datetime])

    @property
    @Unit.register(("minute",))
    def minute(self):
        return np.array([d.minute for d in self.datetime])

    @property
    @Unit.register(("second",))
    def second(self):
        return np.array([d.second for d in self.datetime])

    @property
    @Unit.register(("second",))
    def sec_of_day(self):
        """Seconds since midnight

        Note   -  Does not support leap seconds

        Returns:
            Seconds since midnight
        """
        return np.array([d.hour * 60 * 60 + d.minute * 60 + d.second for d in self.datetime])

    @property
    def yydddsssss(self):
        """Text representation YY:DDD:SSSSS

        YY     - decimal year without century
        DDD    - zero padded decimal day of year
        SSSSS  - zero padded seconds since midnight

        Note   -  Does not support leap seconds

        Returns:
            Time converted to yydddssss format
        """
        return np.array([d.strftime("%y:%j:") + str(s).zfill(5) for d, s in zip(self.datetime, self.sec_of_day)])

    def _todo__iadd__(self, other):
        self.flags.writeable = True
        super().__iadd__(other)
        self.flags.writeable = False
        self._update_hash()
        return self

    def _update_hash(self):
        self._hash = hash(self.jd1.data.tobytes()) + hash(self.jd2.data.tobytes())

    def __hash__(self):
        return self._hash

    def __getattr__(self, key):
        """Get attributes with dot notation

        Add time scales and formats to attributes on Time arrays.
        """
        # Convert to a different scale
        if key in self._scales:
            return self.to_scale(key)

        # Convert to a different format
        elif key in self._formats:
            return self._formats[key].from_jds(self.jd1, self.jd2)

        # Raise error for unknown attributes
        else:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __deepcopy__(self, memo):
        """Deep copy a TimeArray
        """
        time = self.create(val=self.val.copy(), format=self.format, scale=self.scale, _jd1=self.jd1, _jd2=self.jd2)
        memo[id(time)] = time
        return time

    @classmethod
    def _read(self, h5_group, memo):
        scale = h5_group.attrs["scale"]
        format = h5_group.attrs["format"]
        val = h5_group[h5_group.attrs["fieldname"]][...]
        jd1 = h5_group["jd1"][...]
        jd2 = h5_group["jd2"][...]
        time = TimeArray.create(val, scale=scale, format=format, _jd1=jd1, _jd2=jd2)
        memo[f"{h5_group.attrs['fieldname']}"] = time
        return time

    def _write(self, h5_group, memo):
        h5_group.attrs["scale"] = self.scale
        h5_group.attrs["format"] = self.format
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        h5_field = h5_group.create_dataset("jd1", self.jd1.shape, dtype=self.jd1.dtype)
        h5_field[...] = self.data.jd1
        h5_field = h5_group.create_dataset("jd2", self.shape, dtype=self.jd2.dtype)
        h5_field[...] = self.data.jd2

        memo[id(self)] = h5_group.attrs["fieldname"]

    def __dir__(self):
        """List all fields and attributes on the Time array"""
        return super().__dir__() + list(self._scales) + list(self._formats)

    def __repr__(self):
        cls_name = type(self).__name__
        repr_str = super().__repr__()
        return repr_str.replace(f"{cls_name}(", f"{cls_name}(scale={self.scale!r}, format={self.format!r}, ")

    # Turn off arithmetic operations
    def __add__(self, other):
        return NotImplemented

    def __radd__(self, other):
        return NotImplemented

    def __iadd__(self, other):
        return NotImplemented

    def __sub__(self, other):
        return NotImplemented

    def __rsub__(self, other):
        return NotImplemented

    def __isub__(self, other):
        return NotImplemented
