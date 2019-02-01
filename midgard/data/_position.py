"""Array with positions
"""

# Standard library imports
from typing import Any, Callable, Dict, List, Tuple

# Third party imports
import numpy as np

# Midgard imports
from midgard.data._position_delta import PositionDeltaArray
from midgard.dev import exceptions
from midgard.math.constant import constant
from midgard.math import rotation
from midgard.math import transformation

_ATTRIBUTES: List[str] = list()  # Populated by register_attribute()
_FIELDS: List[str] = list()  # Populated by register_field()
_UNITS: Dict[str, str] = dict()  # Populated by register_field()
_SYSTEMS: Dict[str, "PositionArray"] = dict()  # Populated by register_system()
_CONVERSIONS: Dict[Tuple[str, str], Callable] = dict()  # Populated by register_system()
_CONVERSION_HOPS: Dict[Tuple[str, str], List[str]] = dict()  # Cache for to_system()


def register_attribute(name: str) -> None:
    """Function used to register new attributes on position arrays

    The registered attributes will be available as attributes on PositionArray
    and its subclasses. In addition, each attribute can be given as a parameter
    when creating a PositionArray.

    The reason for using this register-function instead of a regular attribute
    is to allow additional attributes to be added on all position systems.

    Args:
        name:  Name of attribute

    """
    _ATTRIBUTES.append(name)


def register_field(units: List[str]) -> Callable:
    """Decorator used to register fields and their units

    """

    def wrapper(func: Callable) -> Callable:
        field = func.__name__
        _FIELDS.append(field)
        _UNITS[field] = units
        return func

    return wrapper


def register_system(
    convert_to: Dict[str, Callable] = None, convert_from: Dict[str, Callable] = None
) -> Callable[[Callable], Callable]:
    """Decorator used to register new position systems

    The system name is read from the .system attribute of the Position class.

    Args:
        convert_to:    Functions used to convert to other systems.
        convert_from:  Functions used to convert from other systems.

    Returns:
        Decorator registering system.
    """

    def wrapper(cls: Callable) -> Callable:
        name = cls.system
        _SYSTEMS[name] = cls

        if convert_to:
            for to_system, converter in convert_to.items():
                _CONVERSIONS[(name, to_system)] = converter
        if convert_from:
            for from_system, converter in convert_from.items():
                _CONVERSIONS[(to_system, name)] = converter
        return cls

    return wrapper


def _find_conversion_hops(hop: Tuple[str, str]) -> List[Tuple[str, str]]:
    """Calculate the hops needed to convert between systems using breadth first search"""
    start_sys, target_sys = hop
    queue = [(start_sys, [])]
    visited = set()

    while queue:
        from_sys, hops = queue.pop(0)
        for to_sys in [t for f, t in _CONVERSIONS if f == from_sys]:
            one_hop = (from_sys, to_sys)
            if to_sys == target_sys:
                return hops + [one_hop]
            if one_hop not in visited:
                visited.add(one_hop)
                queue.append((to_sys, hops + [one_hop]))

    raise exceptions.UnknownConversionError(f"Can't convert PositionArray from {start_sys!r} to {target_sys!r}")


