"""Array with time epochs
"""
# Standard library imports
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple, Any, TypeVar
from functools import lru_cache

try:
    import importlib.resources as importlib_resources  # Python >= 3.7
except ImportError:
    import importlib_resources  # Python <= 3.6:  pip install importlib_resources

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import exceptions
from midgard.math.unit import Unit
from midgard.math.constant import constant

_SCALES: Dict[str, Dict[str, Callable]] = dict()  # Populated by register_scale()
_CONVERSIONS: Dict[str, Dict[Tuple[str, str], Callable]] = dict()  # Populated by register_scale()
_CONVERSION_HOPS: Dict[str, Dict[Tuple[str, str], List[str]]] = dict()  # Cache for to_scale()
_FORMATS: Dict[str, Dict[str, Callable]] = dict()  # Populated by register_format()
_FORMAT_UNITS: Dict[str, Dict[str, str]] = dict()  # Populated by register_format()

# Type specification: scalar float or numpy array
np_float = TypeVar("np_float", float, np.ndarray)


#######################################################################################################################
# Module functions
#######################################################################################################################


def read_tai_utc():
    package, _, _ = __name__.rpartition(".")
    with importlib_resources.path(package, "_taiutc.txt") as path:
        return np.genfromtxt(
            path,
            names=["start", "end", "offset", "ref_epoch", "factor"],
            comments="#",
            dtype=("f8", "f8", "f8", "f8", "f8"),
            autostrip=True,
        )


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
        _SCALES[cls.cls_name][name] = cls

        conversions = _CONVERSIONS.setdefault(cls.cls_name, dict())
        if convert_to:
            for to_scale, converter in convert_to.items():
                conversions[(name, to_scale)] = converter
        if convert_from:
            for from_scale, converter in convert_from.items():
                conversions[(from_scale, name)] = converter
        return cls

    return wrapper


def register_format(cls: Callable) -> Callable:
    """Decorator used to register new time formats

    The format name is read from the .format attribute of the TimeFormat class.
    """
    name = cls.fmt
    _FORMATS[cls.cls_name][name] = cls
    _FORMAT_UNITS[cls.cls_name][name] = cls.unit

    return cls


def _find_conversion_hops(cls: str, hop: Tuple[str, str]) -> List[Tuple[str, str]]:
    """Calculate the hops needed to convert between scales using breadth first search"""
    start_scale, target_scale = hop
    queue = [(start_scale, [])]
    visited = set()

    if start_scale == target_scale:
        return [hop]

    while queue:
        from_scale, hops = queue.pop(0)
        for to_scale in [t for f, t in _CONVERSIONS[cls] if f == from_scale]:
            one_hop = (from_scale, to_scale)
            if to_scale == target_scale:
                return hops + [one_hop]
            if one_hop not in visited:
                visited.add(one_hop)
                queue.append((to_scale, hops + [one_hop]))

    raise exceptions.UnknownConversionError(f"Can't convert TimeArray from {start_scale!r} to {target_scale!r}")


######################################################################################################################
# Time classes
######################################################################################################################


