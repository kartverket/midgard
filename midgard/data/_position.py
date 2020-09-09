""" Module for dealing with positions, velocities and position corrections in different coordinate systems
"""
# Standard library imports
from typing import Any, Callable, Dict, List, Tuple
import copy
import sys
import weakref

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import exceptions
from midgard.math import rotation
from midgard.math import ellipsoid
from midgard.math import nputil

_ATTRIBUTES: Dict[str, List[str]] = dict()  # Populated by register_attribute()
_FIELDS: Dict[str, Dict[str, str]] = dict()  # Populated by register_field()
_UNITS: Dict[str, Dict[str, str]] = dict()  # Populated by register_field()
_SYSTEMS: Dict[str, Dict[str, Callable]] = dict()  # Populated by register_system()
_CONVERSIONS: Dict[str, Dict[Tuple[str, str], Callable]] = dict()  # Populated by register_system()
_CONVERSION_HOPS: Dict[str, Dict[Tuple[str, str], List[str]]] = dict()  # Cache for to_system()


def register_attribute(cls: Callable, name: str) -> None:
    """Function used to register new attributes on position arrays

    The registered attributes will be available as attributes on PositionArray
    and its subclasses. In addition, each attribute can be given as a parameter
    when creating a PositionArray.

    The reason for using this register-function instead of a regular attribute
    is to allow additional attributes to be added on all position systems.

    Args:
        cls:      Class to register the attribute for
        name:     Name of attribute
    """
    _ATTRIBUTES.setdefault(cls.__name__, list()).append(name)


def register_field(units: List[str], dependence: str = None) -> Callable:
    """Decorator used to register fields and their units

    Args: 
    units:             units for the field (tuple of strings)
    dependance:        name of attribute that needs to be set for field to make sense
    """

    def wrapper(func: Callable) -> Callable:
        field = func.__name__
        func_class = func.__qualname__.split(".")[0]
        _FIELDS.setdefault(func_class, dict())[field] = dependence
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
        _SYSTEMS[cls.cls_name][name] = cls

        conversions = _CONVERSIONS.setdefault(cls.cls_name, dict())

        if convert_to:
            for to_system, converter in convert_to.items():
                conversions[(name, to_system)] = converter
        if convert_from:
            for from_system, converter in convert_from.items():
                conversions[(from_system, name)] = converter
        return cls

    return wrapper


def _find_conversion_hops(cls: str, hop: Tuple[str, str]) -> List[Tuple[str, str]]:
    """Calculate the hops needed to convert between systems using breadth first search"""
    start_sys, target_sys = hop
    queue = [(start_sys, [])]
    visited = set()

    if start_sys == target_sys:
        return [hop]

    while queue:
        from_sys, hops = queue.pop(0)
        for to_sys in [t for f, t in _CONVERSIONS[cls] if f == from_sys]:
            one_hop = (from_sys, to_sys)
            if to_sys == target_sys:
                return hops + [one_hop]
            if one_hop not in visited:
                visited.add(one_hop)
                queue.append((to_sys, hops + [one_hop]))

    raise exceptions.UnknownConversionError(f"Can't convert {cls} from {start_sys!r} to {target_sys!r}")