class PositionArray(np.ndarray):
    """Base class for Position arrays

    This PositionArray should not be instatiated. Instead instantiate one of
    the system specific subclasses, typically using the Position factory
    function.
    """

    system = None
    column_names = None
    _units = None
    _systems = _SYSTEMS
    _attributes = _ATTRIBUTES

    def __new__(cls, val, **pos_args):
        """Create a new Position"""
        if cls.system is None or cls.column_names is None:
            raise ValueError(
                f"{cls.__name__} cannot be instantiated. Use Position(val=..., system={cls.system!r}) instead"
            )

        obj = np.asarray(val, dtype=float, order="C").view(cls)
        obj.system = cls.system
        for attr in _ATTRIBUTES:
            setattr(obj, attr, pos_args.get(attr))
        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new Position is created"""
        if obj is None:
            return

        # Validate shape
        num_columns = len(self.column_names)
        if self.shape[-1] != num_columns:
            column_names = ", ".join(self.column_names)
            raise ValueError(f"{type(self).__name__!r} requires {num_columns} columns: {column_names}")

        if self.ndim == 1:
            self.resize(1, num_columns)
        elif self.ndim != 2:
            raise ValueError(f"{type(self).__name__!r} must be a 1- or 2-dimensional array with {num_columns} columns")

        # Copy attributes from the original object
        self.system = getattr(obj, "system", None)
        for attr in _ATTRIBUTES:
            setattr(self, attr, getattr(obj, attr, None))

    @classmethod
    def _fieldnames(cls):
        return _ATTRIBUTES + _FIELDS + [f"{s}.{c}" for s, sc in cls._systems.items() for c in sc.column_names]

    @staticmethod
    def create(val: np.ndarray, system: str, **pos_args: Any) -> "PositionArray":
        """Factory for creating PositionArrays for different systems

        See each position class for exact optional parameters.

        Args:
            val:       Array of position values.
            system:    Name of position system.
            pos_args:  Additional arguments used to create the PositionArray.

        Returns:
            Array with positions in the given system.
        """
        if system not in _SYSTEMS:
            systems = ", ".join(_SYSTEMS)
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        return _SYSTEMS[system](val, **pos_args)

    @classmethod
    def from_position(cls, val: np.ndarray, other: "PositionArray") -> "PositionArray":
        """Create a new position with given values and same attributes as other position

        Factory method for creating a new position array with the given
        values. Attributes will be copied from the other position.
        """
        attrs = {a: getattr(other, a, None) for a in _ATTRIBUTES}
        return cls(val, **attrs)

    @property
    def val(self):
        """Position as a plain numpy array"""
        return np.asarray(self)

    @property
    def mat(self):
        """Position as an array of matrices

        Adds an extra dimension, so that matrix multiplication can be performed
        effectively. By default .mat returns an array of column vectors. To
        effectively access row vectors instead, operate on a transposed delta:

        Example:

        >>> pos    # shape (2, 3)
        LlhPosition([[0., 0., 100.],
                     [1., 1., 0.]])

        >>> pos.mat    # Column vectors, shape (2, 3, 1)
        array([[[0.],
                [0.],
                [100.]],

               [[1.],
                [1.],
                [0.]]])

        >>> pos.T.mat    # Row vectors, shape (2, 1, 3)
            array([[[0., 0., 100.]],

                   [[1., 1., 0.]]])
        """
        is_transposed = self.flags.f_contiguous  # Because we forced order == "C" on creation
        if is_transposed:
            return np.asarray(self)[:, None, :].T
        else:
            return np.asarray(self)[:, :, None]

    def to_system(self, system: str) -> "PositionArray":
        """Convert position to a different system

        Returns a new PositionArray with the same position in the new system.

        Args:
            system:  Name of new system.

        Returns:
            PositionArray representing the same positions in the new system.
        """
        # Don't convert if not necessary
        if system == self.system:
            return self

        # Raise error for unknown systems
        if system not in self._systems:
            systems = ", ".join(self._systems)
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        # Convert to new system
        hop = (self.system, system)
        if hop in _CONVERSIONS:
            return self._systems[system].from_position(_CONVERSIONS[hop](self), self)

        if hop not in _CONVERSION_HOPS:
            _CONVERSION_HOPS[hop] = _find_conversion_hops(hop)
            print(_CONVERSION_HOPS)

        val = self
        for one_hop in _CONVERSION_HOPS[hop]:
            print(one_hop)
            val = self._systems[one_hop[-1]].from_position(_CONVERSIONS[one_hop](val), val)
        return val

    @classmethod
    def unit(cls, field: str = "") -> Tuple[str, ...]:
        """Unit of field"""
        mainfield, _, subfield = field.partition(".")

        # Units of position array
        if not field:
            return cls._units

        # Unit of columns in position array
        elif field in cls.column_names:
            return (cls._units[cls.column_names.index(field)],)

        # Units of properties
        elif field in _UNITS:
            return _UNITS[field]

        # Units of systems
        elif mainfield in cls._systems:
            return cls._systems[mainfield].unit(subfield)

        else:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    def vector_to(self, other: "PositionArray") -> np.ndarray:
        """Vector to other positions in current system

        Args:
            other:  Other position array.

        Returns:
            Array of vectors to other position array.
        """
        return other.to_system(self.system).val - self.val

    @property
    @register_field(units=("meter", "meter", "meter"))
    def vector(self):
        """Vector to registered other position"""
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.vector_to(self.other)

    def distance_to(self, other):
        """Distance to other positions in current system

        Args:
            other:  Other position array

        Returns:
            Array of distances to other position array.
        """
        return np.linalg.norm(self.vector_to(other), axis=1)

    @property
    @register_field(units=("meter",))
    def distance(self):
        """Distance to registered other position"""
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.distance_to(self.other)

    def direction_to(self, other):
        try:
            return self.vector_to(other) / self.distance_to(other)[:, None]
        except AttributeError:
            return other.direction_from(self)

    @property
    @register_field(units=("unitless", "unitless", "unitless"))
    def direction(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.direction_to(self.other)

    def aberrated_direction_to(self, other):
        return other._aberrated_direction_from(self)

    @property
    @register_field(units=("unitless", "unitless", "unitless"))
    def aberrated_direction(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.aberrated_direction_to(self.other)

    def _aberrated_direction_from(self, other):
        """Calculate aberrated direction vector from earth based position"""
        return other.direction_to(self - other.aberration_to(self))  # Todo: Check + or -

    def aberration_to(self, other):
        flight_time = self.distance_to(other) / constant.c
        rotation_angle = flight_time * constant.omega

        return (rotation.R3(rotation_angle) @ other.mat)[:, :, 0] - other.val

    @property
    @register_field(units=("meter", "meter", "meter"))
    def aberration(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.aberration_to(self.other)

    def azimuth_to(self, other):
        lat, lon, _ = self.llh.val.T
        enu2trs = rotation.enu2trs(lat, lon)
        enu_east = enu2trs[:, :, 0:1]
        enu_north = enu2trs[:, :, 1:2]

        east_proj = (self.trs.direction_to(other)[:, None, :] @ enu_east)[:, 0, 0]
        north_proj = (self.trs.direction_to(other)[:, None, :] @ enu_north)[:, 0, 0]

        return np.arctan2(east_proj, north_proj)

    @property
    @register_field(units=("radians",))
    def azimuth(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.azimuth_to(self.other)

    def elevation_to(self, other):
        lat, lon, _ = self.llh.val.T
        enu2trs = rotation.enu2trs(lat, lon)
        enu_up = enu2trs[:, :, 2:3]

        up_proj = (self.trs.direction_to(other)[:, None, :] @ enu_up)[:, 0, 0]

        return np.arcsin(up_proj)

    # TODO: Aberrated azimuth, zenith_distance

    @property
    @register_field(units=("radians",))
    def elevation(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.elevation_to(self.other)

    def aberrated_elevation_to(self, other):
        lat, lon, _ = self.llh.val.T
        enu2trs = rotation.enu2trs(lat, lon)
        enu_up = enu2trs[:, :, 2:3]

        up_proj = (self.trs.aberrated_direction_to(other)[:, None, :] @ enu_up)[:, 0, 0]

        return np.arcsin(up_proj)

    @property
    @register_field(units=("radians",))
    def aberrated_elevation(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.aberrated_elevation_to(self.other)

    def zenith_distance_to(self, other):
        return np.pi / 2 - self.elevation_to(other)

    @property
    @register_field(units=("radians",))
    def zenith_distance(self):
        return np.pi / 2 - self.elevation

    def __getattr__(self, key):
        """Get attributes with dot notation

        Add systems and column names to attributes on Position arrays.

        Args:
            key:  Name of attribute.

        Returns:
            Value of attribute.
        """
        # Convert to a different system
        if key in self._systems:
            return self.to_system(key)

        # Return one column as a regular numpy array
        elif key in self.column_names:
            idx = self.column_names.index(key)
            return np.asarray(self)[:, idx]

        # Raise error for unknown attributes
        else:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __dir__(self):
        """List all fields and attributes on the Position array"""
        return super().__dir__() + list(self._systems) + list(self.column_names)

    def __add__(self, other):
        """self + other"""
        if isinstance(other, PositionDeltaArray):
            try:
                return self.from_position(val=np.asarray(self) + np.asarray(other.to_system(self.system)), other=self)
            except exceptions.UnknownSystemError:
                return NotImplemented

        return NotImplemented

    def __radd__(self, other):
        """other + self"""
        if isinstance(other, PositionDeltaArray):
            try:
                return self.from_position(val=np.asarray(self) + np.asarray(other.to_system(self.system)), other=self)
            except exceptions.UnknownSystemError:
                return NotImplemented

        return NotImplemented

    def __iadd__(self, other):
        """self += other"""
        return self.__add__(other)

    def __sub__(self, other):
        """self - other"""
        # Create a position delta by subtracting two positions
        if isinstance(other, PositionArray):
            try:
                return PositionDeltaArray.create(
                    val=np.asarray(self.to_system(other.system)) - np.asarray(other),
                    system=other.system,
                    ref_pos=other,
                )
            except exceptions.UnknownSystemError:
                return NotImplemented

        # Subtract a position delta from the position
        elif isinstance(other, PositionDeltaArray):
            try:
                return self.from_position(val=np.asarray(self) - np.asarray(other.to_system(self.system)), other=self)
            except exceptions.UnknownSystemError:
                return NotImplemented

        return NotImplemented

    def __rsub__(self, other):
        """other - self"""

        # Create a position delta by subtracting two positions
        if isinstance(other, PositionArray):
            try:
                return PositionDeltaArray.create(
                    val=np.asarray(other) - np.asarray(self.to_system(other.system)), system=other.system, ref_pos=self
                )
            except exceptions.UnknownSystemError:
                return NotImplemented

        return NotImplemented

    def __isub__(self, other):
        """self -= other"""
        return self

    def __matmul__(self, other):
        """self @ other"""
        return NotImplemented

    def __rmatmul__(self, other):
        """other @ self"""
        return NotImplemented

    def __imatmul__(self, other):
        """self @= other"""
        return NotImplemented


#
# Attributes
#
register_attribute("other")


#
# Position systems
#
@register_system(convert_to=dict(llh=transformation.trs2llh))
class TrsPosition(PositionArray):

    system = "trs"
    column_names = ("x", "y", "z")
    _units = ("meter", "meter", "meter")


@register_system(convert_to=dict(trs=transformation.llh2trs))
class LlhPosition(PositionArray):

    system = "llh"
    column_names = ("lat", "lon", "height")
    _units = ("radians", "radians", "meter")
