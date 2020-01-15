"""Midgard library module for handling of SI-unit conversions

Description:
------------

This module provides unit conversion constants and functions. The heavy lifting is done by the `pint` package. The
basic usage is as follows:

    >>> from midgard.math.unit import Unit
    >>> seconds_in_two_weeks = 2 * Unit.week2secs
    >>> seconds_in_two_weeks
    1209600.0

In general `Unit.spam2ham` will give the multiplicative conversion scale between the units `spam` and `ham`. Through
the `pint` package we support a lot of units. See `Unit.list()` or
`https://github.com/hgrecco/pint/blob/master/pint/default_en.txt`. Another notation is also available, and might be
necessary for some more complicated conversions:

    >>> seconds_in_two_weeks = 2 * Unit('week', 'seconds')
    >>> miles_per_hour_in_meters_per_second = Unit('mph', 'meters / sec')

Do note that we support most normal aliases as well as singular and plural forms of the units. For instance can
`second` be represented as `s`, `sec`, `secs` and `seconds`. Prefixes are also handled:

    >>> nanoseconds_in_an_hour = Unit.hour2nanosecs
    >>> inches_in_a_kilometer = Unit.km2inches

For more complicated conversions (for instance from Celsius to Fahrenheit) one can create custom conversion functions
using `convert`:

    >>> c2f = Unit.function('celsius', 'fahrenheit')
    >>> absolute_zero_in_fahrenheit = c2f(-273.15)

For convenience, this can also be written using the attribute notation as `Unit.spam_to_ham(spam_value)`. Then the
previous example simply becomes:

    >>> absolute_zero_in_fahrenheit = Unit.celsius_to_fahrenheit(-273.15)

(or even easier `Unit.kelvin_to_fahrenheit(0)`).

Finally, we can access the unit/quantity system of `pint` by using the name of a unit by itself, e.g. `Unit.spam`. For
instance:

    >>> distance = 42 * Unit.km
    >>> time = 31 * Unit('minutes')
    >>> speed = distance / time
    >>> speed.to(Unit.mph)
    <Quantity(50.511464659292955, 'mph')>

    >>> speed.to_base_units()
    <Quantity(22.580645161290324, 'meter / second')>

However, using the full unit system adds some overhead so we should be careful in using it in heavy calculations.

Note that `pint` has a system for defining new units and constants if necessary,
`http://pint.readthedocs.io/en/latest/defining.html`. To use this system, add units to the `unit.txt` file in the
current (midgard/math) directory.
"""

# Standard library imports
import pathlib
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

try:
    import importlib.resources as importlib_resources  # Python >= 3.7
except ImportError:
    import importlib_resources  # Python <= 3.6:  pip install importlib_resources


# Third party imports
import numpy as np
import pint

# Midgard imports
from midgard.dev import exceptions

# Type that can be either float or numpy array
np_float = TypeVar("np_float", float, np.array)

# The _UNITS-dict is used to keep track of units values returned by functions and methods
_UNITS: Dict[str, Dict[str, str]] = dict()