class PosBase(np.ndarray):
    """Base class for the various position and velocity arrays"""

    cls_name = "noname"
    system = None
    column_names = None
    _units = None

    @property
    def val(self):
        """Position as a plain numpy array"""
        if "val" not in self._cache:
            self._cache["val"] = np.asarray(self)
        return self._cache["val"]

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
        if "mat" not in self._cache:
            if self.is_transposed:
                if self.ndim == 1:
                    self._cache["mat"] = self.val[None, :].T
                else:
                    self._cache["mat"] = self.val[:, None, :].T
            else:
                if self.ndim == 1:
                    self._cache["mat"] = self.val[:, None]
                else:
                    self._cache["mat"] = self.val[:, :, None]
        return self._cache["mat"]

    @property
    def is_transposed(self):
        # Because we forced order == "C" on creation
        return self.flags.f_contiguous

    @property
    def unit_vector(self):
        """Compute unit vector of position from system origo"""
        return nputil.unit_vector(self.val)

    @property
    @register_field(units=("meter"))
    def length(self):
        """Compute length"""
        return nputil.norm(self)

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

        if system in self._cache:
            return self._cache[system]

        # Convert to new system
        hop = (self.system, system)
        if hop in _CONVERSIONS[self.cls_name]:
            self._cache[system] = _SYSTEMS[self.cls_name][system].convert_to(self, _CONVERSIONS[self.cls_name][hop])
            return self._cache[system]

        if hop not in _CONVERSION_HOPS.setdefault(self.cls_name, {}):
            _CONVERSION_HOPS[self.cls_name][hop] = _find_conversion_hops(self.cls_name, hop)

        val = self
        for one_hop in _CONVERSION_HOPS[self.cls_name][hop]:
            val = _SYSTEMS[self.cls_name][one_hop[-1]].convert_to(val, _CONVERSIONS[self.cls_name][one_hop])
            self._cache[one_hop[-1]] = val
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

        # Units of system specific properties
        elif field in _UNITS.get(cls.__name__, {}):
            return _UNITS[cls.__name__][field]

        # Units of properties of parent class
        elif field in _UNITS.get(getattr(cls.__base__.__base__, "cls_name", ""), {}):
            return _UNITS[cls.__base__.__base__.cls_name][field]

        # Units of systems
        elif mainfield in _SYSTEMS[cls.cls_name]:
            return _SYSTEMS[cls.cls_name][mainfield].unit(subfield)
        else:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    def fieldnames(self):
        """Return list of valid attributes for this object"""
        # Pick one element to avoid doing calculations on a large array 
        obj = self if len(self) == 1 else self[0]

        systems_and_columns = []
        for system in obj._systems():
            try:
                _find_conversion_hops(obj.cls_name, (obj.system, system))
                # Add systems
                systems_and_columns.append(system)
                for column in _SYSTEMS[obj.cls_name][system].column_names:
                    # Add system columns
                    systems_and_columns.append(f"{system}.{column}")
                for system_field in _FIELDS.get(_SYSTEMS[obj.cls_name][system].__name__, {}):
                    # Add system fields
                    try:
                        getattr(getattr(obj,system), system_field)
                        systems_and_columns.append(f"{system}.{system_field}")
                    except exceptions.InitializationError:
                        pass # This system field cannot be computed. Skipping
            except exceptions.UnknownConversionError:
                pass  # Skip systems that cannot be converted to

        useable_fields = []
        for field in self._fields():
            try:
                getattr(obj, field)
                useable_fields.append(field)
            except exceptions.InitializationError:
                # This field cannot be computed. Skipping
                pass

        return self._attributes() + systems_and_columns + useable_fields

    def plot_fields(self):
        valid_fields = set(self.fieldnames())
        return sorted(list(valid_fields - set(self._attributes())))

    @classmethod
    def _fields(cls):
        _cls = cls
        fields = []
        while _cls is not None:
            fields += list(_FIELDS.get(_cls.__name__, {}).keys())
            _cls = _cls.__base__
        return fields

    @classmethod
    def _attributes(cls):
        return _ATTRIBUTES.get(cls.cls_name, [])

    @classmethod
    def _systems(cls):
        return list(_SYSTEMS.get(cls.cls_name, {}).keys())

    def __setitem__(self, key, item):
        self.clear_cache()  # Clear cache when any elements change
        if self._dependent_objs:
            for o in self._dependent_objs:
                if o() is None:
                    continue
                o().clear_cache()  # Clear cache of dependent obj
        return super().__setitem__(key, item)

    def __setattr__(self, key, value):
        self.clear_cache()  # Clear cache if any attributes change
        if key in self._attributes():
            prev_attr_value = getattr(self, key, None)
            if prev_attr_value is not None:
                try:
                    prev_attr_value.remove_dependency(self)
                except AttributeError:
                    pass
            if value is not None:
                try:
                    value.add_dependency(self)
                except AttributeError:
                    pass
        return super().__setattr__(key, value)

    def add_dependency(self, dependency):
        self._dependent_objs.append(weakref.ref(dependency))

        # Clean out references that have been garbage collected
        dead_refs = [obj for obj in self._dependent_objs if obj() is None]
        for element in dead_refs:
            self._dependent_objs.remove(element)

    def remove_dependency(self, dependency):
        try:
            idx = next(idx for idx, obj in enumerate(self._dependent_objs) if id(obj()) == id(dependency))
            del self._dependent_objs[idx]
        except StopIteration:
            pass

    def clear_cache(self):
        if getattr(self, "_cache", {}) is not None:
            for k, v in getattr(self, "_cache", {}).items():
                if k in self._systems():
                    try:
                        v.other.remove_dependency(v)
                    except AttributeError:
                        pass
        super().__setattr__("_cache", dict())

    def __getattr__(self, key):
        """Get attributes with dot notation

        Add systems and column names to attributes on Position and PostionDelta arrays.

        Args:
            key:  Name of attribute.

        Returns:
            Value of attribute.
        """
        mainfield, _, subfield = key.partition(".")

        if subfield:
            return getattr(getattr(self, mainfield), subfield)

        # Convert to a different system
        if key in _SYSTEMS[self.cls_name]:
            return self.to_system(key)

        # Return one column as a regular numpy array
        elif key in self.column_names:
            idx = self.column_names.index(key)
            if self.ndim == 1:
                return self.val[idx]
            else:
                if self.is_transposed:
                    return self.val[idx, :]
                else:
                    return self.val[:, idx]

        # Raise error for unknown attributes
        else:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __dir__(self):
        """List all fields and attributes on the PosDeltaBase array"""
        return super().__dir__() + list(_SYSTEMS[self.cls_name]) + list(self.column_names)

    def __len__(self):
        """Number of positions in Array"""
        if self.ndim == 1:
            return 1;
        return super().__len__()

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
    type = "position"
    systems = _SYSTEMS.setdefault(cls_name, dict())

    def __new__(cls, val, ellipsoid=ellipsoid.GRS80, **pos_args):
        """Create a new Position"""
        if cls.system is None or cls.column_names is None:
            raise ValueError(
                f"{cls.cls_name} cannot be instantiated. Use {cls.cls_name.strip('Array')}(val=..., system={cls.system!r}) instead"
            )

        obj = np.asarray(val, dtype=float, order="C").view(cls)
        obj.system = cls.system
        obj.ellipsoid = ellipsoid
        for attr in cls._attributes():
            setattr(obj, attr, pos_args.get(attr))

        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new Position is created"""
        self._cache = dict()
        self._dependent_objs = list()

        if obj is None:
            return

        # Validate shape
        num_columns = len(self.column_names)
        if self.shape[-1] != num_columns:
            column_names = ", ".join(self.column_names)
            raise ValueError(f"{type(self).__name__!r} requires {num_columns} columns: {column_names}")

        if self.ndim > 2:
            raise ValueError(f"{type(self).__name__!r} must be a 1- or 2-dimensional array with {num_columns} columns")

        # Copy attributes from the original object
        self.system = getattr(obj, "system", None)
        self.ellipsoid = getattr(obj, "ellipsoid", ellipsoid.GRS80)
        for attr in self._attributes():
            attr_sliced = getattr(obj, f"_{attr}_sliced", None)
            if attr_sliced is not None:

                setattr(self, attr, attr_sliced)
            else:
                setattr(self, attr, getattr(obj, attr, None))

    def __getitem__(self, item):
        """Update attributes with correct shape, used by __array_finalize__"""

        # Get column
        if isinstance(item, int) and self.is_transposed:
            return getattr(self, self.column_names[item])

        from_super = super().__getitem__(item)

        # Get row or rows
        if isinstance(item, (int, np.int_, slice)):
            pos_args = {}
            for attr in self._attributes():
                orig_value = getattr(self, attr, None)
                if orig_value is not None:
                    sliced_value = orig_value[item]
                    sliced_attr = f"_{attr}_sliced"
                    setattr(self, sliced_attr, sliced_value)
                    pos_args[attr] = sliced_value
            return self.__class__(from_super, self.ellipsoid, **pos_args)

        return from_super

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
        attrs = {a: getattr(other, a, None) for a in cls._attributes()}
        return _SYSTEMS[cls.cls_name][other.system](val, **attrs)

    @classmethod
    def empty_from(cls, other: "PositionArray") -> "PositionArray":
        """Create a new position delta of the same type as other but with NaN values
        """
        return _SYSTEMS[cls.cls_name][other.system](np.full(other.shape, fill_value=np.nan), ellipsoid=ellipsoid)

    @classmethod
    def convert_to(cls, pos: "PositionArray", converter: Callable) -> "PositionArray":
        """Convert the position to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position 
        """
        attrs = {a: getattr(pos, a, None) for a in cls._attributes()}
        return _SYSTEMS[cls.cls_name][cls.system](converter(pos), **attrs)

    def subset(self, idx, memo):
        """Create a subset """
        old_id = id(self)
        if old_id in memo:
            return memo[old_id]

        val = np.asarray(self)[idx]
        pos_args = dict()

        for attr_name in self._attributes():
            attr = getattr(self, attr_name, None)
            if attr is None:
                continue

            old_id_attr = id(attr)
            if old_id_attr in memo:
                pos_args[attr_name] = memo[old_id_attr]
            else:
                pos_args[attr_name] = attr.subset(idx, memo)
                memo[old_id_attr] = pos_args[attr_name]

        new_pos = _SYSTEMS[self.cls_name][self.system](val, **pos_args)
        memo[old_id] = new_pos
        return new_pos

    @classmethod
    def insert(cls, a, pos, b, memo):
        """Insert b into a at index pos"""
        old_id_a = id(a)
        if old_id_a in memo:
            return memo[old_id_a][-1]

        old_id_b = id(b)
        if old_id_b in memo:
            return memo[old_id_b][-1]

        if b is not None:
            val = np.insert(np.asarray(a), pos, np.asarray(b.to_system(a.system)), axis=0)
        else:
            val = np.asarray(a)

        pos_args = dict()

        for attr_name in cls._attributes():
            a_attr = getattr(a, attr_name, None)
            b_attr = getattr(b, attr_name, None)
            if a_attr is None and b_attr is None:
                continue

            old_id_a_attr = id(a_attr)
            old_id_b_attr = id(b_attr)
            if old_id_a_attr in memo:
                pos_args[attr_name] = memo[old_id_a_attr][-1]
            elif old_id_b_attr in memo:
                pos_args[attr_name] = memo[old_id_b_attr][-1]
            else:
                if a_attr is not None and b_attr is not None:
                    attr_cls = a_attr.__class__
                    pos_args[attr_name] = attr_cls.insert(a_attr, pos, b_attr, memo)
                elif a_attr is None:
                    attr_cls = a_attr.__class__
                    print("todo: check empty_from argument")
                    empty_attr = attr_cls.empty_from(a)
                    pos_args[attr_name] = attr_cls.insert(empty_attr, pos, b_attr, memo)
                    memo.pop(id(empty_attr), None)
                elif b_attr is None:
                    attr_cls = a_attr.__class__
                    print("todo: check empty_from argument")
                    empty_attr = attr_cls.empty_from(a)
                    pos_args[attr_name] = attr_cls.insert(a_attr, pos, empty_attr, memo)
                    memo.pop(id(empty_attr), None)

        new_pos = _SYSTEMS[cls.cls_name][a.system](val, ellipsoid=a.ellipsoid, **pos_args)
        memo[old_id_a] = (a, new_pos)
        memo[old_id_b] = (b, new_pos)
        return new_pos

    @property
    def pos(self):
        """Allows base classes to implement this attribute"""
        return self

    @property
    def enu2trs(self):
        if "enu2trs" not in self._cache:
            lat, lon, _ = self.pos.llh.val.T
            self._cache["enu2trs"] = rotation.enu2trs(lat, lon)
        return self._cache["enu2trs"]

    @property
    def trs2enu(self):
        if "trs2enu" not in self._cache:
            lat, lon, _ = self.pos.llh.val.T
            self._cache["trs2enu"] = rotation.trs2enu(lat, lon)
        return self._cache["trs2enu"]

    @property
    def enu_east(self):
        """ Unit vector for in the east direction"""
        return nputil.take(self.enu2trs, 0)

    @property
    def enu_north(self):
        """ Unit vector for in the north direction"""
        return nputil.take(self.enu2trs, 1)

    @property
    def enu_up(self):
        """ Unit vector for in the up direction"""
        return nputil.take(self.enu2trs, 2)

    def vector_to(self, other: "PositionArray") -> np.ndarray:
        """Vector to other positions in current system

        Args:
            other:  Other position array.

        Returns:
            Array of vectors to other position array.
        """
        return other.pos.to_system(self.system).val - self.pos.val

    @property
    @register_field(units=("meter", "meter", "meter"), dependence="other")
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
        return nputil.norm(self.vector_to(other))

    @property
    @register_field(units=("meter",), dependence="other")
    def distance(self):
        """Distance to registered other position"""
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")

        if "distance" not in self._cache:
            self._cache["distance"] = self.distance_to(self.other)
        return self._cache["distance"]

    def direction_to(self, other):
        if isinstance(other, PositionArray):
            return self.vector_to(other) / nputil.col(self.distance_to(other))
        else:
            return other.direction_from(self)

    @property
    @register_field(units=("unitless", "unitless", "unitless"), dependence="other")
    def direction(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")

        if "direction" not in self._cache:
            self._cache["direction"] = self.direction_to(self.other)
        return self._cache["direction"]

    def azimuth_to(self, other):
        trs_dir = self.trs.direction_to(other.trs)
        east_proj = np.squeeze(nputil.row(trs_dir) @ nputil.col(self.enu_east))
        north_proj = np.squeeze(nputil.row(trs_dir) @ nputil.col(self.enu_north))

        return np.arctan2(east_proj, north_proj)

    @property
    @register_field(units=("radians",), dependence="other")
    def azimuth(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")

        if "azimuth" not in self._cache:
            self._cache["azimuth"] = self.azimuth_to(self.other)
        return self._cache["azimuth"]

    def elevation_to(self, other):
        trs_dir = self.trs.direction_to(other.trs)
        up_proj = np.squeeze(nputil.row(trs_dir) @ nputil.col(self.enu_up))

        return np.arcsin(up_proj)

    @property
    @register_field(units=("radians",), dependence="other")
    def elevation(self):
        if self.other is None:
            raise exceptions.InitializationError("Other position is not defined")

        if "elevation" not in self._cache:
            self._cache["elevation"] = self.elevation_to(self.other)
        return self._cache["elevation"]

    def zenith_distance_to(self, other):
        return np.pi / 2 - self.elevation_to(other)

    @property
    @register_field(units=("radians",), dependence="other")
    def zenith_distance(self):
        if "zenith_distance" not in self._cache:
            self._cache["zenith_distance"] = np.pi / 2 - self.elevation
        return self._cache["zenith_distance"]

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
        return NotImplemented

    def __deepcopy__(self, memo):
        """Deep copy a PositionArray

        Makes sure references to other objects are updated correctly
        """
        attrs = {a: copy.deepcopy(getattr(self, a, None), memo) for a in self._attributes()}
        new_pos = PositionArray.create(val=np.asarray(self).copy(), system=self.system, **attrs)
        memo[id(self)] = new_pos
        return new_pos

    @classmethod
    def _read(cls, h5_group, memo):
        system = h5_group.attrs["system"]
        ellipsoid_ = ellipsoid.get(h5_group.attrs["ellipsoid"])

        pos_args = {}
        for a in PositionArray._attributes():
            if a in h5_group.attrs:
                # attribute is a reference to the data of another field
                fieldname = h5_group.attrs[a]
                if fieldname in memo:
                    # the other field has already been read
                    pos_args.update({a: memo[fieldname]})
                else:
                    # the other field has not been read yet
                    attr_group = h5_group.parent[fieldname]
                    cls_module, _, cls_name = attr_group.attrs["__class__"].rpartition(".")
                    attr_cls = getattr(sys.modules[cls_module], cls_name)
                    arg = attr_cls._read(attr_group, memo)
                    pos_args.update({a: arg})
                    memo[fieldname] = arg

            elif a in h5_group and isinstance(h5_group[a], type(h5_group)):
                # attribute is a part of this group and is not in a separate field
                cls_module, _, cls_name = h5_group[a].attrs["__class__"].rpartition(".")
                attr_cls = getattr(sys.modules[cls_module], cls_name)
                arg = attr_cls._read(h5_group[a], memo)
                pos_args.update({a: arg})
                memo[f"{h5_group.attrs['fieldname']}.{a}"] = arg

        val = h5_group[h5_group.attrs["fieldname"]][...]

        pos = cls.create(val, system=system, ellipsoid=ellipsoid_, **pos_args)
        memo[f"{h5_group.attrs['fieldname']}"] = pos
        return pos

    def _write(self, h5_group, memo):
        h5_group.attrs["system"] = self.system
        h5_group.attrs["ellipsoid"] = self.ellipsoid.name
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        for a in PositionArray._attributes():
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
                h5_sub_group.attrs["__class__"] = f"{attr.__class__.__module__}.{attr.__class__.__name__}"
                memo[id(attr)] = f"{h5_group.attrs['fieldname']}.{a}"
                attr._write(h5_sub_group, memo)  # Potential recursive call

        memo[id(self)] = h5_group.attrs["fieldname"]


class PositionDeltaArray(PosBase):
    """Base class for position deltas

    This PositionDeltaArray should not be instantiated. Instead instantiate one
    of the system specific subclasses, typically using the PositionDelta
    factory function.
    """

    cls_name = "PositionDeltaArray"
    type = "position_delta"
    systems = _SYSTEMS.setdefault(cls_name, dict())

    def __new__(cls, val, ref_pos, **delta_args):
        """Create a new Positiondelta"""
        if cls.system is None or cls.column_names is None:
            raise ValueError(
                f"{cls.cls_name} cannot be instantiated. Use {cls.cls_name.strip('Array')}(val=..., system={cls.system!r}) instead"
            )

        obj = np.asarray(val, dtype=float, order="C").view(cls)
        obj.system = cls.system
        obj.ref_pos = ref_pos
        for attr in cls._attributes():
            setattr(obj, attr, delta_args.get(attr))

        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new PositionDelta is created"""
        self._cache = dict()
        self._dependent_objs = list()

        if obj is None:
            return

        # Validate shape
        num_columns = len(self.column_names)
        if self.shape[-1] != num_columns:
            column_names = ", ".join(self.column_names)
            raise ValueError(f"{type(self).__name__!r} requires {num_columns} columns: {column_names}")

        if self.ndim > 2:
            raise ValueError(f"{type(self).__name__!r} must be a 1- or 2-dimensional array with {num_columns} columns")

        # Copy attributes from the original object
        self.system = getattr(obj, "system", None)

        for attr in self._attributes() + ["ref_pos"]:
            attr_sliced = getattr(obj, f"_{attr}_sliced", None)
            if attr_sliced is not None:
                setattr(self, attr, attr_sliced)
            else:
                setattr(self, attr, getattr(obj, attr, None))

    def __getitem__(self, item):
        """Update attributes with correct shape, used by __array_finalize__"""
        # Get column
        if isinstance(item, int) and self.is_transposed:
            return getattr(self, self.column_names[item])

        from_super = super().__getitem__(item)

        # Get row or rows
        if isinstance(item, (int, np.int_, slice)):
            pos_args = {}
            for attr in self._attributes() + ["ref_pos"]:
                orig_value = getattr(self, attr, None)
                if orig_value is not None:
                    sliced_value = orig_value[item]
                    sliced_attr = f"_{attr}_sliced"
                    setattr(self, sliced_attr, sliced_value)
                    pos_args[attr] = sliced_value
            return self.__class__(from_super, **pos_args)

        return from_super

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

    def plot_fields(self):
        return list(set(super().plot_fields()) - {"ref_pos"})

    def fieldnames(self):
        return super().fieldnames() + ["ref_pos"]

    @classmethod
    def from_position(cls, val: np.ndarray, other: "PositionArray") -> "PositionDeltaArray":
        """Create a new position delta with given values and same attributes as other position

        Factory method for creating a new position array with the given
        values. Attributes will be copied from the other position.
        """
        attrs = {a: getattr(other, a, None) for a in cls._attributes()}
        return _SYSTEMS[cls.cls_name][other.system](val, ref_pos=other, **attrs)

    @classmethod
    def empty_from(cls, other: "PositionDeltaArray") -> "PositionDeltaArray":
        """Create a new position delta of the same type as other but with NaN values
        """
        ref_pos = _SYSTEMS[other.ref_pos.cls_name][other.ref_pos.system](
            np.full(other.shape, fill_value=np.nan), ellipsoid=other.ellipsoid
        )
        return _SYSTEMS[cls.cls_name][other.system](
            np.full(other.shape, fill_value=np.nan), ellipsoid=ellipsoid, ref_pos=ref_pos
        )

    @classmethod
    def from_position_delta(cls, val: np.ndarray, other: "PositionDeltaArray") -> "PositionDeltaArray":
        """Create a new position with given values and same attributes as other position

        Factory method for creating a new position array with the given
        values. Attributes will be copied from the other position.
        """
        attrs = {a: getattr(other, a, None) for a in cls._attributes()}
        return _SYSTEMS[cls.cls_name][other.system](val, ref_pos=other.ref_pos, **attrs)

    @classmethod
    def convert_to(cls, pos_delta: "PositionDeltaArray", converter: Callable) -> "PositionDeltaArray":
        """Convert the position delta to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position delta 
        """
        attrs = {a: getattr(pos_delta, a, None) for a in cls._attributes()}
        return _SYSTEMS[cls.cls_name][cls.system](converter(pos_delta), ref_pos=pos_delta.ref_pos, **attrs)

    def subset(self, idx, memo):
        """Create a subset """
        old_id = id(self)
        if old_id in memo:
            return memo[old_id]

        old_id_ref_pos = id(self.ref_pos)

        val = np.asarray(self)[idx]
        pos_args = dict()

        for attr_name in self._attributes():
            attr = getattr(self, attr_name, None)
            if attr is None:
                continue

            old_id_attr = id(attr)
            if old_id_attr in memo:
                pos_args[attr_name] = memo[old_id_attr]
            else:
                pos_args[attr_name] = attr.subset(idx, memo)
                memo[old_id_attr] = pos_args[attr_name]

        if old_id_ref_pos in memo:
            ref_pos = memo[old_id_ref_pos]
        else:
            ref_pos = self.ref_pos.subset(idx, memo)
            memo[old_id_ref_pos] = ref_pos

        new_posdelta = _SYSTEMS[self.cls_name][self.system](val, ref_pos=ref_pos, **pos_args)
        memo[old_id] = new_posdelta
        return new_posdelta

    @classmethod
    def insert(cls, a, pos, b, memo):
        """Insert b into a at index pos"""
        old_id_a = id(a)
        if old_id_a in memo:
            return memo[old_id_a][-1]

        old_id_b = id(b)
        if old_id_b in memo:
            return memo[old_id_b][-1]

        old_id_ref_pos = id(a.ref_pos)

        val = np.insert(np.asarray(a), pos, np.asarray(b.to_system(a.system)), axis=0)
        pos_args = dict()

        for attr_name in cls._attributes():
            a_attr = getattr(a, attr_name, None)
            b_attr = getattr(b, attr_name, None)
            if a_attr is None and b_attr is None:
                continue

            old_id_a_attr = id(a_attr)
            old_id_b_attr = id(b_attr)
            if old_id_a_attr in memo:
                pos_args[attr_name] = memo[old_id_a_attr][-1]
            elif old_id_b_attr in memo:
                pos_args[attr_name] = memo[old_id_b_attr][-1]
            else:
                if a_attr is not None and b_attr is not None:
                    attr_cls = a_attr.__class__
                    pos_args[attr_name] = attr_cls.insert(a_attr, pos, b_attr, memo)
                elif a_attr is None:
                    attr_cls = a_attr.__class__
                    empty_attr = attr_cls.empty_from(a)
                    pos_args[attr_name] = attr_cls.insert(empty_attr, pos, b_attr, memo)
                    memo.pop(id(empty_attr), None)
                elif b_attr is None:
                    attr_cls = a_attr.__class__
                    empty_attr = attr_cls.empty_from(a)
                    pos_args[attr_name] = attr_cls.insert(a_attr, pos, empty_attr, memo)
                    memo.pop(id(empty_attr), None)

        if old_id_ref_pos in memo:
            new_ref_pos = memo[old_id_ref_pos][-1]
        else:
            new_ref_pos = a.ref_pos.insert(a.ref_pos, pos, b.ref_pos, memo)
            memo[old_id_ref_pos] = (a.ref_pos, new_ref_pos)

        new_posdelta = _SYSTEMS[cls.cls_name][a.system](val, ref_pos=new_ref_pos, **pos_args)
        memo[old_id_a] = (a, new_posdelta)
        memo[old_id_b] = (b, new_posdelta)
        return new_posdelta

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
        attrs = {a: copy.deepcopy(getattr(self, a, None), memo) for a in self._attributes() + ["ref_pos"]}
        new_pos = PositionDeltaArray.create(val=np.asarray(self).copy(), system=self.system, **attrs)
        memo[id(self)] = new_pos
        return new_pos

    @classmethod
    def _read(cls, h5_group, memo):
        system = h5_group.attrs["system"]

        delta_args = {}
        for a in cls._attributes() + ["ref_pos"]:
            if a in h5_group.attrs:
                # attribute is a reference to the data of another field
                fieldname = h5_group.attrs[a]
                if fieldname in memo:
                    # the other field has already been read
                    delta_args.update({a: memo[fieldname]})
                else:
                    # the other field has not been read yet
                    attr_group = h5_group.parent[fieldname]
                    cls_module, _, cls_name = attr_group.attrs["__class__"].rpartition(".")
                    attr_cls = getattr(sys.modules[cls_module], cls_name)
                    arg = attr_cls._read(attr_group, memo)
                    delta_args.update({a: arg})
                    memo[fieldname] = arg

            elif a in h5_group and isinstance(h5_group[a], type(h5_group)):
                # attribute is a part of this group and is not in a separate field
                cls_module, _, cls_name = h5_group[a].attrs["__class__"].rpartition(".")
                attr_cls = getattr(sys.modules[cls_module], cls_name)
                arg = attr_cls._read(h5_group[a], memo)
                delta_args.update({a: arg})
                memo[f"{h5_group.attrs['fieldname']}.{a}"] = arg

        val = h5_group[h5_group.attrs["fieldname"]][...]

        posdelta = cls.create(val, system=system, **delta_args)
        memo[f"{h5_group.attrs['fieldname']}"] = posdelta
        return posdelta

    def _write(self, h5_group, memo):
        h5_group.attrs["system"] = self.system
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        for a in self._attributes() + ["ref_pos"]:
            attr = getattr(self, a, None)
            if attr is None:
                continue

            if id(attr) in memo:
                # attribute is a reference to the data of another field
                h5_group.attrs[a] = memo[id(attr)]
            else:
                # attribute is stored as part of this in PositionDeltaArray
                h5_sub_group = h5_group.create_group(a)
                h5_sub_group.attrs["fieldname"] = a
                h5_sub_group.attrs["__class__"] = f"{attr.__class__.__module__}.{attr.__class__.__name__}"
                memo[id(attr)] = f"{h5_group.attrs['fieldname']}.{a}"
                attr._write(h5_sub_group, memo)  # Potential recursive call

        memo[id(self)] = h5_group.attrs["fieldname"]


