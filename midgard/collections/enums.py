"""Framework for working with enumerations

Description:
------------

Custom enumerations used for structured names. You can add your own enumerations in your own application by importing
`register_enum` and using that to register your own enums.


Example:
--------

Create your own enumeration:

    from midgard.collections.enums import register_enum

    @register_enum("reference_ellipsoid")
    class ReferenceEllipsoid(enum.IntEnum):

        wgs84 = 1
        grs80 = 2
        wgs72 = 3


Use enumerations in your code:

    from midgard.collections import enums
    enums.get_value("gnss_freq_G", "L1")
    enums.get_value("gnss_freq_G", "L1") + 1

    enums.get_enum("gnss_freq_G")
    enums.get_enum("gnss_freq_G").L1
    enums.get_enum("gnss_freq_G").L1 + 1

    enums.gnss_freq_G.L1
    enums.gnss_freq_G.L1 * 2
"""

# Standard library imports
import enum
from typing import Any, Callable, Dict, List

# Midgard imports
from midgard.dev.console import color
from midgard.dev import exceptions


# Dictionary of Enumerations. Populated by the @register_enum-decorators.
_ENUMS: Dict[str, enum.EnumMeta] = dict()


class NotGiven:
    """Dummy class used as a marker for a argument not given, used instead of None because None is valid value"""

    pass


def register_enum(name: str) -> Callable[[enum.EnumMeta], enum.EnumMeta]:
    """Register a named Enumeration

    This allows for getting Enumerations with the get_enum-function.

    Args:
        name:  Name used for Enumeration.

    Returns:
        Decorator that registers an Enumeration.
    """

    def register_decorator(enum_cls: enum.EnumMeta) -> enum.EnumMeta:
        _ENUMS[name] = enum_cls
        globals()[name] = enum_cls
        return enum_cls

    return register_decorator


def enums() -> List[str]:
    """Return a list of available enums

    Returns:
        Names of available enums.
    """
    return sorted(_ENUMS)


def get_enum(name: str) -> enum.EnumMeta:
    """Return a named Enumeration

    Names are defined by the @register_enum-decorator. If the name-parameter is not a valid enum, the function will
    raise an UnknownEnumError and list the available enumerations.

    Args:
        name:  Name used for Enumeration.

    Returns:
        Enumeration with the given name.
    """
    try:
        return _ENUMS[name]
    except KeyError:
        valid_enums = ", ".join(e for e in _ENUMS)
        raise exceptions.UnknownEnumError(
            f"Enumeration '{name}' is not defined. Available enumerations are {valid_enums}."
        ) from None


def get_value(name: str, value: str, default: Any = NotGiven) -> enum.Enum:
    """Return the value of a named Enumeration

    Names are defined by the @register_enum-decorator.

    Args:
        name:     Name used for Enumeration.
        value:    Value of Enumeration.
        default:  Optional object returned if enumeration does not contain value

    Returns:
        Value of enumeration with the given name.
    """
    try:
        return get_enum(name)[value]
    except KeyError:
        if default is NotGiven:
            valid_values = ", ".join(v.name for v in get_enum(name))  # type: ignore
            raise ValueError(
                f"Value '{value}' is not valid for a {name}-enumeration. Valid values are {valid_values}."
            ) from None
        else:
            return default


def has_value(name: str, value: str) -> bool:
    """Check whether a named Enumeration defines a given value

    Args:
        name:     Name used for Enumeration.
        value:    Value of Enumeration.

    Returns:
        True if Enumeration defines value, False otherwise
    """
    return value in get_enum(name).__members__


#
# ENUMS
#
@register_enum("log_level")
class LogLevel(int, enum.Enum):
    """Levels used when deciding how much log output to show"""

    all = enum.auto()
    debug = enum.auto()
    info = enum.auto()
    warn = enum.auto()
    error = enum.auto()
    fatal = enum.auto()
    none = enum.auto()


@register_enum("log_color")
class LogColor(str, enum.Enum):
    """Colors used when logging"""

    warn = color.Fore.YELLOW
    error = color.Fore.RED
    fatal = color.Style.BRIGHT + color.Fore.RED


@register_enum("write_level")
class WriteLevel(enum.IntEnum):
    """Levels used when deciding which fields of a dataset and other information to write to disk"""

    detail = enum.auto()
    analysis = enum.auto()
    operational = enum.auto()


@register_enum("gnss_freq_G")
class GPSFrequency(float, enum.Enum):
    """GPS frequencies"""

    L1 = 1575.42e+6
    L2 = 1227.60e+6
    L5 = 1176.45e+6


# Examples

# from midgard.collections import enums
# enums.get_value("gnss_freq_G", "L1")
# enums.get_value("gnss_freq_G", "L1") + 1

# enums.get_enum("gnss_freq_G")
# enums.get_enum("gnss_freq_G").L1
# enums.get_enum("gnss_freq_G").L1 + 1

# enums.gnss_freq_G.L1
# enums.gnss_freq_G.L1 * 2