class _convert_units(type):
    """A meta-class that does the parsing of units

    The meta-class is used for convenience. It allows us to use the `Unit`-class without instantiating it. That is, we
    can write `Unit.km2m` instead of `Unit().km2m`.
    """

    _ureg = pint.UnitRegistry()

    def __call__(cls, from_unit: str, to_unit: Optional[str] = None) -> Any:  # type: ignore
        """Calculate the conversion scale between from_unit and to_unit

        If `to_unit` is not given, then `from_unit` is returned as a `pint` Quantity.

        Args:
            from_unit:  The unit to convert from.
            to_unit:    The unit to convert to.

        Returns:
            Scale to multiply by to convert from from_unit to to_unit, or from_unit as a Quantity.
        """
        try:
            if to_unit is None:
                return cls._ureg(from_unit)
            else:
                return cls._ureg(from_unit).to(to_unit).magnitude
        except pint.errors.DimensionalityError as err:
            raise exceptions.UnitError(err)

    def __getattr__(cls, key: str) -> Any:
        """Simplify notation for converting between units

        This makes it possible to type `Unit.km2m` instead of `Unit('km', 'm')`. We split on the character `2`
        (pronounced "to"), and pass the result on to `__call__` to do the conversion. If a `2` is not found, we
        check if we can split on '_to_' instead, if so it is interpreted as a conversion function and is handed of to
        `convert`. Finally, if no split is done, the attribute is interpreted as a simple unit.

        Note that if you need a unit whose name contains a '2' (or '_to_') you need to use the notation
        `Unit('foot_H2O', 'pascal'). Similarly, more complex units need the same notation, e.g. `Unit('meters per
        second ** 2')`.

        Args:
            key:   The key (name) of the attribute to the class. Interpreted as units.

        Returns:
            Scale to multiply by or function to perform the unit conversion, or Quantity.
        """
        if "2" in key:
            from_unit, _, to_unit = key.partition("2")
            return cls(from_unit, to_unit)
        elif "_to_" in key:
            from_unit, _, to_unit = key.partition("_to_")
            return cls.function(from_unit, to_unit)
        else:
            return cls(key)

    def load_definitions(cls, file_path: Union[str, pathlib.Path]) -> None:
        """Load customized units and constants

        Piggybacking on `pint`'s system for defining new units and constants,
        `http://pint.readthedocs.io/en/latest/defining.html`.

        Args:
            file_path:  File containing definitions of units and constants.
        """
        with open(file_path, mode="rt") as fid:
            cls._ureg.load_definitions(fid)

    def function(cls, from_unit: str, to_unit: str) -> Callable[[float], float]:
        """Create a conversion function

        This is necessary for unit conversions that are not simple multiplications. The usual example is temperature
        conversions for instance from Celsius to Fahrenheit.

        Args:
            from_unit:  The unit to convert from.
            to_unit:    The unit to convert to.

        Returns:
            Conversion function that converts from from_unit to to_unit.
        """
        return lambda value: cls._ureg.Quantity(value, cls._ureg(from_unit)).to(cls._ureg(to_unit)).magnitude

    def register(cls, unit: Tuple, module=None) -> Callable:
        """Register unit of a function/method/property

        This method should be used as a decorator on the function/method/property, and specify the unit of the value
        returned by that function/method/property. For instance

            @property
            @Unit.register(('meter',))
            def calculate_delay(...):
                return delay_in_meters

        Units registered with this decorator can be used by the functions returned by the `unit_func_factory`,
        `convert_func_factory` and `factor_func_factory`.

        Args:
            unit:  Name of unit.

        Returns:
            Decorator that registers the unit.
        """

        def register_decorator(func: Callable) -> Callable:
            """Register unit of func in _UNITS-dictionary"""
            module_name = module.__name__ if module else func.__module__
            func_name = func.__name__
            _UNITS.setdefault(module_name, dict())[func_name] = unit

            return func

        return register_decorator

    @staticmethod
    def _get_unit(module_name: str, func_name: str) -> str:
        """Get registered unit of function/method/property

        Outside code should use the `unit_factory` to get registered units.

        Args:
            module_name:   Name of module containing function/method/property.
            func_name:     Name of function/method/property with registered unit.

        Returns:
            Name of unit.
        """
        units = _UNITS.get(module_name, dict())
        try:
            return units[func_name]
        except KeyError:
            raise exceptions.UnitError(f"No unit is registered for {func_name!r} in {module_name!r}") from None

    def unit_factory(cls, module_name: str) -> Callable[[str], str]:
        """Provide a function that can get registered units of functions/methods/properties

        The function checks for units registered with the unit.register-decorator. It can for instance be added to a
        class as follows:

            unit = staticmethod(Unit.unit_factory(__name__))

        Args:
            module_name:   Name of module as returned by `__name__`.

        Returns:
            Function that gets unit of values returned by functions.
        """

        def unit(func_name: str) -> str:
            """Unit of value returned by function/method/property

            Args:
                func_name (String):  Name of function/method/property.

            Returns:
                String:  Name of unit.
            """
            return cls._get_unit(module_name, func_name)

        return unit

    def convert_factory(cls, module_name: str) -> Callable[[object, str, str], float]:
        """Provide a function that can convert values of properties to a given unit

        The function checks for units registered with the unit.register-decorator. It can for instance be added to a
        class as follows:

            convert_to = Unit.convert_factory(__name__)

        Note that unlike the other factories, this one only works for properties.

        Args:
            module_name:   Name of module as returned by `__name__`.

        Returns:
            Function that converts values of properties.
        """

        def convert(self: object, property_name: str, to_unit: str) -> float:
            """Convert value of property to another unit

            Args:
                property_name:  Name of property.
                to_unit:        Name of other unit.

            Returns:
                Value of property converted to other unit.
            """
            from_unit = cls._get_unit(module_name, property_name)
            factor = cls(from_unit, to_unit)
            return getattr(self, property_name) * factor

        return convert

    def factor_factory(cls, module_name: str) -> Callable[[str, str], float]:
        """Provide a function that calculates conversion factor to another unit

        The function finds conversion factors for units registered with the unit.register-decorator. It can for
        instance be added to a class as follows:

            unit_factor = staticmethod(Unit.factor_factory(__name__))

        Args:
            module_name:   Name of module as returned by `__name__`.

        Returns:
            Function that calculates conversion factor to another unit.
        """

        def factor(func_name: str, to_unit: str) -> float:
            """Conversion factor between unit of function/method/property and another unit

            Args:
                func_name:  Name of function/method/property.
                to_unit:    Name of other unit.

            Returns:
                Conversion factor.
            """
            from_unit = cls._get_unit(module_name, func_name)
            return cls(from_unit, to_unit)

        return factor

    def units_dict(cls, module_name: str) -> Dict[str, str]:
        """Dictionary of units registered on a module

        Add a sub-dictionary if the module name is unknown, to set up a reference in case units are registered later.

        Args:
            module_name:  Name of module.

        Returns:
            Dictionary with units registered on a module.
        """
        return _UNITS.setdefault(module_name, dict())

    @property
    def names(cls) -> List[str]:
        """List available units and constants

        The list of available units contains aliases (for instance s, sec, second), but not plural forms (secs,
        seconds) or possible prefixes (milliseconds, usec, ms).

        Returns:
            List of names of available units and constants
        """
        return dir(cls._ureg)