class VelocityArray(PosBase):
    """Base class for Velocity arrays

    This VelocityArray should not be instantiated. Instead instantiate one of
    the system specific subclasses. The intended usage will be through a PosVelArray
    """

    cls_name = "VelocityArray"
    systems = _SYSTEMS.setdefault(cls_name, dict())

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
        for attr in cls._attributes():
            setattr(obj, attr, vel_args.get(attr))

        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new PositionDelta is created"""
        self._cache = dict()
        self._dependent_objs = list()

        if obj is None:
            return

        # Validate shape
        num_columns = len(self.column_names)
        if self.shape[-1] != num_columns:
            column_names = ", ".join(self.column_names)
            raise ValueError(f"{type(self).__name__!r} requires {num_columns} columns: {column_names}")

        if self.ndim > 2:
            raise ValueError(f"{type(self).__name__!r} must be a 1- or 2-dimensional array with {num_columns} columns")

        # Copy attributes from the original object
        self.system = getattr(obj, "system", None)
        self.ref_pos = getattr(obj, "ref_pos", None)

    @classmethod
    def convert_to(cls, vel: "VelocityArray", converter: Callable) -> "VelocityArray":
        """Convert the position to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position 
        """
        attrs = {a: getattr(vel, a, None) for a in cls._attributes()}
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
    systems = _SYSTEMS.setdefault(cls_name, dict())

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
        for attr in cls._attributes():
            setattr(obj, attr, vel_args.get(attr))

        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new VelocityDelta is created"""
        self._cache = dict()
        self._dependent_objs = list()

        if obj is None:
            return

        # Validate shape
        num_columns = len(self.column_names)
        if self.shape[-1] != num_columns:
            column_names = ", ".join(self.column_names)
            raise ValueError(f"{type(self).__name__!r} requires {num_columns} columns: {column_names}")

        if self.ndim > 2:
            raise ValueError(f"{type(self).__name__!r} must be a 1- or 2-dimensional array with {num_columns} columns")

        # Copy attributes from the original object
        self.system = getattr(obj, "system", None)
        self.ref_pos = getattr(obj, "ref_pos", None)

    @classmethod
    def convert_to(cls, vel: "VelocityDeltaArray", converter: Callable) -> "VelocityDeltaArray":
        """Convert the position to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position 
        """
        attrs = {a: getattr(vel, a, None) for a in cls._attributes()}
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
    type = "posvel"
    systems = _SYSTEMS.setdefault(cls_name, dict())

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
        attrs = {a: getattr(other, a, None) for a in cls._attributes()}
        return _SYSTEMS["PosVelArray"][other.system](val, **attrs)

    @classmethod
    def convert_to(cls, pos: "PosVelArray", converter: Callable) -> "PosVelArray":
        """Convert the position to the type of this class

        Applies the converter function that is provides and copies all registered attributes to the new position 
        """
        attrs = {a: getattr(pos, a, None) for a in cls._attributes()}
        return _SYSTEMS["PosVelArray"][cls.system](converter(pos), **attrs)

    @property
    def pos(self):
        if "pos" not in self._cache:
            attrs = {a: getattr(self, a, None) for a in self._attributes()}
            if self.ndim == 1:
                val = self.val[0:3]
            else:
                val = self.val[:, 0:3]
            self._cache["pos"] = _SYSTEMS["PositionArray"][self.system](val, **attrs)
        return self._cache["pos"]

    @property
    def vel(self):
        if "vel" not in self._cache:
            attrs = {a: getattr(self, a, None) for a in self._attributes()}
            if self.ndim == 1:
                val = self.val[3:6]
            else:
                val = self.val[:, 3:6]
            self._cache["vel"] = _SYSTEMS["VelocityArray"][self.system](val, ref_pos=self.pos, **attrs)
        return self._cache["vel"]

    @property
    def acr2trs(self):
        """Transformation matrix from local orbital reference system given with along-track, cross-track and radial
        directions to ITRS."""
        if "acr2trs" not in self._cache:
            if self.ndim == 1:
                self._cache["acr2trs"] = self.trs2acr.T
            else:
                self._cache["acr2trs"] = self.trs2acr.transpose(0, 2, 1)
        return self._cache["acr2trs"]

    @property
    def trs2acr(self):
        """Transformation matrix from ITRS to local orbital reference system given with along-track, cross-track and
        radial."""
        if "trs2acr" not in self._cache:
            r_unit = self.trs.pos.unit_vector
            v_unit = self.trs.vel.unit_vector
            c_unit = nputil.unit_vector(np.cross(r_unit, v_unit))
            a_unit = nputil.unit_vector(np.cross(c_unit, r_unit))
            self._cache["trs2acr"] = np.stack((a_unit, c_unit, r_unit), axis=1)
        return self._cache["trs2acr"]

    @property
    def acr_along(self):
        """ Unit vector for in the along-track direction"""
        return self.acr2trs[:, :, 0:1]

    @property
    def acr_cross(self):
        """ Unit vector for in the cross-track direction"""
        return self.acr2trs[:, :, 1:2]

    @property
    def acr_radial(self):
        """ Unit vector for in the radial (up) direction"""
        return self.trs.pos.unit_vector

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
        attrs = {a: copy.deepcopy(getattr(self, a, None), memo) for a in self._attributes()}
        new_pos = PosVelArray.create(val=np.asarray(self).copy(), system=self.system, **attrs)
        memo[id(self)] = new_pos
        return new_pos

    @classmethod
    def _read(cls, h5_group, memo):
        system = h5_group.attrs["system"]
        ellipsoid_ = ellipsoid.get(h5_group.attrs["ellipsoid"])

        pos_args = {}
        for a in PosVelArray._attributes():
            if a in h5_group.attrs:
                # attribute is a reference to the data of another field
                fieldname = h5_group.attrs[a]
                if fieldname in memo:
                    # the other field has already been read
                    pos_args.update({a: memo[fieldname]})
                else:
                    # the other field has not been read yet
                    attr_group = h5_group.parent[fieldname]
                    cls_module, _, cls_name = attr_group.attrs["__class__"].rpartition(".")
                    attr_cls = getattr(sys.modules[cls_module], cls_name)
                    arg = attr_cls._read(attr_group, memo)
                    pos_args.update({a: arg})
                    memo[fieldname] = arg
            elif a in h5_group and isinstance(h5_group[a], type(h5_group)):
                # attribute is a part of this group and is not in a separate field
                cls_module, _, cls_name = h5_group[a].attrs["__class__"].rpartition(".")
                attr_cls = getattr(sys.modules[cls_module], cls_name)
                arg = attr_cls._read(h5_group[a], memo)
                pos_args.update({a: arg})
                memo[f"{h5_group.attrs['fieldname']}.{a}"] = arg

        val = h5_group[h5_group.attrs["fieldname"]][...]
        posvel = cls.create(val, system=system, ellipsoid=ellipsoid_, **pos_args)
        memo[f"{h5_group.attrs['fieldname']}"] = posvel
        return posvel

    def _write(self, h5_group, memo):
        h5_group.attrs["system"] = self.system
        h5_group.attrs["ellipsoid"] = self.ellipsoid.name
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        for a in PosVelArray._attributes():
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
                h5_sub_group.attrs["__class__"] = f"{attr.__class__.__module__}.{attr.__class__.__name__}"
                memo[id(attr)] = f"{h5_group.attrs['fieldname']}.{a}"
                attr._write(h5_sub_group, memo)  # Potential recursive call

        memo[id(self)] = h5_group.attrs["fieldname"]


