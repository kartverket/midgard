"""Framework for working with enumerations

Description:
------------

Custom enumerations used for structured names.

"""

# Midgard imports
from midgard.dev import exceptions


# Dictionary of Enumerations. Populated by the @register_enum-decorators.
_ENUMS = dict()


def get_enum(name=None):
    """Return a named Enumeration

    Names are defined by the @register_enum-decorator. If the name-parameter is not given, the function will raise an
    UnknownEnumError and list the available enumerations.

    Args:
        name (String):  Name used for Enumeration.

    Returns:
        Enum: Enumeration with the given name.
    """
    try:
        return _ENUMS[name]
    except KeyError:
        valid_enums = ', '.join(e for e in _ENUMS)
        raise exceptions.UnknownEnumError(f"Enumeration '{name}' is not defined. "
                                          f'Available enumerations are {valid_enums}.') from None


def get_value(name, value):
    """Return the value of a named Enumeration

    Names are defined by the @register_enum-decorator.

    Args:
        name (String):   Name used for Enumeration.
        value (String):  Value of Enumeration.

    Returns:
        Enum: Value of enumeration with the given name.
    """
    try:
        return get_enum(name)[value]
    except KeyError:
        valid_values = ', '.join(v.name for v in get_enum(name))
        raise ValueError(f"Value '{value}' is not valid for a {name}-enumeration. "
                         f'Valid values are {valid_values}.') from None


def register_enum(name):
    """Register a named Enumeration

    This allows for getting Enumerations with the get_enum-function.

    Args:
        name (String):  Name used for Enumeration.

    Returns:
        Decorator: Decorator that registers an Enumeration.
    """
    def register_decorator(func):
        _ENUMS[name] = func
        return func

    return register_decorator
