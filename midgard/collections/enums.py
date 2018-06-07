"""Framework for working with enumerations

Description:
------------

Custom enumerations used for structured names.
"""

# Standard library imports
import enum
from typing import Callable, Dict, List

# Midgard imports
from midgard.dev import exceptions


# Dictionary of Enumerations. Populated by the @register_enum-decorators.
_ENUMS: Dict[str, enum.EnumMeta] = dict()


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


def get_value(name: str, value: str) -> enum.Enum:
    """Return the value of a named Enumeration

    Names are defined by the @register_enum-decorator.

    Args:
        name:   Name used for Enumeration.
        value:  Value of Enumeration.

    Returns:
        Value of enumeration with the given name.
    """
    try:
        return get_enum(name)[value]
    except KeyError:
        valid_values = ", ".join(v.name for v in get_enum(name))  # type: ignore
        raise ValueError(
            f"Value '{value}' is not valid for a {name}-enumeration. Valid values are {valid_values}."
        ) from None


#
# ENUMS
#
@register_enum("log_level")
class LogLevel(enum.IntEnum):
    """Levels used when deciding how much log output to show"""

    all = enum.auto()
    debug = enum.auto()
    time = enum.auto()
    dev = enum.auto()
    info = enum.auto()
    warn = enum.auto()
    check = enum.auto()
    error = enum.auto()
    fatal = enum.auto()
    none = enum.auto()