class Unit(metaclass=_convert_units):
    """Unit converter

    The implementation of the unit conversion is done in the `_convert_units`-metaclass.
    """

    # Make pint exceptions available
    from pint.errors import DimensionalityError

    #
    # Conversion routines not defined by pint
    #
    @classmethod
    def rad_to_dms(cls, radians: np_float) -> Tuple[np_float, np_float, np_float]:
        """Converts radians to degrees, minutes and seconds

        Args:
            radians:  Angle(s) in radians

        Returns:
            Tuple with degrees, minutes, and seconds.

        Examples:

            >>> Unit.rad_to_dms(1.04570587646256)
            (59.0, 54.0, 52.3200000000179)
            >>> Unit.rad_to_dms(-0.2196050301753194)
            (-12.0, 34.0, 56.78900000000468)
            >>> Unit.rad_to_dms(-0.005817642339636369)
            (-0.0, 19.0, 59.974869999999925)
        """
        sign = np.sign(radians)
        degrees = abs(radians) * cls.radians2degrees
        minutes = (degrees % 1) * cls.hour2minutes
        seconds = (minutes % 1) * cls.minute2seconds

        return sign * np.floor(degrees), np.floor(minutes), seconds

    @classmethod
    def dms_to_rad(cls, degrees: np_float, minutes: np_float, seconds: np_float) -> np_float:
        """Convert degrees, minutes and seconds to radians

        The sign of degrees will be used. In this case, be careful that the sign
        of +0 or -0 is correctly passed on. That is, degrees must be specified as a float, not an
        int.

        Args:
            degrees:   Degrees as float (including sign) or array of floats
            minutes:   Minutes as int/float or array of ints/floats
            seconds:   Seconds as float or array of floats

        Returns:
            Given degrees, minutes and seconds as radians.

        Examples:

            >>> Unit.dms_to_rad(59, 54, 52.32)
            1.04570587646256
            >>> Unit.dms_to_rad(-12.0, 34, 56.789)
            -0.21960503017531938
            >>> Unit.dms_to_rad(-0.0, 19, 59.974870)
            -0.005817642339636369
        """
        sign = np.copysign(1, degrees)
        return (
            sign * (np.abs(degrees) + minutes * cls.minutes2hours + seconds * cls.seconds2hours) * cls.degrees2radians
        )

    @classmethod
    def hms_to_rad(cls, hours: np_float, minutes: np_float, seconds: np_float) -> np_float:
        """Convert hours, minutes and seconds to radians

        Args:
            hours:     Hours as int or array of ints
            minutes:   Minutes as int or or array of ints
            seconds:   Seconds as float or or array of floats

        Returns:
            Given hours, minutes and seconds as radians.

        Examples:

            >>> Unit.hms_to_rad(17, 7, 17.753427)
            4.482423920139868
            >>> Unit.hms_to_rad(12, 0, 0.00)
            3.1415926535897936
            >>> Unit.hms_to_rad(-12, 34, 56.789)
            Traceback (most recent call last):
            ValueError: hours must be non-negative
        """
        if np.any(np.array(hours) < 0):
            raise ValueError("hours must be non-negative")

        return 15 * cls.dms_to_rad(hours, minutes, seconds)

    @classmethod
    def symbol(cls, unit: str):
        if unit == "unitless" or unit == "dimensionless":
            return ""
        try:
            unit = str(cls(unit).u)
        except pint.errors.UndefinedUnitError:
            return unit
        try:
            return cls._ureg._units[unit].symbol
        except KeyError:
            for u in cls._ureg._units.keys():
                if u != cls._ureg._units[u].symbol:
                    unit = unit.replace(u, cls._ureg._units[u].symbol).replace(" ", "")
            return unit


# Read extra units defined specially for Midgard
with importlib_resources.open_text("midgard.math", "unit.txt") as fid:
    Unit._ureg.load_definitions(fid)
