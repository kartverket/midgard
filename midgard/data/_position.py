""" Module for dealing with positions, velocities and position corrections in different coordinate systems
"""
# Standard library imports
from typing import Any, Callable, Dict, List, Tuple
import copy

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import exceptions
from midgard.math.constant import constant
from midgard.math import rotation
from midgard.math import ellipsoid

_ATTRIBUTES: Dict[str, Dict[str, Callable]] = dict()  # Populated by register_attribute()
_FIELDS: Dict[str, List[str]] = dict()  # Populated by register_field()
_UNITS: Dict[str, Dict[str, str]] = dict()  # Populated by register_field()
_SYSTEMS: Dict[str, Dict[str, Callable]] = dict()  # Populated by register_system()
_CONVERSIONS: Dict[str, Dict[Tuple[str, str], Callable]] = dict()  # Populated by register_system()
_CONVERSION_HOPS: Dict[str, Dict[Tuple[str, str], List[str]]] = dict()  # Cache for to_system()


def register_attribute(cls: Callable, name: str, attr_cls: Callable) -> None:
    """Function used to register new attributes on position arrays

    The registered attributes will be available as attributes on PositionArray
    and its subclasses. In addition, each attribute can be given as a parameter
    when creating a PositionArray.

    The reason for using this register-function instead of a regular attribute
    is to allow additional attributes to be added on all position systems.

    Args:
        cls:      Name of class to register the attribute for
        name:     Name of attribute
        attr_cls: Class of attribute

    """
    _ATTRIBUTES.setdefault(cls.__name__, dict()).setdefault(name, attr_cls)


def register_field(units: List[str]) -> Callable:
    """Decorator used to register fields and their units

    """

    def wrapper(func: Callable) -> Callable:
        field = func.__name__
        func_class = func.__qualname__.split(".")[0]
        _FIELDS.setdefault(func_class, list()).append(field)
        _UNITS.setdefault(func_class, dict())[field] = units
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
        _SYSTEMS.setdefault(cls.cls_name, dict())[name] = cls

        if convert_to:
            for to_system, converter in convert_to.items():
                _CONVERSIONS.setdefault(cls.cls_name, dict())[(name, to_system)] = converter
        if convert_from:
            for from_system, converter in convert_from.items():
                _CONVERSIONS.setdefault(cls.cls_name, dict())[(from_system, name)] = converter
        return cls

    return wrapper


def _find_conversion_hops(cls: str, hop: Tuple[str, str]) -> List[Tuple[str, str]]:
    """Calculate the hops needed to convert between systems using breadth first search"""
    start_sys, target_sys = hop
    queue = [(start_sys, [])]
    visited = set()

    while queue:
        from_sys, hops = queue.pop(0)
        for to_sys in [t for f, t in _CONVERSIONS[cls] if f == from_sys]:
            one_hop = (from_sys, to_sys)
            if to_sys == target_sys:
                return hops + [one_hop]
            if one_hop not in visited:
                visited.add(one_hop)
                queue.append((to_sys, hops + [one_hop]))

    raise exceptions.UnknownConversionError(f"Can't convert PositionArray from {start_sys!r} to {target_sys!r}")


