"""Array with positions
"""

# Standard library imports
from typing import Any, Callable, Dict, List, Tuple

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import exceptions
from midgard.math import rotation

_SYSTEMS: Dict[str, "PositionDeltaArray"] = dict()  # Populated by register_system()
_CONVERSIONS: Dict[Tuple[str, str], Callable] = dict()  # Populated by register_system()
_CONVERSION_HOPS: Dict[Tuple[str, str], List[str]] = dict()  # Cache for to_system()


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

    def wrapper(cls: Callable):
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

    raise exceptions.UnknownConversionError(f"Can't convert PositionDeltaArray from {start_sys!r} to {target_sys!r}")


#
# Position Delta
#
class PositionDeltaArray(np.ndarray):
    """Base class for position deltas

    This PositionDeltaArray should not be instatiated. Instead instantiate one
    of the system specific subclasses, typically using the PositionDelta
    factory function.
    """

    system = None
    column_names = None
    _systems = _SYSTEMS

    def __new__(cls, val, ref_pos, **delta_args):
        """Create a new Positiondelta"""
        if cls.system is None or cls.column_names is None:
            raise ValueError(
                f"{cls.__name__} cannot be instantiated. Use PositionDelta(val=..., system={cls.system!r}) instead"
            )

        obj = np.asarray(val, dtype=float, order="C").view(cls)
        obj.system = cls.system
        obj.ref_pos = ref_pos
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
        if system not in _SYSTEMS:
            systems = ", ".join(_SYSTEMS)
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        return _SYSTEMS[system](val, ref_pos, **delta_args)

    @property
    def val(self):
        """Position delta as a plain numpy array"""
        return np.asarray(self)

    @property
    def mat(self):
        """Position deltas as an array of matrices

        Adds an extra dimension, so that matrix multiplication can be performed
        effectively. By default .mat returns an array of column vectors. To
        effectively access row vectors instead, operate on a transposed delta:

        Example:

        >>> delta    # shape (2, 3)
        EnuPositionDelta([[0., 0., 1.],
                          [1., 1., 0.]])

        >>> delta.mat    # Column vectors, shape (2, 3, 1)
        array([[[0.],
                [0.],
                [1.]],

               [[1.],
                [1.],
                [0.]]])

        >>> delta.T.mat    # Row vectors, shape (2, 1, 3)
            array([[[0., 0., 1.]],

                   [[1., 1., 0.]]])
        """
        is_transposed = self.flags.f_contiguous  # Because we forced order == "C" on creation
        if is_transposed:
            return np.asarray(self)[:, None, :].T
        else:
            return np.asarray(self)[:, :, None]

    def to_system(self, system: str) -> "PositionDeltaArray":
        """Convert position to a different system

        Returns a new PositionDeltaArray with the same position in the new system.

        Args:
            system:  Name of new system.

        Returns:
            PositionDeltaArray representing the same positions in the new system.
        """
        # Don't convert if not necessary
        if system == self.system:
            return self

        # Raise error for unknown systems
        if system not in _SYSTEMS:
            systems = ", ".join(_SYSTEMS)
            raise exceptions.UnknownSystemError(f"System {system!r} unknown. Use one of {systems}")

        # Convert to new system
        hop = (self.system, system)
        if hop in _CONVERSIONS:
            return _SYSTEMS[system](_CONVERSIONS[hop](self), ref_pos=self.ref_pos)

        if hop not in _CONVERSION_HOPS:
            _CONVERSION_HOPS[hop] = _find_conversion_hops(hop)

        val = self
        for one_hop in _CONVERSION_HOPS[hop]:
            print(one_hop)
            val = _CONVERSIONS[one_hop](val)
        return _SYSTEMS[system](val, ref_pos=self.ref_pos)

    def __getattr__(self, key):
        """Get attributes with dot notation

        Add systems and column names to attributes on Position arrays.

        Args:
            key:  Name of attribute.

        Returns:
            Value of attribute.
        """
        # Convert to a different system
        if key in _SYSTEMS:
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
        return super().__dir__() + list(_SYSTEMS) + list(self.column_names)

    def __add__(self, other):
        """Add position delta with other object

        Convert other position delta to correct system. If other is a position, delegate to that object. In all other cases, treat
        """
        print(f"{type(self).__name__}.__add__({other})")
        if isinstance(other, PositionDeltaArray):
            return self.create(
                val=np.asarray(self) + np.asarray(other.to_system(self.system)),
                system=self.system,
                ref_pos=self.ref_pos,
            )
            return super().__add__(other.to_system(self.system))
            #        elif isinstance(other, PositionDeltaArray):
            #            return NotImplemented
        else:
            return NotImplemented

    def __radd__(self, other):
        print(f"{type(self).__name__}.__radd__({other})")
        return NotImplemented

    def __iadd__(self, other):
        print(f"{type(self).__name__}.__iadd__({other})")
        return self.__add__(other)

    def __sub__(self, other):
        print(f"{type(self).__name__}.__sub__({other})")
        if isinstance(other, PositionDeltaArray):
            return self.create(
                val=np.asarray(self) - np.asarray(other.to_system(self.system)),
                system=self.system,
                ref_pos=self.ref_pos,
            )
        return NotImplemented

    def __rsub__(self, other):
        print(f"{type(self).__name__}.__rsub__({other})")
        return NotImplemented

    def __isub__(self, other):
        print(f"{type(self).__name__}.__isub__({other})")
        return self.__sub__(other)

    def __matmul__(self, other):
        return NotImplemented

    def __rmatmul__(self, other):
        return NotImplemented

    def __imatmul__(self, other):
        return NotImplemented


def delta_trs2enu(trs: "TrsPositionDelta") -> np.ndarray:
    """Convert position deltas from TRS to ENU"""
    lat, lon, _ = trs.ref_pos.llh.val.T
    trs2enu = rotation.trs2enu(lat, lon)

    return (trs2enu @ trs.mat)[:, :, 0]


def delta_enu2trs(enu: "EnuPositionDelta") -> np.ndarray:
    """Convert position deltas from ENU to TRS"""
    lat, lon, _ = enu.ref_pos.llh.val.T
    enu2trs = rotation.enu2trs(lat, lon)

    return (enu2trs @ enu.mat)[:, :, 0]


@register_system(convert_to=dict(enu=delta_trs2enu))
class TrsPositionDelta(PositionDeltaArray):

    system = "trs"
    column_names = ("x", "y", "z")


@register_system(convert_to=dict(trs=delta_enu2trs))
class EnuPositionDelta(PositionDeltaArray):

    system = "enu"
    column_names = ("east", "north", "up")
