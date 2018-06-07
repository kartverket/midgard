"""Tests for the math.interpolation-module

"""
# System library imports
from collections import namedtuple

# Third party imports
import pytest
import numpy as np

# Midgard imports
from midgard.dev import exceptions
from midgard.math import interpolation


# Simple datastructure for test sets
IPSet = namedtuple("IPSet", ("x", "y", "x_new"))

# Arguments to individual interpolators
IPARGS = dict(lagrange={"window": 5}, interpolated_univariate_spline={"ext": "raise"})


#
# Test data sets
#
@pytest.fixture
def ipset():
    """A basic test set of interpolation data, should not cause problems"""
    return IPSet(x=np.linspace(0, 10, 11), y=np.random.randn(11), x_new=np.linspace(3, 9, 20))


@pytest.fixture
def ipset_same_x():
    """A test set with x_new being equal to x"""
    return IPSet(x=np.linspace(0, 10, 11), y=np.linspace(-1, 1, 11), x_new=np.linspace(0, 10, 11))


@pytest.fixture
def ipset_one_x_new():
    """A test set with only one value for x_new"""
    x = np.linspace(-3, 3, 11)
    return IPSet(x=x, y=x ** 2, x_new=1)


@pytest.fixture
def ipset_linear():
    """A test set with linear y values"""
    return IPSet(x=np.linspace(0, 10, 11), y=np.linspace(-1, 1, 11), x_new=np.linspace(2, 8, 51))


@pytest.fixture
def ipset_x_2d():
    """A test set with 2-dimensional x values"""
    x1 = np.linspace(0, 10, 11)
    x2 = np.linspace(-3, 3, 11)
    return IPSet(x=np.stack((x1, x2), axis=1), y=np.linspace(-1, 1, 11), x_new=np.stack((x1[1:-1], x2[1:-1]), axis=1))


@pytest.fixture
def ipset_y_0d():
    """A test set with 0-dimensional y values"""
    return IPSet(x=np.linspace(0, 10, 1), y=np.array(1), x_new=np.linspace(2, 5, 7))


@pytest.fixture
def ipset_y_2d():
    """A test set with 2-dimensional y values"""
    return IPSet(x=np.linspace(0, 10, 11), y=np.random.randn(11, 4), x_new=np.linspace(1, 4, 3))


@pytest.fixture
def ipset_y_3d():
    """A test set with 3-dimensional y values"""
    return IPSet(x=np.linspace(0, 10, 11), y=np.random.randn(11, 2, 5), x_new=np.linspace(1, 4, 3))


@pytest.fixture
def ipset_below():
    """A test set with x_new values outside (below) the orginal x values"""
    return IPSet(x=np.linspace(0, 10, 11), y=np.linspace(-1, 1, 11), x_new=np.linspace(-2, 2, 5))


@pytest.fixture
def ipset_above():
    """A test set with x_new values outside (above) the orginal x values"""
    return IPSet(x=np.linspace(0, 10, 11), y=np.linspace(-1, 1, 11), x_new=np.linspace(8, 12, 5))


@pytest.fixture
def ipset_num_x_y_different():
    """A test set with different number of x and y values"""
    return IPSet(x=np.linspace(0, 10, 11), y=np.linspace(-1, 1, 3), x_new=np.linspace(2, 5, 4))


@pytest.fixture
def ipset_x_repeating():
    """A test set with a repeating x value"""
    x = np.linspace(0, 10, 11)
    x[5] = x[4]
    return IPSet(x=x, y=np.linspace(-1, 1, 11), x_new=np.linspace(2, 5, 7))


#
# Tests
#
def test_list_of_interpolators_not_empty():
    """Test that list_all() finds some plugins in midgard.readers-package"""
    interpolators = interpolation.interpolators()
    assert len(interpolators) > 0