class PosBase(np.ndarray):
    """Base class for the various position and velocity arrays"""

    system = None
    column_names = None
    _units = None

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
            return self.val[:, None, :].T
        else:
            return self.val[:, :, None]

    def to_system(self, system: str) -> "PosDeltaBase":
        """Convert to a different system

        Args:
            system:  Name of new system.

        Returns:
            PosDeltaBase representing the same positions or position deltas in the new system.
        """
        # Don't convert if not necessary
        if system == self.system:
            return self

        # Raise error for unknown systems
        if system not in _SYSTEMS[self.cls_name]:
            systems = ", ".join(_SYSTEMS[self.cls_name])
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        # Convert to new system
        hop = (self.system, system)
        if hop in _CONVERSIONS[self.cls_name]:
            return _SYSTEMS[self.cls_name][system].convert_to(self, _CONVERSIONS[self.cls_name][hop])

        if hop not in _CONVERSION_HOPS.setdefault(self.cls_name, {}):
            _CONVERSION_HOPS[self.cls_name][hop] = _find_conversion_hops(self.cls_name, hop)

        val = self
        for one_hop in _CONVERSION_HOPS[self.cls_name][hop]:
            val = _SYSTEMS[self.cls_name][one_hop[-1]].convert_to(val, _CONVERSIONS[self.cls_name][one_hop])
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
        elif field in _UNITS.get(cls.cls_name, {}):
            return _UNITS[cls.cls_name][field]

        # Units of systems
        elif mainfield in _SYSTEMS[cls.cls_name]:
            return _SYSTEMS[cls.cls_name][mainfield].unit(subfield)

        else:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    @classmethod
    def _fieldnames(cls):
        return (
            list(cls._attributes().keys())
            + _FIELDS.get(cls.cls_name, [])
            + [f"{s}.{c}" for s, sc in _SYSTEMS[cls.cls_name].items() for c in sc.column_names]
        )

    @classmethod
    def _attributes(cls):
        return _ATTRIBUTES.get(cls.cls_name, {})

    def __getattr__(self, key):
        """Get attributes with dot notation

        Add systems and column names to attributes on Position and PostionDelta arrays.

        Args:
            key:  Name of attribute.

        Returns:
            Value of attribute.
        """
        # Convert to a different system
        if key in _SYSTEMS[self.cls_name]:
            return self.to_system(key)

        # Return one column as a regular numpy array
        elif key in self.column_names:
            idx = self.column_names.index(key)
            return self.val[:, idx]

        # Raise error for unknown attributes
        else:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __dir__(self):
        """List all fields and attributes on the PosDeltaBase array"""
        return super().__dir__() + list(_SYSTEMS[self.cls_name]) + list(self.column_names)

    def __iadd__(self, other):
        """self += other"""
        return self.__add__(other)

    def __isub__(self, other):
        """self -= other"""
        return self.__sub__(other)

    # For matrix-multiplication use trs.mat @ numbers[slice]

    def __matmul__(self, _):
        """self @ _"""
        return NotImplemented

    def __rmatmul__(self, _):
        """_ @ self"""
        return NotImplemented

    def __imatmul__(self, _):
        """self @= _"""
        return NotImplemented

    # For _ matematical operations use pos.val

    def __mul__(self, _):
        """self * _"""
        return NotImplemented

    def __rmul__(self, _):
        """_ * self"""
        return NotImplemented

    def __imul__(self, _):
        """self *= _"""
        return NotImplemented

    def __truediv__(self, _):
        """self / _"""
        return NotImplemented

    def __rtruediv__(self, _):
        """_ / self"""
        return NotImplemented

    def __itruediv__(self, _):
        """self /= _"""
        return NotImplemented

    def __floordiv__(self, _):
        """self // _"""
        return NotImplemented

    def __rfloordiv__(self, _):
        """ _ // self"""
        return NotImplemented

    def __ifloordiv__(self, _):
        """self //= _"""
        return NotImplemented

    def __pow__(self, _):
        """ self ** _"""
        return NotImplemented

    def __rpow(self, _):
        """ _ ** self """
        return NotImplemented

    def __ipow__(self, _):
        """ self **= _"""
        return NotImplemented