#
# Position Delta
#
class PosVelDeltaArray(PositionDeltaArray):
    """Base class for position and velocity deltas

    This PosVelDeltaArray should not be instantiated. Instead instantiate one
    of the system specific subclasses, typically using the PositionDelta
    factory function.
    """

    cls_name = "PosVelDeltaArray"
    type = "posvel_delta"
    systems = _SYSTEMS.setdefault(cls_name, dict())

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
        if "pos" not in self._cache:
            attrs = {a: getattr(self, a, None) for a in self._attributes()}
            if self.ndim == 1:
                val = self.val[3:6]
            else:
                val = self.val[:, 3:6]
            self._cache["pos"] = _SYSTEMS["PositionDeltaArray"][self.system](val, ref_pos=self.ref_pos, **attrs)
        return self._cache["pos"]

    @property
    def vel(self):
        if "vel" not in self._cache:
            attrs = {a: getattr(self, a, None) for a in self._attributes()}
            if self.ndim == 1:
                val = self.val[3:6]
            else:
                val = self.val[:, 3:6]
            self._cache["vel"] = _SYSTEMS["VelocityDeltaArray"][self.system](val, ref_pos=self.ref_pos, **attrs)
        return self._cache["vel"]

    def __sub__(self, other):
        """self - other"""
        if isinstance(other, PosVelDeltaArray):
            if self.system != other.system:
                return NotImplemented
            return other.from_position_delta(val=self.val - other.val, other=self)

        elif isinstance(other, PosVelArray):
            if self.system != other.system:
                return NotImplemented
            return other.from_position(val=self.val - other.val, other=other)

    def __deepcopy__(self, memo):
        """Deep copy a PositionDeltaArray
 
        Makes sure references to other objects are updated correctly
        """
        attrs = {a: copy.deepcopy(getattr(self, a, None), memo) for a in self._attributes() + ["ref_pos"]}
        new_pos = PosVelDeltaArray.create(val=np.asarray(self).copy(), system=self.system, **attrs)
        memo[id(self)] = new_pos
        return new_pos

    @classmethod
    def _read(cls, h5_group, memo):
        system = h5_group.attrs["system"]

        delta_args = {}
        for a in cls._attributes() + ["ref_pos"]:
            if a in h5_group.attrs:
                # attribute is a reference to the data of another field
                fieldname = h5_group.attrs[a]
                if fieldname in memo:
                    # the other field has already been read
                    delta_args.update({a: memo[fieldname]})
                else:
                    # the other field has not been read yet
                    attr_group = h5_group.parent[fieldname]
                    cls_module, _, cls_name = attr_group.attrs["__class__"].rpartition(".")
                    attr_cls = getattr(sys.modules[cls_module], cls_name)
                    arg = attr_cls._read(attr_group, memo)
                    delta_args.update({a: arg})
                    memo[fieldname] = arg

            elif a in h5_group and isinstance(h5_group[a], type(h5_group)):
                # attribute is a part of this group and is not in a separate field
                cls_module, _, cls_name = h5_group[a].attrs["__class__"].rpartition(".")
                attr_cls = getattr(sys.modules[cls_module], cls_name)
                arg = attr_cls._read(h5_group[a], memo)
                delta_args.update({a: arg})
                memo[f"{h5_group.attrs['fieldname']}.{a}"] = arg

        val = h5_group[h5_group.attrs["fieldname"]][...]

        posveldelta = cls.create(val, system=system, **delta_args)
        memo[f"{h5_group.attrs['fieldname']}"] = posveldelta
        return posveldelta

    def _write(self, h5_group, memo):
        h5_group.attrs["system"] = self.system
        h5_field = h5_group.create_dataset(h5_group.attrs["fieldname"], self.shape, dtype=self.dtype)
        h5_field[...] = self.val

        for a in self._attributes() + ["ref_pos"]:
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
                h5_sub_group.attrs["__class__"] = f"{attr.__class__.__module__}.{attr.__class__.__name__}"
                memo[id(attr)] = f"{h5_group.attrs['fieldname']}.{a}"
                attr._write(h5_sub_group, memo)  # Potential recursive call