def test_interpolator_non_existing():
    """Test that a non-existent interpolator raises an appropriate error"""
    with pytest.raises(exceptions.UnknownPluginError):
        interpolation.get_interpolator("non_existent")


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_interpolator_is_callable(name):
    """Test that an existing interpolator returns a function"""
    interpolator = interpolation.get_interpolator(name)
    assert callable(interpolator)


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_interpolating_to_same_x(name, ipset_same_x):
    """Test that using x_new == x returns y_new == y"""
    y_new = interpolation.interpolate(*ipset_same_x, kind=name, **IPARGS.get(name, {}))
    assert np.allclose(y_new, ipset_same_x.y)


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_interpolating_one_value(name, ipset_one_x_new):
    """Test that interpolating one value returns a scalar array"""
    if name in ("lagrange",):
        pytest.skip(f"Method {name} does not handle scalar data")

    y_new = interpolation.interpolate(*ipset_one_x_new, kind=name, **IPARGS.get(name, {}))
    assert y_new.ndim == 0


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_dot_constant_for_linear_values(name, ipset_linear):
    """Test that the derivative is constant for linear values"""
    _, y_dot = interpolation.interpolate_with_derivative(*ipset_linear, kind=name, **IPARGS.get(name, {}))
    assert np.allclose(y_dot, y_dot.mean())


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_interpolating_x_2d(name, ipset_x_2d):
    """Test that 2-dimensional x values raises an error"""
    with pytest.raises(ValueError):
        interpolation.interpolate(*ipset_x_2d, kind=name, **IPARGS.get(name, {}))


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_interpolating_y_0d(name, ipset_y_0d):
    """Test that 0-dimensional interpolation raises an error"""
    with pytest.raises(ValueError):
        interpolation.interpolate(*ipset_y_0d, kind=name, **IPARGS.get(name, {}))


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_interpolating_y_2d(name, ipset_y_2d):
    """Test that 2-dimensional interpolation returns 2-dimensional data"""
    y_new = interpolation.interpolate(*ipset_y_2d, kind=name, **IPARGS.get(name, {}))
    assert y_new.ndim == 2


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_interpolating_y_3d(name, ipset_y_3d):
    """Test that 3-dimensional interpolation returns 3-dimensional data"""
    if name in ("lagrange",):
        pytest.skip(f"Method {name} does not support 3-dimensional data")

    y_new = interpolation.interpolate(*ipset_y_3d, kind=name, **IPARGS.get(name, {}))
    assert y_new.ndim == 3


@pytest.mark.parametrize("name", set(interpolation.interpolators()) - {"barycentric_interpolator"})
def test_extrapolating_below_raise(name, ipset_below):
    """Test that extrapolation raises an error"""
    with pytest.raises(ValueError):
        interpolation.interpolate(*ipset_below, kind=name, **IPARGS.get(name, {}))


@pytest.mark.parametrize(
    "name", set(interpolation.interpolators()) - {"barycentric_interpolator", "interpolated_univariate_spline"}
)
def test_extrapolating_below_ok(name, ipset_below):
    """Test that extrapolation does not raise an error when bounds_error==False"""
    y_new = interpolation.interpolate(*ipset_below, kind=name, bounds_error=False, **IPARGS.get(name, {}))
    assert len(y_new) == len(ipset_below.x_new)


@pytest.mark.parametrize("name", set(interpolation.interpolators()) - {"barycentric_interpolator"})
def test_extrapolating_above_raise(name, ipset_above):
    """Test that extrapolation raises an error"""
    with pytest.raises(ValueError):
        interpolation.interpolate(*ipset_above, kind=name, **IPARGS.get(name, {}))


@pytest.mark.parametrize(
    "name", set(interpolation.interpolators()) - {"barycentric_interpolator", "interpolated_univariate_spline"}
)
def test_extrapolating_above_ok(name, ipset_above):
    """Test that extrapolation does not raise an error when bounds_error==False"""
    y_new = interpolation.interpolate(*ipset_above, kind=name, bounds_error=False, **IPARGS.get(name, {}))
    assert len(y_new) == len(ipset_above.x_new)


@pytest.mark.parametrize("name", interpolation.interpolators())
def test_num_x_y_different(name, ipset_num_x_y_different):
    """Test that inconsistent number of x and y values raises an error"""
    if name in ("interpolated_univariate_spline",):
        pytest.skip(f"Method {name} does not support detecting inconsistent number of x and y values")

    with pytest.raises(ValueError):
        interpolation.interpolate(*ipset_num_x_y_different, kind=name, **IPARGS.get(name, {}))


@pytest.mark.parametrize("name", set(interpolation.interpolators()) - {"linear", "barycentric_interpolator"})
def test_x_repeating(name, ipset_x_repeating):
    """Test that repeating values of x raises an error"""
    with pytest.raises(ValueError):
        interpolation.interpolate(*ipset_x_repeating, kind=name, **IPARGS.get(name, {}))


def test_lagrange_window_too_big(ipset):
    """Test that a window bigger than number of x raises an error"""
    window = len(ipset.x) + 1
    with pytest.raises(ValueError):
        interpolation.interpolate(*ipset, kind="lagrange", window=window)


def test_lagrange_window_too_small(ipset):
    """Test that a window smaller than 3 raises an error"""
    window = 2
    with pytest.raises(ValueError):
        interpolation.interpolate(*ipset, kind="lagrange", window=window)