class PositionArray(PosBase):
    """Base class for Position arrays

    This PositionArray should not be instantiated. Instead instantiate one of
    the system specific subclasses, typically using the Position factory
    function.
    """

    cls_name = "PositionArray"

    def __new__(cls, val, ellipsoid=ellipsoid.GRS80, **pos_args):
        """Create a new Position"""
        if cls.system is None or cls.column_names is None:
            raise ValueError(
                f"{cls.cls_name} cannot be instantiated. Use {cls.cls_name.strip('Array')}(val=..., system={cls.system!r}) instead"
            )

        obj = np.asarray(val, dtype=float, order="C").view(cls)
        obj.system = cls.system
        obj.ellipsoid = ellipsoid
        for attr in cls._attributes().keys():
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
        self.ellipsoid = getattr(obj, "ellipsoid", ellipsoid.GRS80)
        for attr in self._attributes().keys():
            setattr(self, attr, getattr(obj, attr, None))

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
        if system not in _SYSTEMS["PositionArray"]:
            systems = ", ".join(_SYSTEMS["PositionArray"])
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        return _SYSTEMS["PositionArray"][system](val, **pos_args)

    @classmethod
    def from_position(cls, val: np.ndarray, other: "PositionArray") -> "PositionArray":
        """Create a new position with given values and same attributes as other position

        Factory method for creating a new position array with the given
        values. Attributes will be copied from the other position.
        """
        attrs = {a: getattr(other, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS[cls.cls_name][other.system](val, **attrs)

    @classmethod
    def convert_to(cls, pos: "PositionArray", converter: Callable) -> "PositionArray":
        """Convert the position to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position 
        """
        attrs = {a: getattr(pos, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS[cls.cls_name][cls.system](converter(pos), **attrs)

    @property
    def pos(self):
        """Allows base classes to implement this attribute"""
        return self

    @property
    @register_field(units=("unitless", "unitless", "unitless"))
    def enu2trs(self):
        lat, lon, _ = self.pos.llh.val.T
        return rotation.enu2trs(lat, lon)

    @property
    @register_field(units=("unitless", "unitless", "unitless"))
    def trs2enu(self):
        lat, lon, _ = self.pos.llh.val.T
        return rotation.enu2trs(lat, lon)

    @property
    @register_field(units=("unitless", "unitless", "unitless"))
    def enu_east(self):
        """ Unit vector for in the east direction"""
        return self.enu2trs[:, :, 0:1]

    @property
    @register_field(units=("unitless", "unitless", "unitless"))
    def enu_north(self):
        """ Unit vector for in the north direction"""
        return self.enu2trs[:, :, 1:2]

    @property
    @register_field(units=("unitless", "unitless", "unitless"))
    def enu_up(self):
        """ Unit vector for in the up direction"""
        return self.enu2trs[:, :, 2:3]

    def vector_to(self, other: "PositionArray") -> np.ndarray:
        """Vector to other positions in current system

        Args:
            other:  Other position array.

        Returns:
            Array of vectors to other position array.
        """
        return other.pos.to_system(self.system).val - self.pos.val

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
        return other.aberrated_direction_from(self)

    @property
    @register_field(units=("unitless", "unitless", "unitless"))
    def aberrated_direction(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.aberrated_direction_to(self.other)

    def aberrated_direction_from(self, other):
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
        east_proj = (self.trs.direction_to(other)[:, None, :] @ self.enu_east)[:, 0, 0]
        north_proj = (self.trs.direction_to(other)[:, None, :] @ self.enu_north)[:, 0, 0]

        return np.arctan2(east_proj, north_proj)

    @property
    @register_field(units=("radians",))
    def azimuth(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.azimuth_to(self.other)

    def aberrated_azimuth_to(self, other):
        east_proj = (self.trs.aberrated_direction_to(other)[:, None, :] @ self.enu_east)[:, 0, 0]
        north_proj = (self.trs.aberrated_direction_to(other)[:, None, :] @ self.enu_north)[:, 0, 0]

        return np.arctan2(east_proj, north_proj)

    @property
    @register_field(units=("radians",))
    def aberrated_azimuth(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.aberrated_azimuth_to(self.other)

    def elevation_to(self, other):
        up_proj = (self.trs.direction_to(other)[:, None, :] @ self.enu_up)[:, 0, 0]

        return np.arcsin(up_proj)

    @property
    @register_field(units=("radians",))
    def elevation(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.elevation_to(self.other)

    def aberrated_elevation_to(self, other):
        up_proj = (self.trs.aberrated_direction_to(other)[:, None, :] @ self.enu_up)[:, 0, 0]

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

    def aberrated_zenith_distance_to(self, other):
        return np.pi / 2 - self.aberrated_elevation_to(other)

    @property
    @register_field(units=("radians",))
    def aberrated_zenith_distance(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")
        return self.aberrated_zenith_distance_to(self.other)

    def __add__(self, other):
        """self + other"""
        if isinstance(other, PositionDeltaArray):
            if self.system != other.system:
                return NotImplemented
            return self.from_position(val=self.val + other.val, other=self)

        elif isinstance(other, PositionArray):
            # pos1 + pos2 does not make sense
            return NotImplemented

        return NotImplemented

    def __radd__(self, other):
        """other + self"""
        if isinstance(other, PositionDeltaArray):
            if self.system != other.system:
                return NotImplemented

        elif isinstance(other, PositionArray):
            # pos1 + pos2 does not make sense
            return NotImplemented

        return NotImplemented

    def __sub__(self, other):
        """self - other"""

        if isinstance(other, PositionArray):
            if self.system != other.system:
                return NotImplemented
            try:
                return PositionDeltaArray.from_position(val=self.val - other.val, other=self)
            except KeyError:
                return NotImplemented

        elif isinstance(other, PositionDeltaArray):
            if self.system != other.system:
                return NotImplemented
            return self.from_position(val=self.val - other.val, other=self)

        return NotImplemented

    def __rsub__(self, other):
        """other - self"""
        if isinstance(other, PositionArray):
            if self.system != other.system:
                return NotImplemented

        elif isinstance(other, PositionDeltaArray):
            if self.system != other.system:
                return NotImplemented

        return NotImplemented

    def __deepcopy__(self, memo):
        """Deep copy a PositionArray

        Makes sure references to other objects are updated correctly
        """
        attrs = {a: copy.deepcopy(getattr(self, a, None), memo) for a in self._attributes().keys()}
        new_pos = PositionArray.create(val=np.asarray(self).copy(), system=self.system, **attrs)
        memo[id(self)] = new_pos
        return new_pos

    @classmethod
    def _read(cls, h5_group, memo):
        system = h5_group.attrs["system"]
        ellipsoid_ = ellipsoid.get(h5_group.attrs["ellipsoid"])

        pos_args = {}
        for a, attr_cls in PositionArray._attributes().items():
            if a in h5_group.attrs:
                # attribute is a reference to the data of another field
                pos_args.update({a: memo[h5_group.attrs[a]]})
            elif a in h5_group and isinstance(h5_group[a], type(h5_group)):
                # attribute is a part of this group and is not in a separate field
                arg = attr_cls._read(h5_group[a], memo)
                pos_args.update({a: arg})
                memo[f"{h5_group.attrs['fieldname']}.{a}"] = arg

        val = h5_group[h5_group.attrs["fieldname"]][...]

        return cls.create(val, system=system, ellipsoid=ellipsoid_, **pos_args)

    def _write(self, h5_group, memo):
        h5_group.attrs["system"] = self.system
        h5_group.attrs["ellipsoid"] = self.ellipsoid.name
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        for a in PositionArray._attributes().keys():
            attr = getattr(self, a, None)
            if attr is None:
                continue

            if id(attr) in memo:
                # attribute is a reference to the data of another field
                h5_group.attrs[a] = memo[id(attr)]
            else:
                # attribute is stored as part of this in PositionArray
                h5_sub_group = h5_group.create_group(a)
                h5_sub_group.attrs["fieldname"] = a
                memo[id(attr)] = f"{h5_group.attrs['fieldname']}.{a}"
                attr._write(h5_sub_group, memo)  # Potential recursive call


class PositionDeltaArray(PosBase):
    """Base class for position deltas

    This PositionDeltaArray should not be instantiated. Instead instantiate one
    of the system specific subclasses, typically using the PositionDelta
    factory function.
    """

    system = None
    column_names = None
    cls_name = "PositionDeltaArray"

    def __new__(cls, val, ref_pos, **delta_args):
        """Create a new Positiondelta"""
        if cls.system is None or cls.column_names is None:
            raise ValueError(
                f"{cls.cls_name} cannot be instantiated. Use {cls.cls_name.strip('Array')}(val=..., system={cls.system!r}) instead"
            )

        obj = np.asarray(val, dtype=float, order="C").view(cls)
        obj.system = cls.system
        obj.ref_pos = ref_pos
        for attr in cls._attributes().keys():
            setattr(obj, attr, delta_args.get(attr))

        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new PositionDelta is created"""
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
        self.ref_pos = getattr(obj, "ref_pos", None)

    @staticmethod
    def create(val: np.ndarray, system: str, ref_pos, **delta_args: Any) -> "PositionDeltaArray":
        """Factory for creating PositionDeltaArrays for different systems

        See each position delta class for exact optional parameters.

        Args:
            val:         Array of position deltas.
            system:      Name of position system.
            ref_pos:     Array of reference positions.
            delta_args:  Additional arguments used to create the PositionDeltaArray.

        Returns:
            Array with positions in the given system.
        """
        if system not in _SYSTEMS["PositionDeltaArray"]:
            systems = ", ".join(_SYSTEMS["PositionDeltaArray"])
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        return _SYSTEMS["PositionDeltaArray"][system](val, ref_pos, **delta_args)

    @classmethod
    def from_position(cls, val: np.ndarray, other: "PositionArray") -> "PositionDeltaArray":
        """Create a new position delta with given values and same attributes as other position

        Factory method for creating a new position array with the given
        values. Attributes will be copied from the other position.
        """
        attrs = {a: getattr(other, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS[cls.cls_name][other.system](val, ref_pos=other, **attrs)

    @classmethod
    def from_position_delta(cls, val: np.ndarray, other: "PositionDeltaArray") -> "PositionDeltaArray":
        """Create a new position with given values and same attributes as other position

        Factory method for creating a new position array with the given
        values. Attributes will be copied from the other position.
        """
        attrs = {a: getattr(other, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS[cls.cls_name][other.system](val, ref_pos=other.ref_pos, **attrs)

    @classmethod
    def convert_to(cls, pos_delta: "PositionDeltaArray", converter: Callable) -> "PositionDeltaArray":
        """Convert the position delta to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position delta 
        """
        attrs = {a: getattr(pos_delta, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS[cls.cls_name][cls.system](converter(pos_delta), ref_pos=pos_delta.ref_pos, **attrs)

    @property
    def pos(self):
        """Allows base classes to implement this attribute"""
        return self

    def __add__(self, other):
        """self + other"""
        if isinstance(other, PositionDeltaArray):
            if self.system != other.system:
                return NotImplemented
            return other.from_position_delta(val=self.val + other.val, other=self)

        elif isinstance(other, PositionArray):
            if self.system != other.system:
                return NotImplemented
            return other.from_position(val=self.val + other.val, other=other)

        return NotImplemented

    def __radd__(self, other):
        """other + self"""
        if isinstance(other, PositionArray):
            if self.system != other.system:
                return NotImplemented

        elif isinstance(other, PositionDeltaArray):
            if self.system != other.system:
                return NotImplemented

        return NotImplemented

    def __sub__(self, other):
        """self - other"""
        if isinstance(other, PositionDeltaArray):
            if self.system != other.system:
                return NotImplemented
            return other.from_position_delta(val=self.val - other.val, other=self)

        elif isinstance(other, PositionArray):
            if self.system != other.system:
                return NotImplemented
            return other.from_position(val=self.val - other.val, other=other)

        return NotImplemented

    def __rsub__(self, other):
        """other - self"""
        if isinstance(other, PositionArray):
            if self.system != other.system:
                return NotImplemented
        elif isinstance(other, PositionDeltaArray):
            if self.system != other.system:
                return NotImplemented

        return NotImplemented

    def __deepcopy__(self, memo):
        """Deep copy a PositionDeltaArray

        Makes sure references to other objects are updated correctly
        """
        attrs = {a: copy.deepcopy(getattr(self, a, None), memo) for a in list(self._attributes().keys()) + ["ref_pos"]}
        new_pos = PositionDeltaArray.create(val=np.asarray(self).copy(), system=self.system, **attrs)
        memo[id(self)] = new_pos
        return new_pos

    @classmethod
    def _read(cls, h5_group, memo):
        system = h5_group.attrs["system"]

        cls_args = {"ref_pos": PositionArray}
        delta_args = {}
        for a, attr_cls in {**PositionDeltaArray._attributes(), **cls_args}.items():
            if a in h5_group.attrs:
                # attribute is a reference to the data of another field
                delta_args.update({a: memo[h5_group.attrs[a]]})
            elif a in h5_group and isinstance(h5_group[a], type(h5_group)):
                # attribute is a part of this group and is not in a separate field
                arg = attr_cls._read(h5_group[a], memo)
                delta_args.update({a: arg})
                memo[f"{h5_group.attrs['fieldname']}.{a}"] = arg

        val = h5_group[h5_group.attrs["fieldname"]][...]

        return cls.create(val, system=system, **delta_args)

    def _write(self, h5_group, memo):
        h5_group.attrs["system"] = self.system
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        cls_args = {"ref_pos": PositionArray}
        for a in {**PositionDeltaArray._attributes(), **cls_args}.keys():
            attr = getattr(self, a, None)
            if attr is None:
                continue

            if id(attr) in memo:
                # attribute is a reference to the data of another field
                h5_group.attrs[a] = memo[id(attr)]
            else:
                # attribute is stored as part of this in PositionArray
                h5_sub_group = h5_group.create_group(a)
                h5_sub_group.attrs["fieldname"] = a
                memo[id(attr)] = f"{h5_group.attrs['fieldname']}.{a}"
                attr._write(h5_sub_group, memo)  # Potential recursive call


class VelocityArray(PosBase):
    """Base class for Velocity arrays

    This VelocityArray should not be instantiated. Instead instantiate one of
    the system specific subclasses. The intended usage will be through a PosVelArray
    """

    cls_name = "VelocityArray"

    def __new__(cls, val, ref_pos, **vel_args):
        """Create a new VelocityArray"""
        if cls.system is None or cls.column_names is None:
            raise ValueError(
                f"{cls.__name__} cannot be instantiated. Use VelocityArray(val=..., system={cls.system!r}) instead"
            )

        obj = np.asarray(val, dtype=float, order="C").view(cls)
        obj.system = cls.system
        # Reference position needed to make conversions to other systems
        obj.ref_pos = ref_pos
        for attr in cls._attributes().keys():
            setattr(obj, attr, vel_args.get(attr))

        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new PositionDelta is created"""
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
        self.ref_pos = getattr(obj, "ref_pos", None)

    @classmethod
    def convert_to(cls, vel: "VelocityArray", converter: Callable) -> "VelocityArray":
        """Convert the position to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position 
        """
        attrs = {a: getattr(vel, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS[cls.cls_name][cls.system](converter(vel), ref_pos=vel.ref_pos, **attrs)

    def __add__(self, _):
        """self + other"""
        return NotImplemented

    def __radd__(self, _):
        """other + self"""
        return NotImplemented

    def __sub__(self, _):
        """self - other"""
        return NotImplemented

    def __rsub__(self, _):
        """other - self"""
        return NotImplemented


class VelocityDeltaArray(PosBase):
    """Base class for Velocity arrays

    This VelocityArray should not be instantiated. Instead instantiate one of
    the system specific subclasses. The intended usage will be through a PosVelArray
    """

    cls_name = "VelocityDeltaArray"

    def __new__(cls, val, ref_pos, **vel_args):
        """Create a new VelocityArray"""
        if cls.system is None or cls.column_names is None:
            raise ValueError(
                f"{cls.__name__} cannot be instantiated. Use VelocityDelta(val=..., system={cls.system!r}) instead"
            )

        obj = np.asarray(val, dtype=float, order="C").view(cls)
        obj.system = cls.system
        # Reference position needed to make conversions to other systems
        obj.ref_pos = ref_pos
        for attr in cls._attributes().keys():
            setattr(obj, attr, vel_args.get(attr))

        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new VelocityDelta is created"""
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
        self.ref_pos = getattr(obj, "ref_pos", None)

    @classmethod
    def convert_to(cls, vel: "VelocityDeltaArray", converter: Callable) -> "VelocityDeltaArray":
        """Convert the position to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position 
        """
        attrs = {a: getattr(vel, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS[cls.cls_name][cls.system](converter(vel), ref_pos=vel.ref_pos, **attrs)

    def __add__(self, _):
        """self + other"""
        return NotImplemented

    def __radd__(self, _):
        """other + self"""
        return NotImplemented

    def __sub__(self, _):
        """self - other"""
        return NotImplemented

    def __rsub__(self, _):
        """other - self"""
        return NotImplemented


class PosVelArray(PositionArray):
    """Base class for Position and Velocity arrays

    This PosVelArray should not be instantiated. Instead instantiate one of
    the system specific subclasses, typically using the Position factory
    function.
    """

    cls_name = "PosVelArray"

    @staticmethod
    def create(val: np.ndarray, system: str, **pos_args: Any) -> "PosVelArray":
        """Factory for creating PosVelArrays for different systems

        See each position class for exact optional parameters.

        Args:
            val:       Array of position and velocity values.
            system:    Name of position system.
            pos_args:  Additional arguments used to create the PosVelArray.

        Returns:
            Array with positions in the given system.
        """
        if system not in _SYSTEMS["PosVelArray"]:
            systems = ", ".join(_SYSTEMS["PosVelArray"])
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        return _SYSTEMS["PosVelArray"][system](val, **pos_args)

    @classmethod
    def from_posvel(cls, val: np.ndarray, other: "PosVelArray") -> "PosVelArray":
        """Create a new posvel object with given values and same attributes as other 

        Factory method for creating a array with the given
        values. Attributes will be copied from the other position.
        """
        attrs = {a: getattr(other, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS["PosVelArray"][other.system](val, **attrs)

    @classmethod
    def convert_to(cls, pos: "PosVelArray", converter: Callable) -> "PosVelArray":
        """Convert the position to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position 
        """
        attrs = {a: getattr(pos, a, None) for a in cls._attributes().keys()}
        return _SYSTEMS["PosVelArray"][cls.system](converter(pos), **attrs)

    @property
    def pos(self):
        attrs = {a: getattr(self, a, None) for a in self._attributes().keys()}
        return _SYSTEMS["PositionArray"][self.system](self.val[:, 0:3], **attrs)

    @property
    def vel(self):
        attrs = {a: getattr(self, a, None) for a in self._attributes().keys()}
        return _SYSTEMS["VelocityArray"][self.system](self.val[:, 3:6], ref_pos=self.pos, **attrs)

    def __add__(self, other):
        """self + other"""
        if isinstance(other, PosVelDeltaArray):
            if self.system != other.system:
                return NotImplemented
            return self.from_position(val=self.val + other.val, other=self)

        elif isinstance(other, PosVelArray):
            # pos1 + pos2 does not make sense
            return NotImplemented

        return NotImplemented

    def __radd__(self, other):
        """other + self"""
        if isinstance(other, PosVelDeltaArray):
            if self.system != other.system:
                return NotImplemented

        elif isinstance(other, PosVelArray):
            # pos1 + pos2 does not make sense
            return NotImplemented

        return NotImplemented

    def __sub__(self, other):
        """self - other"""

        if isinstance(other, PosVelArray):
            if self.system != other.system:
                return NotImplemented
            try:
                return PosVelDeltaArray.from_position(val=self.val - other.val, other=self)
            except KeyError:
                return NotImplemented

        elif isinstance(other, PosVelDeltaArray):
            if self.system != other.system:
                return NotImplemented
            return self.from_position(val=self.val - other.val, other=self)

        return NotImplemented

    def __rsub__(self, other):
        """other - self"""
        if isinstance(other, PosVelArray):
            if self.system != other.system:
                return NotImplemented

        elif isinstance(other, PosVelDeltaArray):
            if self.system != other.system:
                return NotImplemented

        return NotImplemented

    def __deepcopy__(self, memo):
        """Deep copy a PosVelArray

        Makes sure references to other objects are updated correctly
        """
        attrs = {a: copy.deepcopy(getattr(self, a, None), memo) for a in self._attributes().keys()}
        new_pos = PosVelArray.create(val=np.asarray(self).copy(), system=self.system, **attrs)
        memo[id(self)] = new_pos
        return new_pos

    @classmethod
    def _read(cls, h5_group, memo):
        system = h5_group.attrs["system"]
        ellipsoid_ = ellipsoid.get(h5_group.attrs["ellipsoid"])

        pos_args = {}
        for a, attr_cls in PosVelArray._attributes().items():
            if a in h5_group.attrs:
                # attribute is a reference to the data of another field
                pos_args.update({a: memo[h5_group.attrs[a]]})
            elif a in h5_group and isinstance(h5_group[a], type(h5_group)):
                # attribute is a part of this group and is not in a separate field
                arg = attr_cls._read(h5_group[a], memo)
                pos_args.update({a: arg})
                memo[f"{h5_group.attrs['fieldname']}.{a}"] = arg

        val = h5_group[h5_group.attrs["fieldname"]][...]

        return cls.create(val, system=system, ellipsoid=ellipsoid_, **pos_args)

    def _write(self, h5_group, memo):
        h5_group.attrs["system"] = self.system
        h5_group.attrs["ellipsoid"] = self.ellipsoid.name
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        for a in PosVelArray._attributes().keys():
            attr = getattr(self, a, None)
            if attr is None:
                continue

            if id(attr) in memo:
                # attribute is a reference to the data of another field
                h5_group.attrs[a] = memo[id(attr)]
            else:
                # attribute is stored as part of this in PosVelArray
                h5_sub_group = h5_group.create_group(a)
                h5_sub_group.attrs["fieldname"] = a
                memo[id(attr)] = f"{h5_group.attrs['fieldname']}.{a}"
                attr._write(h5_sub_group, memo)  # Potential recursive call


#
# Position Delta
#
class PosVelDeltaArray(PositionDeltaArray):
    """Base class for position and velocity deltas

    This PosVelDeltaArray should not be instantiated. Instead instantiate one
    of the system specific subclasses, typically using the PositionDelta
    factory function.
    """

    system = None
    column_names = None
    cls_name = "PosVelDeltaArray"

    @staticmethod
    def create(val: np.ndarray, system: str, ref_pos, **delta_args: Any) -> "PosVelDeltaArray":
        """Factory for creating PosVelDeltaArrays for different systems

        See each position delta class for exact optional parameters.

        Args:
            val:         Array of position deltas.
            system:      Name of position system.
            ref_pos:     Array of reference positions.
            delta_args:  Additional arguments used to create the PosVelDeltaArray.

        Returns:
            Array with positions in the given system.
        """
        if system not in _SYSTEMS["PosVelDeltaArray"]:
            systems = ", ".join(_SYSTEMS["PosVelDeltaArray"])
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        return _SYSTEMS["PosVelDeltaArray"][system](val, ref_pos, **delta_args)

    @property
    def pos(self):
        attrs = {a: getattr(self, a, None) for a in self._attributes().keys()}
        return _SYSTEMS["PositionDeltaArray"][self.system](self.val[:, 0:3], ref_pos=self.ref_pos, **attrs)

    @property
    def vel(self):
        attrs = {a: getattr(self, a, None) for a in self._attributes().keys()}
        return _SYSTEMS["VelocityDeltaArray"][self.system](self.val[:, 3:6], ref_pos=self.ref_pos, **attrs)

    def __sub__(self, other):
        """self - other"""

        if isinstance(other, PosVelArray):
            if self.system != other.system:
                return NotImplemented
            try:
                return PosVelDeltaArray.from_position(val=self.val - other.val, other=self)
            except KeyError:
                return NotImplemented

        elif isinstance(other, PosVelDeltaArray):
            if self.system != other.system:
                return NotImplemented
            return self.from_position(val=self.val - other.val, other=self)

    def __deepcopy__(self, memo):
        """Deep copy a PositionDeltaArray
 
        Makes sure references to other objects are updated correctly
        """
        attrs = {a: copy.deepcopy(getattr(self, a, None), memo) for a in list(self._attributes().keys()) + ["ref_pos"]}
        new_pos = PosVelDeltaArray.create(val=np.asarray(self).copy(), system=self.system, **attrs)
        memo[id(self)] = new_pos
        return new_pos

    @classmethod
    def _read(cls, h5_group, memo):
        system = h5_group.attrs["system"]

        cls_args = {"ref_pos": PosVelArray}
        delta_args = {}
        for a, attr_cls in {**cls._attributes(), **cls_args}.items():
            if a in h5_group.attrs:
                # attribute is a reference to the data of another field
                delta_args.update({a: memo[h5_group.attrs[a]]})
            elif a in h5_group and isinstance(h5_group[a], type(h5_group)):
                # attribute is a part of this group and is not in a separate field
                arg = attr_cls._read(h5_group[a], memo)
                delta_args.update({a: arg})
                memo[f"{h5_group.attrs['fieldname']}.{a}"] = arg

        val = h5_group[h5_group.attrs["fieldname"]][...]

        return cls.create(val, system=system, **delta_args)

    def _write(self, h5_group, memo):
        h5_group.attrs["system"] = self.system
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        cls_args = {"ref_pos": PosVelArray}
        for a in {**PosVelDeltaArray._attributes(), **cls_args}.keys():
            attr = getattr(self, a, None)
            if attr is None:
                continue

            if id(attr) in memo:
                # attribute is a reference to the data of another field
                h5_group.attrs[a] = memo[id(attr)]
            else:
                # attribute is stored as part of this in PosVelArray
                h5_sub_group = h5_group.create_group(a)
                h5_sub_group.attrs["fieldname"] = a
                memo[id(attr)] = f"{h5_group.attrs['fieldname']}.{a}"
                attr._write(h5_sub_group, memo)  # Potential recursive call