class TimeBase(np.ndarray):
    """Base class for TimeArray and TimeDeltaArray"""

    scale = None

    def __new__(cls, val, fmt, val2=None, _jd1=None, _jd2=None):
        """Create a new TimeArray"""
        if cls.scale is None:
            raise ValueError(f"{cls.__name__} cannot be instantiated. Use Time(val=..., scale={cls.scale!r}) instead")

        if fmt not in cls._formats():
            formats = ", ".join(cls._formats())
            raise exceptions.UnknownSystemError(f"Format {fmt!r} unknown. Use one of {formats}")

        # Convert to numpy array and read format
        fmt_values = cls._formats()[fmt](val, val2, cls.scale)

        val = np.asarray(val)
        if val2 is not None:
            val2 = np.asarray(val2)
            if val2.shape != val.shape:
                raise ValueError(f"'val2' must have the same shape as 'val': {val.shape}")

            if val2.ndim == 0:
                val2 = val2.item()

        if val.ndim == 0:
            val = val.item()

        # Store values on array
        obj = np.asarray(fmt_values.value).view(cls)
        jd1 = fmt_values.jd1 if _jd1 is None else _jd1
        jd2 = fmt_values.jd2 if _jd2 is None else _jd2

        # Validate shape
        fmt_ndim = cls._formats()[fmt].ndim
        if obj.ndim > fmt_ndim:
            raise ValueError(
                f"{type(self).__name__!r} must be a {fmt_ndim - 1} or {fmt_ndim}-dimensional array for format type {obj_fmt}"
            )

        # Freeze
        if isinstance(jd1, np.ndarray):
            jd1.flags.writeable = False
        if isinstance(jd2, np.ndarray):
            jd2.flags.writeable = False
        super(TimeBase, obj).__setattr__("fmt", fmt)
        super(TimeBase, obj).__setattr__("jd1", jd1)
        super(TimeBase, obj).__setattr__("jd2", jd2)

        if isinstance(obj, np.ndarray):
            obj.flags.writeable = False
        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new TimeArray is created"""
        if obj is None:
            return

        obj_fmt = getattr(obj, "fmt", None)

        # Copy attributes from the original object
        super().__setattr__("fmt", obj_fmt)

        jd1_sliced = getattr(obj, "_jd1_sliced", None)
        if jd1_sliced is not None:
            super().__setattr__("jd1", jd1_sliced)
        else:
            super().__setattr__("jd1", getattr(obj, "jd1", None))

        jd2_sliced = getattr(obj, "_jd2_sliced", None)
        if jd2_sliced is not None:
            super().__setattr__("jd2", jd2_sliced)
        else:
            super().__setattr__("jd2", getattr(obj, "jd2", None))

        # Validate shape for arrays not created with __new__
        if obj_fmt and self.ndim > 1:
            fmt_ndim = self._formats()[obj_fmt].ndim
            if self.ndim > fmt_ndim:
                raise ValueError(
                    f"{type(self).__name__!r} must be a {fmt_ndim - 1} or {fmt_ndim}-dimensional array for format type {obj_fmt}"
                )

        # Freeze
        self.flags.writeable = False
        if self.jd1 is not None and self.jd2 is not None:
            if isinstance(self.jd1, np.ndarray):
                self.jd1.flags.writeable = False
            if isinstance(self.jd2, np.ndarray):
                self.jd2.flags.writeable = False

    def __lt__(self, other):
        return self.jd < other.jd

    @lru_cache()
    def to_scale(self, scale: str) -> "TimeBase":
        """Convert to a different scale
 
        Returns a new array with the same time in the new scale.
 
        Args:
            scale:  Name of new scale.
 
        Returns:
            TimeBase representing the same times in the new scale.
        """
        # Don't convert if not necessary
        if scale == self.scale:
            return self

        # Raise error for unknown scales
        if scale not in self._scales():
            scales = ", ".join(self._scales())
            raise exceptions.UnknownSystemError(f"Scale {scale!r} unknown. Use one of {scales}")

        # Simplified conversion if time is None
        if self.shape == () and self.item() == None: # time is None
            return _SCALES[self.cls_name][scale](val=None, fmt=self.fmt, _jd1=None, _jd2=None)

        # Convert to new scale
        hop = (self.scale, scale)
        if hop in _CONVERSIONS[self.cls_name]:
            jd1, jd2 = _CONVERSIONS[self.cls_name][hop](self)
            try:
                return self._scales()[scale].from_jds(jd1, jd2, self.fmt)
            except ValueError:
                # Given format does not exist for selected time scale, use default jd
                return self._scales()[scale].from_jds(jd1, jd2, "jd")
        if hop not in _CONVERSION_HOPS.setdefault(self.cls_name, {}):
            _CONVERSION_HOPS[self.cls_name][hop] = _find_conversion_hops(self.cls_name, hop)

        converted_time = self
        for one_hop in _CONVERSION_HOPS[self.cls_name][hop]:
            jd1, jd2 = _CONVERSIONS[self.cls_name][one_hop](converted_time)
            try:
                converted_time = self._scales()[one_hop[-1]].from_jds(jd1, jd2, self.fmt)
            except ValueError:
                # Given format does not exist for selected time scale, use default jd
                converted_time = self._scales()[one_hop[-1]].from_jds(jd1, jd2, "jd")
        return converted_time

    def subset(self, idx, memo):
        """Create a subset"""
        old_id = id(self)
        if old_id in memo:
            return memo[old_id]

        new_time = self._scales()[self.scale](
            np.asarray(self)[idx], fmt=self.fmt, _jd1=self.jd1[idx], _jd2=self.jd2[idx]
        )
        memo[old_id] = new_time
        return new_time

    @classmethod
    def insert(cls, a, pos, b, memo):
        """Insert b into a at index pos"""
        id_a = id(a)
        if id_a in memo:
            return memo[id_a][-1]

        id_b = id(b)
        if id_b in memo:
            return memo[id_b][-1]

        b = b if a.scale == b.scale else getattr(b, a.scale)
        b_formatted = np.asarray(b) if a.fmt == b.fmt else getattr(b, a.fmt)
        val = np.insert(np.asarray(a), pos, b_formatted)
        jd1 = np.insert(a.jd1, pos, b.jd1)
        jd2 = np.insert(a.jd2, pos, b.jd2)
        new_time = cls._scales()[a.scale](val, fmt=a.fmt, _jd1=jd1, _jd2=jd2)
        memo[id(a)] = (a, new_time)
        memo[id(b)] = (b, new_time)
        return new_time

    @property
    def val(self):
        return np.asarray(self)

    @classmethod
    def _cls_scale(cls, scale: str) -> "Type[TimeArray]":
        """Check that scale is valid and return corresponding type"""
        if scale not in cls._scales():
            scales = ", ".join(sorted(cls._scales()))
            raise exceptions.UnknownSystemError(f"Scale {scale!r} unknown. Use one of {scales}")

        return cls._scales()[scale]

    @classmethod
    def create(
        cls,
        val: np.ndarray,
        scale: str,
        fmt: str,
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
        return cls._cls_scale(scale)(val, val2=val2, fmt=fmt, _jd1=_jd1, _jd2=_jd2)

    @classmethod
    def from_jds(cls, jd1: np.ndarray, jd2: np.ndarray, fmt: str) -> "TimeArray":
        """Create a new time array with given Julian dates and format, keep scale
        """
        fmt_value = cls._formats()[fmt].from_jds(jd1, jd2, cls.scale)
        return cls(val=fmt_value, fmt=fmt, _jd1=jd1, _jd2=jd2)


    def fieldnames(self):
        """Return list of valid attributes for this object"""
        # Pick one element to avoid doing calculations on a large array 
        obj = self if len(self) == 1 else self[0]

        scales_and_formats = []
        for scale in obj._scales():
            try:
                _find_conversion_hops(self.cls_name, (obj.scale, scale))
                # Add scales
                scales_and_formats.append(scale)
                scale_time = getattr(obj, scale)
                fmt_cls = obj.cls_name.replace("Array", "Format")
                for fmt in _FORMATS.get(fmt_cls, {}):
                    # Add system fields
                    try:
                        fmt_time = getattr(scale_time, fmt)
                        if isinstance(fmt_time, tuple) and hasattr(fmt_time, "_fields"):
                            for f in fmt_time._fields:
                                scales_and_formats.append(f"{scale}.{fmt}.{f}")
                        else:
                            scales_and_formats.append(f"{scale}.{fmt}")
                    except ValueError:
                        pass  # Skip formats that are invalid for that scale
            except exceptions.UnknownConversionError:
                pass  # Skip systems that cannot be converted to

        return scales_and_formats

    @lru_cache()
    def plot_fields(self):
        """Returns list of attributes that can be plotted"""
        obj = self if len(self) == 1 else self[0]
        fieldnames = set(self.fieldnames())
        text_fields = set()
        for f in fieldnames:
            attr_value = getattr(obj, f)
            if isinstance(attr_value, np.ndarray) and attr_value.dtype.type is np.str_:
                text_fields.add(f)
            elif isinstance(attr_value, str):
                text_fields.add(f)

        return list(fieldnames - text_fields)

    def unit(self, field: str = "") -> Tuple[str, ...]:
        """Unit of field"""
        # mainfield, _, subfield = field.partition(".")

        # Units of formats
        field = self.fmt if not field else field
        if field in self._formats():
            return _FORMAT_UNITS[field]

        # Units of properties
        else:
            return self._unit

    @lru_cache()
    def to_format(self, fmt: str):
        return self._formats()[fmt].from_jds(self.jd1, self.jd2, scale=self.scale)

    def __hash__(self):
        try:
            return hash(self.jd1.data.tobytes()) + hash(self.jd2.data.tobytes())
        except AttributeError:
            return hash(str(self.jd1)) + hash(str(self.jd2))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return np.all(self.jd1 == other.jd1) and np.all(self.jd2 == other.jd2)
        else:
            return NotImplemented

    def __getattr__(self, key):
        """Get attributes with dot notation

        Add time scales and formats to attributes on Time arrays.
        """
        if "." in key:
            mainfield, _, subfield = key.partition(".")
            return getattr(getattr(self, mainfield), subfield)

        # Convert to a different scale
        if key in self._scales():
            return self.to_scale(key)

        # Convert to a different format
        elif key in self._formats():
            return self.to_format(key)

        # Raise error for unknown attributes
        else:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __len__(self):
        fmt_ndim = self._formats()[self.fmt].ndim
        return int(self.size / fmt_ndim)

    def __setattr__(self, name, value):
        raise AttributeError(f"{self.__class__.__name__} object does not support item assignment ")

    def __copy__(self):
        return self.create(val=self.val.copy(), fmt=self.fmt, scale=self.scale, _jd1=self.jd1, _jd2=self.jd2)

    def __deepcopy__(self, memo):
        """Deep copy a TimeArray
        """
        time = self.create(val=self.val.copy(), fmt=self.fmt, scale=self.scale, _jd1=self.jd1, _jd2=self.jd2)
        memo[id(time)] = time
        return time

    # Override numpys copy method # Might not be needed for numpy 1.16 or higher
    copy = __copy__

    def __getitem__(self, item):
        """Update _jd*_sliced with correct shape, used by __array_finalize__"""
        fmt_ndim = self._formats()[self.fmt].ndim
        if isinstance(item, tuple) and fmt_ndim > 1 and len(item) > 1:
            # Only use item row to slice jds
            super().__setattr__("_jd1_sliced", self.jd1[item[-1]])
            super().__setattr__("_jd2_sliced", self.jd2[item[-1]])
        else:
            if isinstance(self.jd1, np.ndarray):
                super().__setattr__("_jd1_sliced", self.jd1[item])
            if isinstance(self.jd2, np.ndarray):
                super().__setattr__("_jd2_sliced", self.jd2[item])
        if isinstance(item, (int, np.int_)):
            return self._scales()[self.scale].from_jds(self._jd1_sliced, self._jd2_sliced, self.fmt)
        return super().__getitem__(item)

    @classmethod
    def _read(cls, h5_group, memo):
        scale = h5_group.attrs["scale"]
        fmt = h5_group.attrs["fmt"]
        jd1 = h5_group["jd1"][...]
        jd2 = h5_group["jd2"][...]
        time = cls._cls_scale(scale).from_jds(jd1, jd2, fmt)
        memo[f"{h5_group.attrs['fieldname']}"] = time
        return time

    def _write(self, h5_group, memo):
        h5_group.attrs["scale"] = self.scale
        h5_group.attrs["fmt"] = self.fmt
        h5_field = h5_group.create_dataset("jd1", self.jd1.shape, dtype=self.jd1.dtype)
        h5_field[...] = self.jd1
        h5_field = h5_group.create_dataset("jd2", self.shape, dtype=self.jd2.dtype)
        h5_field[...] = self.jd2

    def __dir__(self):
        """List all fields and attributes on the Time array"""
        return super().__dir__() + list(self._scales()) + list(self._formats())

    def __repr__(self):
        cls_name = type(self).__name__
        repr_str = super().__repr__()
        return repr_str.replace(f"{cls_name}(", f"{cls_name}(scale={self.scale!r}, fmt={self.fmt!r}, ")


#
# The main Time class
#
class TimeArray(TimeBase):
    """Base class for time objects. Is immutable to allow the data to be hashable"""

    cls_name = "TimeArray"
    type = "time"
    _SCALES.setdefault(cls_name, dict())
    _unit = None

    @classmethod
    def now(cls, scale="utc", fmt="datetime") -> "TimeArray":
        """Create a new time representing now"""
        jd1, jd2 = cls._formats()["datetime"].to_jds(datetime.now(), scale=scale)
        return cls._cls_scale("utc").from_jds(jd1, jd2, fmt=fmt).to_scale(scale)

    @classmethod
    def empty_from(cls, other: "TimeArray") -> "TimeArray":
        """Create a new time of the same type as other but with empty(datetime.min) values
        """
        return _SCALES[other.scale](np.full(other.shape, fill_value=datetime.min), fmt="datetime")

    @classmethod
    def _scales(cls):
        return _SCALES.setdefault(cls.cls_name, dict())

    @classmethod
    def _formats(cls):
        return _FORMATS["TimeFormat"]

    @property
    @Unit.register(("year",))
    @lru_cache()
    def year(self):
        if isinstance(self.datetime, datetime):
            return self.datetime.year
        return np.array([d.year for d in self.datetime])

    @property
    @lru_cache()
    @Unit.register(("month",))
    def month(self):
        if isinstance(self.datetime, datetime):
            return self.datetime.month
        return np.array([d.month for d in self.datetime])

    @property
    @lru_cache()
    @Unit.register(("day",))
    def day(self):
        if isinstance(self.datetime, datetime):
            return self.datetime.day
        return np.array([d.day for d in self.datetime])

    @property
    @lru_cache()
    @Unit.register(("hour",))
    def hour(self):
        if isinstance(self.datetime, datetime):
            return self.datetime.hour
        return np.array([d.hour for d in self.datetime])

    @property
    @lru_cache()
    @Unit.register(("minute",))
    def minute(self):
        if isinstance(self.datetime, datetime):
            return self.datetime.minute
        return np.array([d.minute for d in self.datetime])

    @property
    @lru_cache()
    @Unit.register(("second",))
    def second(self):
        if isinstance(self.datetime, datetime):
            return self.datetime.second
        return np.array([d.second for d in self.datetime])

    @property
    @lru_cache()
    @Unit.register(("day",))
    def doy(self):
        if isinstance(self.datetime, datetime):
            return self.datetime.timetuple().tm_yday
        return np.array([d.timetuple().tm_yday for d in self.datetime])

    @property
    @lru_cache()
    @Unit.register(("second",))
    def sec_of_day(self):
        """Seconds since midnight

        Note   -  Does not support leap seconds

        Returns:
            Seconds since midnight
        """
        if isinstance(self.datetime, datetime):
            return self.datetime.hour * 60 * 60 + self.datetime.minute * 60 + self.datetime.second
        return np.array([d.hour * 60 * 60 + d.minute * 60 + d.second for d in self.datetime])

    @property
    @lru_cache()
    def mean(self):
        """Mean time

        Returns:
            Time:    Time object containing the mean time
        """
        if self.size == 1:
            return self

        return self._cls_scale(self.scale)(np.mean(self.utc.jd), fmt="jd")

    @property
    @lru_cache()
    def min(self):
        return self[np.argmin(self.jd)]

    @property
    @lru_cache()
    def max(self):
        return self[np.argmax(self.jd)]

    @property
    @lru_cache()
    def jd_int(self):
        """Integer part of Julian Day

        To ensure consistency, we therefore add two properties `jd_int` and `jd_frac` where the integer part is
        guaranteed to be a "half-integer" (e.g. 2457617.5) and the fractional part is guaranteed to be a float in the
        range [0., 1.). The parts are calculated from `jd1` and `jd2` to preserve precision.

        Returns:
            Numpy-float scalar or array with (half-)integer part of Julian Day.
        """
        return self.jd1 - self._jd_delta

    @property
    @lru_cache()
    def jd_frac(self):
        """Fractional part of Julian Day

        See the docstring of `jd_int` for more information.

        Returns:
            Numpy-float scalar or array with fractional part of Julian Day, in the range [0., 1.).
        """
        return self.jd2 + self._jd_delta

    @property
    @lru_cache()
    def _jd_delta(self):
        """Delta between jd1 and jd_int

        This is a helper function used by `jd_int` and `jd_frac` to find the difference to `jd1` and `jd2`
        respectively. See the docstring of `jd_int` for more information.

        Returns:
            Numpy-float scalar or array with difference between `jd1` and the integer part of Julian Day.
        """
        return self.jd1 - (np.floor(self.jd - 0.5) + 0.5)

    @property
    @lru_cache()
    def mjd_int(self):
        """Integer part of Modified Julian Day

        In general, we have that MJD = JD - 2400000.5. See the docstring of `jd_int` for more information.

        Returns:
            Numpy-float scalar or array with the integer part of Modified Julian Day.
        """
        return self.jd_int - 2_400_000.5

    @property
    @lru_cache()
    def mjd_frac(self):
        """Fractional part of Modified Julian Day

        See the docstring of `jd_int` for more information. The way we have defined `jd_int` and `jd_frac` means that
        `mjd_frac` will be equal to `jd_frac`.

        Returns:
            Numpy-float scalar or array with the fractional part of Modified Julian Day, in the range [0., 1.).
        """
        return self.jd_frac

    def __add__(self, other):
        """self + other"""
        if self.scale != other.scale:
            return NotImplemented

        if isinstance(other, TimeDeltaArray):
            # time + timedelta
            jd2 = self.jd2 + other.days
            return self.from_jds(self.jd1, jd2, self.fmt)

        elif isinstance(other, TimeArray):
            # time1 + time2 does not make sense
            return NotImplemented

        return NotImplemented

    def __sub__(self, other):
        """self - other"""
        if self.scale != other.scale:
            return NotImplemented

        if isinstance(other, TimeDeltaArray):
            # time - timedelta -> time
            jd1 = self.jd1 - other.jd1
            jd2 = self.jd2 - other.jd2
            return self.from_jds(self.jd1, jd2, self.fmt)

        elif isinstance(other, TimeArray):
            # time - time -> timedelta
            jd1 = self.jd1 - other.jd1
            jd2 = self.jd2 - other.jd2
            fmt = "timedelta" if self.fmt == other.fmt == "datetime" else "jd"
            return _SCALES["TimeDeltaArray"][self.scale].from_jds(jd1, jd2, fmt)

        return NotImplemented

    # Turn off remaining arithmetic operations
    def __rsub__(self, _):
        """ other - self"""
        return NotImplemented

    def __radd__(self, _):
        """other + self"""
        return NotImplemented

    def __iadd__(self, _):
        """Immutable object does not support this operation"""
        return NotImplemented

    def __isub__(self, _):
        """Immutable object does not support this operation"""
        return NotImplemented


class TimeDeltaArray(TimeBase):
    """Base class for time delta objects. Is immutable to allow the data to be hashable"""

    cls_name = "TimeDeltaArray"
    type = "time_delta"
    _SCALES.setdefault(cls_name, dict())
    _unit = None

    @classmethod
    def empty_from(cls, other: "TimeDeltaArray") -> "TimeDeltaArray":
        """Create a new time of the same type as other but with empty(datetime.min) values
        """
        return _SCALES[other.scale](np.full(other.shape, fill_value=timedelta(seconds=0)), fmt="timedelta")

    @lru_cache()
    def plot_fields(self):
        """Returns list of attributes that can be plotted"""
        obj = self if len(self) == 1 else self[0]
        scales_and_formats = []
        try:
            # Add scale
            scales_and_formats.append(obj.scale)
            fmt_cls = obj.cls_name.replace("Array", "Format")
            for fmt in _FORMATS.get(fmt_cls, {}):
                # Add system fields
                try:
                    fmt_time = getattr(obj, fmt)
                    if isinstance(fmt_time, np.ndarray) and fmt_time.dtype.type is np.str_:
                        # Skip string formats
                        continue
                    if isinstance(fmt_time, str):
                        # Skip string formats
                        continue
                    scales_and_formats.append(f"{obj.scale}.{fmt}")
                except ValueError:
                    pass  # Skip formats that are invalid for that scale
        except exceptions.UnknownConversionError:
            pass  # Skip systems that cannot be converted to

        return scales_and_formats

    @classmethod
    def _scales(cls):
        return _SCALES.setdefault(cls.cls_name, dict())

    @classmethod
    def _formats(cls):
        return _FORMATS["TimeDeltaFormat"]

    def __add__(self, other):
        """self + other """
        if self.scale != other.scale:
            return NotImplemented

        if isinstance(other, TimeDeltaArray):
            # timedelta + timedelta -> timedelta
            jd1 = self.jd1 + other.jd2
            jd2 = self.jd1 + other.jd2
            return self.from_jds(jd1, jd2, fmt=self.fmt)

        elif isinstance(other, TimeArray):
            # timedelta + time -> time
            jd1 = self.jd1 + other.jd1
            jd2 = self.jd2 + other.jd2
            return other.from_jds(jd1, jd2, fmt=other.fmt)

        return NotImplemented

    def __sub__(self, other):
        """self - other"""
        if self.scale != other.scale:
            return NotImplemented

        if isinstance(other, TimeArray):
            # timedelta - time -> time
            jd1 = self.jd1 - other.jd1
            jd2 = self.jd2 - other.jd2
            return other.from_jds(jd1, jd2, fmt=other.fmt)

        elif isinstance(other, TimeDeltaArray):
            # timedelta - timedelta -> timedelta
            jd1 = self.jd1 - other.jd1
            jd2 = self.jd1 - other.jd2
            return self.from_jds(jd1, jd2, fmt=self.fmt)

        return NotImplemented

    # Turn off remaining arithmetic operations
    def __radd__(self, _):
        """other - self"""
        return NotImplemented

    def __rsub__(self, _):
        """other - self"""
        return NotImplemented

    def __iadd__(self, _):
        """Immutable object does not support this operation"""
        return NotImplemented

    def __isub__(self, _):
        """Immutable object does not support this operation"""
        return NotImplemented


#######################################################################################################################
# Time scales
#######################################################################################################################

# Time deltas


def delta_tai_utc(time: "TimeArray") -> "np_float":
    try:
        idx = [np.argmax(np.logical_and(t.jd >= _TAIUTC["start"], t.jd < _TAIUTC["end"])) for t in time]
    except TypeError:
        idx = np.argmax(np.logical_and(time.jd >= _TAIUTC["start"], time.jd < _TAIUTC["end"]))

    delta = _TAIUTC["offset"][idx] + (time.mjd - _TAIUTC["ref_epoch"][idx]) * _TAIUTC["factor"][idx]

    if time.scale == "utc":
        return delta * Unit.seconds2day
    else:
        # time.scale is tai
        tmp_utc_jd = time.tai.jd - delta * Unit.seconds2day
        tmp_utc_mjd = time.tai.mjd - delta * Unit.seconds2day

        try:
            idx = [np.argmax(np.logical_and(t >= _TAIUTC["start"], t < _TAIUTC["end"])) for t in tmp_utc_jd]
        except TypeError:
            idx = np.argmax(np.logical_and(tmp_utc_jd >= _TAIUTC["start"], tmp_utc_jd < _TAIUTC["end"]))

        delta = _TAIUTC["offset"][idx] + (tmp_utc_mjd - _TAIUTC["ref_epoch"][idx]) * _TAIUTC["factor"][idx]
        return -delta * Unit.seconds2day


def delta_tai_tt(time: "TimeArray") -> "np_float":
    delta = 32.184 * Unit.seconds2day
    if time.scale == "tt":
        return -delta
    else:
        # time.scale is tai
        return delta


def delta_tcg_tt(time: "TimeArray") -> "np_float":
    dt = time.jd1 - constant.T_0_jd1 + time.jd2 - constant.T_0_jd2
    if time.scale == "tt":
        return constant.L_G / (1 - constant.L_G) * dt
    else:
        # time.scale is tcg
        return -constant.L_G * dt


def delta_gps_tai(time: "TimeArray") -> "np_float":
    delta = 19 * Unit.seconds2day
    if time.scale == "gps":
        return delta
    else:
        # time.scale is tai
        return -delta


#
# Time scale conversions
#
def _utc2tai(utc: "TimeArray") -> ("np_float", "np_float"):
    """Convert UTC to TAI"""
    return utc.jd1, utc.jd2 + delta_tai_utc(utc)


def _tai2utc(tai: "TimeArray") -> ("np_float", "np_float"):
    """Convert TAI to UTC"""
    return tai.jd1, tai.jd2 + delta_tai_utc(tai)


def _tai2tt(tai: "TimeArray") -> ("np_float", "np_float"):
    """Convert TAI to UTC"""
    return tai.jd1, tai.jd2 + delta_tai_tt(tai)


def _tt2tai(tt: "TimeArray") -> ("np_float", "np_float"):
    """Convert TT to TAI"""
    return tt.jd1, tt.jd2 + delta_tai_tt(tt)


def _tt2tcg(tt: "TimeArray") -> ("np_float", "np_float"):
    """Convert TT to TCG"""
    return tt.jd1, tt.jd2 + delta_tcg_tt(tt)


def _tcg2tt(tcg: "TimeArray") -> ("np_float", "np_float"):
    """Convert TCG to TT"""
    return tcg.jd1, tcg.jd2 + delta_tcg_tt(tcg)


def _gps2tai(gps: "TimeArray") -> ("np_float", "np_float"):
    """Convert GPS to TAI"""
    return gps.jd1, gps.jd2 + delta_gps_tai(gps)


def _tai2gps(tai: "TimeArray") -> ("np_float", "np_float"):
    """Convert TAI to GPS"""
    return tai.jd1, tai.jd2 + delta_gps_tai(tai)


#
# Time scales
#
@register_scale(convert_to=dict(tai=_utc2tai))
class UtcTime(TimeArray):

    scale = "utc"


@register_scale(convert_to=dict(utc=_tai2utc, tt=_tai2tt, gps=_tai2gps))
class TaiTime(TimeArray):

    scale = "tai"


@register_scale(convert_to=dict(tt=_tcg2tt))
class TcgTime(TimeArray):

    scale = "tcg"


@register_scale(convert_to=dict(tai=_gps2tai))
class GpsTime(TimeArray):

    scale = "gps"


@register_scale(convert_to=dict(tai=_tt2tai, tcg=_tt2tcg))
class TtTime(TimeArray):

    scale = "tt"


#
# Time Delta scales
#
@register_scale(convert_to=dict())
class UtcTimeDelta(TimeDeltaArray):

    scale = "utc"


@register_scale(convert_to=dict())
class TaiTimeDelta(TimeDeltaArray):

    scale = "tai"


@register_scale(convert_to=dict())
class TcgTimeDelta(TimeDeltaArray):

    scale = "tcg"


@register_scale(convert_to=dict())
class GpsTimeDelta(TimeDeltaArray):

    scale = "gps"


@register_scale(convert_to=dict())
class TtTimeDelta(TimeDeltaArray):

    scale = "tt"


######################################################################################################################
# Formats
######################################################################################################################


#
# Time formats
#
class TimeFormat:

    cls_name = "TimeFormat"
    _FORMATS.setdefault(cls_name, dict())
    _FORMAT_UNITS.setdefault(cls_name, dict())
    fmt = None
    unit = None
    ndim = 1
    day2seconds = Unit.day2seconds
    week2days = Unit.week2days

    def __init__(self, val, val2=None, scale=None):
        """Convert val and val2 to Julian days"""
        self.scale = scale
        if val is None:
            self.jd1 = None
            self.jd2 = None
        elif np.asarray(val).size == 0 and np.asarray(val).ndim == 1: # Empty array
            self.jd1 = np.array([])
            self.jd2 = np.array([])
        else:
            self.jd1, self.jd2 = self.to_jds(val, val2=val2, scale=scale)

    @classmethod
    def to_jds(cls, val, val2=None, scale=None):
        """Convert val and val2 to Julian days and set the .jd1 and .jd2 attributes"""
        if val is None and val2 is None:
            return None, None
        return cls._to_jds(val, val2, scale)

    @classmethod
    def _to_jds(cls, val, val2, scale):
        """Convert val and val2 to Julian days and set the .jd1 and .jd2 attributes"""
        raise NotImplementedError

    @classmethod
    def from_jds(cls, jd1, jd2, scale):
        """Convert Julian days to the right format"""
        if jd1 is None and jd2 is None:
            return None
        return cls._from_jds(jd1, jd2, scale)

    @classmethod
    def _from_jds(cls, jd1, jd2, scale):
        """Convert Julian days to the right format"""
        raise NotImplementedError

    @property
    def value(self):
        """Convert Julian days to the right format"""
        if self.jd1 is None and self.jd1 is None:
            return None
        return self.from_jds(self.jd1, self.jd2, self.scale)


class TimeDeltaFormat(TimeFormat):
    """Base class for Time Delta formats"""

    cls_name = "TimeDeltaFormat"
    _FORMATS.setdefault(cls_name, dict())
    _FORMAT_UNITS.setdefault(cls_name, dict())


@register_format
class TimeJD(TimeFormat):

    fmt = "jd"
    unit = ("day",)

    @classmethod
    def _to_jds(cls, val, val2, scale=None):
        if val2 is None:
            try:
                val2 = np.zeros(val.shape)
            except AttributeError:
                val2 = 0
        val = np.asarray(val)
        _delta = val - (np.floor(val + val2 - 0.5) + 0.5)
        jd1 = val - _delta
        jd2 = val2 + _delta
        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        return jd1 + jd2


@register_format
class TimeMJD(TimeFormat):
    """Modified Julian Date time format.

    This represents the number of days since midnight on November 17, 1858.
    For example, 51544.0 in MJD is midnight on January 1, 2000.
    """

    fmt = "mjd"
    unit = ("day",)
    _mjd0 = 2_400_000.5

    @classmethod
    def _to_jds(cls, val, val2, scale=None):
        if val2 is None:
            try:
                val2 = np.zeros(val.shape)
            except AttributeError:
                val2 = 0
        val = np.asarray(val)
        _delta = val - (np.floor(val + val2 - 0.5) + 0.5)
        jd1 = cls._mjd0 + val - _delta
        jd2 = val2 + _delta
        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        return jd1 - cls._mjd0 + jd2


@register_format
class TimeDateTime(TimeFormat):

    fmt = "datetime"
    unit = None
    _jd2000 = 2_451_544.5
    _dt2000 = datetime(2000, 1, 1)

    @classmethod
    def _to_jds(cls, val, val2=None, scale=None):
        try:
            if val2 is not None:
                val = np.asarray(val) + np.asarray(val2)
            return np.array([cls._dt2jd(dt) for dt in val]).T
        except TypeError:
            if val2 is not None:
                val = val + val2
            return cls._dt2jd(val)

    @classmethod
    @lru_cache()
    def _dt2jd(cls, dt):
        """Convert one datetime to one Julian date pair"""
        delta = dt - cls._dt2000
        jd1 = cls._jd2000 + delta.days

        delta -= timedelta(days=delta.days)
        jd2 = delta.total_seconds() / cls.day2seconds

        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        try:
            return np.array([cls._jd2dt(j1, j2) for j1, j2 in zip(jd1, jd2)])
        except TypeError:
            return cls._jd2dt(jd1, jd2)

    @classmethod
    @lru_cache()
    def _jd2dt(cls, jd1, jd2):
        """Convert one Julian date to a datetime"""
        return cls._dt2000 + timedelta(days=jd1 - cls._jd2000) + timedelta(days=jd2)


@register_format
class TimePlotDate(TimeFormat):
    """Matplotlib date format

    Matplotlib represents dates using floating point numbers specifying the number
    of days since 0001-01-01 UTC, plus 1.  For example, 0001-01-01, 06:00 is 1.25,
    not 0.25. Values < 1, i.e. dates before 0001-01-01 UTC are not supported.
    """

    fmt = "plot_date"
    unit = None
    _jd0001 = 1721424.5  # julian day 2001-01-01 minus 1

    @classmethod
    def _to_jds(cls, val, val2=None, scale=None):
        if val2 is None:
            try:
                val2 = np.zeros(val.shape)
            except AttributeError:
                val2 = 0

        _delta = val - (np.floor(val + val2 - 0.5) + 0.5)
        jd1 = cls._jd0001 + val - _delta
        jd2 = val2 + _delta
        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        return jd1 - cls._jd0001 + jd2


@register_format
class TimeGPSWeekSec(TimeFormat):
    """GPS weeks and seconds."""

    fmt = "gps_ws"
    unit = ("week", "second")
    _jd19800106 = 2_444_244.5
    WeekSec = namedtuple("week_sec", ["week", "seconds", "day"])
    ndim = len(WeekSec._fields)

    @classmethod
    def _to_jds(cls, val, val2, scale=None):
        if scale != "gps":
            raise ValueError(f"Format {cls.fmt} is only available for time scale gps")

        if isinstance(val, cls.WeekSec):
            week = np.asarray(val.week)
            sec = np.asarray(val.seconds)
        elif val2 is None:
            raise ValueError(f"val2 should be seconds (not {val2}) for format {cls.fmt}")
        else:
            week = np.asarray(val)
            sec = np.asarray(val2)

        # Determine GPS day
        wd = np.floor((sec + 0.5 * cls.day2seconds) / cls.day2seconds)  # 0.5 d = 43200.0 s

        # Determine remainder
        fracSec = sec + 0.5 * cls.day2seconds - wd * cls.day2seconds

        # Conversion GPS week and day to from Julian Date (JD)
        jd_day = week * Unit.week2days + wd + cls._jd19800106 - 0.5
        jd_frac = fracSec / cls.day2seconds

        return jd_day, jd_frac

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        if scale != "gps":
            raise ValueError(f"Format {cls.fmt} is only available for time scale gps")

        if np.any(jd1 + jd2 < cls._jd19800106):
            raise ValueError(f"Julian Day exceeds the GPS time start date of 6-Jan-1980 (JD {cls._jd19800106})")

        # See Time.jd_int for explanation
        _delta = jd1 - (np.floor(jd1 + jd2 - 0.5) + 0.5)
        jd_int = jd1 - _delta
        jd_frac = jd2 + _delta

        # .. Conversion from Julian Date (JD) to GPS week and day
        wwww = np.floor((jd_int - cls._jd19800106) / cls.week2days)
        wd = np.floor(jd_int - cls._jd19800106 - wwww * cls.week2days)
        gpssec = (jd_frac + wd) * cls.day2seconds

        return cls.WeekSec(wwww, gpssec, wd)


@register_format
class TimeGPSSec(TimeFormat):
    """Number of seconds since the GPS epoch 1980-01-06 00:00:00 UTC."""

    fmt = "gps_seconds"
    unit = "second"
    _jd19800106 = 2_444_244.5

    @classmethod
    def _to_jds(cls, val, val2, scale=None):
        if scale != "gps":
            raise ValueError(f"Format {cls.fmt} is only available for time scale gps")

        if val2 is not None:
            raise ValueError(f"val2 should be None (not {val2}) for format {cls.fmt}")

        days = np.asarray(val) * Unit.second2day
        days_int = np.floor(days)
        days_frac = days - days_int

        return cls._jd19800106 + days_int, days_frac

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        if scale != "gps":
            raise ValueError(f"Format {cls.fmt} is only available for time scale gps")

        if np.any(jd1 + jd2 < cls._jd19800106):
            raise ValueError(f"Julian Day exceeds the GPS time start date of 6-Jan-1980 (JD {cls._jd19800106})")

        # See Time.jd_int for explanation
        _delta = jd1 - (np.floor(jd1 + jd2 - 0.5) + 0.5)
        days_int = jd1 - _delta - cls._jd19800106
        days_frac = jd2 + _delta

        return (days_int + days_frac) * Unit.day2second


@register_format
class TimeJulianYear(TimeFormat):
    """ Time as year with decimal number. (Ex: 2000.0). Fixed year length."""

    fmt = "jyear"
    unit = ("julian_year",)
    _jd2000 = 2_451_545.0
    _j2000 = 2000

    @classmethod
    def _to_jds(cls, val, val2=None, scale=None):
        """Based on epj2jd.for from SOFA library"""
        if val2 is not None:
            raise ValueError(f"val2 should be None (not {val2}) for format {fmt}")

        int_part, fraction = np.divmod((val - cls._j2000) * Unit.julian_year2day, 1)
        return cls._jd2000 + int_part, fraction

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        """Based on epj.for from SOFA library"""
        return cls._j2000 + ((jd1 - cls._jd2000) + jd2) * Unit.day2julian_year


@register_format
class TimeDecimalYear(TimeFormat):
    """Time as year with decimal number. (Ex: 2000.0). Variable year length."""

    fmt = "decimalyear"
    unit = None  # Year length is variable so this does not make sense to apply one value

    @classmethod
    def _to_jds(cls, val, val2=None, scale=None):
        if val2 is not None:
            raise ValueError(f"val2 should be None (not {val2}) for format {fmt}")

        if scale is None:
            raise ValueError(f"scale must be defined for format {fmt}")

        try:
            return np.array([cls._dy2jd(t, scale) for t in val]).T
        except TypeError:
            return cls._dy2jd(val, scale)

    @classmethod
    @lru_cache()
    def _dy2jd(cls, decimalyear, scale):
        year_int = int(decimalyear)
        year_frac = decimalyear - year_int

        t_start_of_year = TimeArray.create(datetime(year_int, 1, 1), scale=scale, fmt="datetime")
        days = year_frac * cls._year2days(year_int, scale)
        jd = t_start_of_year.jd1 + days  # t_start.jd2 is zero for start of year

        jd1 = int(jd)
        jd2 = jd - jd1
        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        try:
            return np.array([cls._jd2dy(j1, j2, scale) for j1, j2 in zip(jd1, jd2)]).T
        except TypeError:
            return cls._jd2dy(jd1, jd2, scale)

    @classmethod
    @lru_cache()
    def _jd2dy(cls, jd1, jd2, scale):
        year = TimeDateTime._jd2dt(jd1, jd2).year
        t_start_of_year = TimeArray.create(datetime(year, 1, 1), scale=scale, fmt="datetime")
        year2days = cls._year2days(year, scale)
        days = jd1 - t_start_of_year.jd1 + jd2  # t_start.jd2 is zero for start of year
        decimalyear = year + days / year2days
        return decimalyear

    @classmethod
    @lru_cache()
    def _year2days(cls, year, scale):
        """Computes number of days in year, including leap seconds"""
        t_start = TimeArray.create(datetime(year, 1, 1), scale=scale, fmt="datetime")
        t_end = TimeArray.create(datetime(year + 1, 1, 1), scale=scale, fmt="datetime")

        if scale == "utc":
            # Account for leap seconds in UTC by differencing one TAI year
            t_start = getattr(t_start, "tai")
            t_end = getattr(t_end, "tai")
        return (t_end - t_start).days


@register_format
class TimeYyDddSssss(TimeFormat):
    """ Time as 2 digit year, doy and second of day.

    Text based format "yy:ddd:sssss"
        yy     - decimal year without century
        ddd    - zero padded decimal day of year
        sssss  - zero padded seconds since midnight

        Note   -  Does not support leap seconds

        Returns:
            Time converted to yydddssss format

    """

    fmt = "yydddsssss"
    unit = None

    @classmethod
    def _to_jds(cls, val, val2=None, scale=None):
        if val2 is not None:
            raise ValueError(f"val2 should be None (not {val2}) for format {fmt}")

        try:
            return np.array([cls._yds2jd(v) for v in val])
        except TypeError:
            cls._yds2jd(val)

    @classmethod
    @lru_cache()
    def _yds2jd(cls, val):
        return datetime.strptime(val[:7], "%y:%j:") + timedelta(sec=float(val[7:]))

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        try:
            return np.array([cls._jd2yds(j1, j2) for j1, j2 in zip(jd1, jd2)])
        except TypeError:
            return cls._jd2yds(jd1, jd2)

    @classmethod
    @lru_cache()
    def _jd2yds(cls, jd1, jd2):
        dt = TimeDateTime._jd2dt(jd1, jd2)
        delta = (dt - datetime(dt.year, dt.month, dt.day)).seconds
        return dt.strftime("%y:%j:") + str(delta).zfill(5)


@register_format
class TimeYyyyDddSssss(TimeFormat):
    """ Time as 4-digit year, doy and second of day.

    Text based format "yyyy:ddd:sssss"
        yyyy   - decimal year with century
        ddd    - zero padded decimal day of year
        sssss  - zero padded seconds since midnight

        Note   -  Does not support leap seconds

        Returns:
            Time converted to yydddssss format

    """

    fmt = "yyyydddsssss"
    unit = None

    @classmethod
    def _to_jds(cls, val, val2=None, scale=None):
        if val2 is not None:
            raise ValueError(f"val2 should be None (not {val2}) for format {fmt}")

        try:
            return np.array([cls._yds2jd(v) for v in val])
        except TypeError:
            cls._yds2jd(val)

    @classmethod
    @lru_cache()
    def _yds2jd(cls, val):
        return datetime.strptime(val[:9], "%Y:%j:") + timedelta(sec=float(val[9:]))

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        try:
            return np.array([cls._jd2yds(j1, j2) for j1, j2 in zip(jd1, jd2)])
        except TypeError:
            return cls._jd2yds(jd1, jd2)

    @classmethod
    @lru_cache()
    def _jd2yds(cls, jd1, jd2):
        dt = TimeDateTime._jd2dt(jd1, jd2)
        delta = (dt - datetime(dt.year, dt.month, dt.day)).seconds
        return dt.strftime("%Y:%j:") + str(delta).zfill(5)


# Text based time formats


class TimeStr(TimeFormat):
    """ Base class for text based time. """

    unit = None
    _dt_fmt = None

    @classmethod
    def _to_jds(cls, val, val2=None, scale=None):
        if val2 is not None:
            raise ValueError(f"val2 should be None (not {val2}) for format {fmt}")

        if isinstance(val, str):
            return TimeDateTime._dt2jd(cls._str2dt(val))
        else:
            return np.array([TimeDateTime._dt2jd(cls._str2dt(isot)) for isot in val]).T

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        try:
            return np.array([cls._dt2str(TimeDateTime._jd2dt(j1, j2)) for j1, j2 in zip(jd1, jd2)])
        except TypeError:
            return cls._dt2str(TimeDateTime._jd2dt(jd1, jd2))

    @classmethod
    @lru_cache()
    def _dt2str(cls, dt):
        return dt.strftime(cls._dt_fmt)

    @classmethod
    @lru_cache()
    def _str2dt(cls, time_str):
        # fractional parts are optional
        main_str, _, fraction = time_str.partition(".")
        if fraction and set(fraction) != "0":
            # Truncate fraction to 6 digits due to limits of datetime
            frac = float(f"0.{fraction}")
            fraction = f"{frac:8.6f}"[2:]
            time_str = f"{main_str}.{fraction}"
            return datetime.strptime(time_str, cls._dt_fmt)
        else:
            fmt_str, _, _ = cls._dt_fmt.partition(".")
            return datetime.strptime(main_str, fmt_str)


@register_format
class TimeIsot(TimeStr):
    """ISO 8601 compliant date-time format “YYYY-MM-DDTHH:MM:SS.sss…” """

    fmt = "isot"
    _dt_fmt = "%Y-%m-%dT%H:%M:%S.%f"


@register_format
class TimeIso(TimeStr):
    """ISO 8601 compliant date-time format “YYYY-MM-DD HH:MM:SS.sss…” without the T"""

    fmt = "iso"
    _dt_fmt = "%Y-%m-%d %H:%M:%S.%f"


@register_format
class TimeYearDoy(TimeStr):

    fmt = "yday"
    _dt_fmt = "%Y:%j:%H:%M:%S.%f"


@register_format
class TimeDate(TimeStr):

    fmt = "date"
    _dt_fmt = "%Y-%m-%d"


# Time Delta Formats


@register_format
class TimeDeltaJD(TimeDeltaFormat):
    """Time delta as Julian days"""

    fmt = "jd"
    unit = ("day",)

    @classmethod
    def _to_jds(cls, val, val2, scale=None):
        if val2 is None:
            try:
                val2 = np.zeros(val.shape)
            except AttributeError:
                val2 = 0

        _delta = val - (np.floor(val + val2))
        jd1 = val - _delta
        jd2 = val2 + _delta
        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        return jd1 + jd2


@register_format
class TimeDeltaSec(TimeDeltaFormat):
    """Time delta in seconds"""

    fmt = "seconds"
    unit = ("second",)

    @classmethod
    def _to_jds(cls, val, val2, scale=None):
        if val2 is None:
            try:
                val2 = np.zeros(val.shape)
            except AttributeError:
                val2 = 0

        val *= Unit.second2day
        val2 *= Unit.second2day
        _delta = val - (np.floor(val + val2))
        jd1 = val - _delta
        jd2 = val2 + _delta
        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        return (jd1 + jd2) * Unit.day2second


@register_format
class TimeDeltaDay(TimeDeltaFormat):
    """Time delta in days"""

    fmt = "days"
    unit = ("day",)

    @classmethod
    def _to_jds(cls, val, val2, scale=None):
        if val2 is None:
            try:
                val2 = np.zeros(val.shape)
            except AttributeError:
                val2 = 0

        _delta = val - (np.floor(val + val2))
        jd1 = val - _delta
        jd2 = val2 + _delta
        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        return jd1 + jd2


@register_format
class TimeDeltaDateTime(TimeDeltaFormat):
    """Time delta as datetime's timedelta"""

    fmt = "timedelta"
    unit = None

    @classmethod
    def _to_jds(cls, val, val2, scale=None):
        if val2 is None:
            try:
                val2 = [timedelta(seconds=0)] * len(val)
            except TypeError:
                val2 = timedelta(seconds=0)

        try:
            days = (val + val2).total_seconds() * Unit.second2day
        except AttributeError:
            seconds = [v1.total_seconds() + v2.total_seconds() for v1, v2 in zip(val, val2)]
            days = np.array(seconds) * Unit.second2day

        jd1 = np.floor(days)
        jd2 = days - jd1
        return jd1, jd2

    @classmethod
    def _from_jds(cls, jd1, jd2, scale=None):
        try:
            return timedelta(days=jd1 + jd2)
        except TypeError:
            return np.array([timedelta(days=j1 + j2) for j1, j2 in zip(jd1, jd2)])


#######################################################################################################################
# Execute on import
#######################################################################################################################
_TAIUTC = read_tai_utc()
