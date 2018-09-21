"""Tests for the math.unit-module

"""
# System library imports

# Third party imports
import pytest

# Midgard imports
from midgard.dev import exceptions
from midgard.math.unit import Unit


#
# Test function
#
@Unit.register("meters per second")
def bolt():
    """100 meters in 9.58 seconds

    https://www.youtube.com/watch?v=3nbjhpcZ9_g
    """
    return 100 / 9.58


#
# Tests
#
def test_unit_as_attribute():
    """Test that we can get unit as an attribute"""
    meter = Unit.m
    assert meter.__class__.__name__ == "Quantity"  # Quantity class is not easily available in pint
    assert meter.magnitude == 1
    assert str(meter.units) == "meter"


def test_conversion_as_attribute():
    """Test that we can do unit conversion using attributes"""
    assert Unit.kilometer2meter == 1000


def test_convert_function_as_attribute():
    """Test that we can define conversion functions as attributes"""
    c2f = Unit.celsius_to_fahrenheit
    assert callable(c2f)
    assert c2f(0) == pytest.approx(32.0)
    assert c2f(100) == pytest.approx(212.0)


def test_registered_units_as_dict():
    """Test that we can access units registered on a function"""
    units = Unit.units_dict(__name__)
    assert "bolt" in units
    assert units["bolt"] == "meters per second"


def test_registered_units_as_function():
    """Test that we can access units registered on a function"""
    units = Unit.unit_factory(__name__)
    assert callable(units)
    assert units("bolt") == "meters per second"


def test_registered_units_as_factor():
    """Test that we can access conversion factor for registered units"""
    factor = Unit.factor_factory(__name__)
    assert callable(factor)
    assert factor("bolt", "miles per hour") == pytest.approx(3600 / 1609.344)


def test_nonregistered_units_raise_error():
    """Test that an error is raised when trying to get unit of function that is not registered"""
    units = Unit.unit_factory(__name__)
    with pytest.raises(exceptions.UnitError):
        units("not_registered")


def test_list_of_available_units():
    """Test that we can list available units"""
    unit_names = Unit.names
    assert len(unit_names) > 0
    assert "meter" in unit_names
    assert "second" in unit_names
    assert "radian" in unit_names
