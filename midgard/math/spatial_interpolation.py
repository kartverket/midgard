"""Methods for spatial interpolating (2D-interpolation) in numpy arrays

Description:
------------

Different interpolation methods are decorated with `@register_interpolator` and will then become available for use as
`kind` in `interpolate` function.


Example:
--------

import numpy as np
from midgard.math import spatial_interpolation

# Generate grid input data
x = np.arange(-5.01, 5.01, 0.25)
y = np.arange(-5.01, 5.01, 0.25)
grid_x, grid_y = np.meshgrid(x, y)
values = np.sin(xx**2+yy**2)

# Define data points for interplation
xnew = np.arange(-5.01, 5.01, 1e-2)
ynew = np.arange(-5.01, 5.01, 1e-2)

# Interpolate for given data points
values_new = spatial_interpolation.interpolate(grid_x, grid_y, values, xnew, ynew, kind="griddata")



Developer info:
---------------

To add your own interpolators, you can simply decorate your interpolator functions with `@register_interpolator`. Your
interpolator function should have the signature

    (   grid_x: np.ndarray, 
        grid_y: np.ndarray, 
        values: np.ndarray, 
        x: Union[float, np.ndarray],
        y: Union[float, np.ndarray],
    ) -> np.ndarray

"""
# Standard library imports
from typing import Any, Callable, Dict, List, Union

# Third party imports
import numpy as np
import scipy.interpolate 

# Midgard imports
from midgard.dev import exceptions


# Dictionary of Enumerations. Populated by the @register_enum-decorators.
_INTERPOLATORS: Dict[str, Callable] = dict()


def register_interpolator(func: Callable) -> Callable:
    """Register an interpolation function

    This function should be used as a @register_interpolator-decorator

    Args:
        func: Function that will be registered as an interpolator.

    Returns:
        Same function.
    """
    name = func.__name__
    _INTERPOLATORS[name] = func
    return func


def interpolators() -> List[str]:
    """Return a list of available interpolators

    Returns:
        Names of available interpolators.
    """
    return sorted(_INTERPOLATORS)


def interpolate(
        grid_x: np.ndarray, 
        grid_y: np.ndarray, 
        values: np.ndarray, 
        x: Union[float, np.ndarray],
        y: Union[float, np.ndarray],
        kind: str, 
        **kwargs: Any,
) -> np.ndarray:
    """Interpolate values from one x-array to another

    See `interpolators()` for a list of valid interpolators.

    Args:
        grid_x: (n,m) Array with x-positions for each grid point 
        grid_y: (n,m) Array with y-positions for each grid point 
        values: (n,m) Array with data values for each grid point
        x:            x-position
        y:            y-position
        kind:         Name of interpolator to use.
        kwargs:       Keyword arguments passed on to the interp1d-interpolator.

    Returns:
        Array of interpolated y-values.
    """
    interpolator = _get_interpolator(kind)(grid_x, grid_y, values, x, y, **kwargs)
    return interpolator


#
# INTERPOLATORS
# 
@register_interpolator
def griddata(
        grid_x: np.ndarray, 
        grid_y: np.ndarray, 
        values: np.ndarray, 
        x: Union[float, np.ndarray],
        y: Union[float, np.ndarray],
        **kwargs: Any,
) -> np.ndarray:
    """Griddata interpolation through the given points

    Interpolation is based on scipy.interpolate.griddata module.
    
    The 'method' argument can e.g. be chosen as additional griddata keyword argument 'kwargs'. Following interpolation
    methods can be chosen via the 'method' argument:
                    linear:  tessellate the input point set to N-D simplices, and interpolate linearly on each simplex
                    nearest: value of data point closest to the point of interpolation
                    cubic:   value determined from a piecewise cubic 
    
    Args:
        grid_x: (n,m) Array with x-positions for each grid point 
        grid_y: (n,m) Array with y-positions for each grid point 
        values: (n,m) Array with data values for each grid point
        x:            x-position
        y:            y-position
        kwargs:       Keyword arguments passed on to the griddata-interpolator.

    Returns:
        Interpolated value in data grid for a given position
    """
    method = kwargs["method"] if "method" in kwargs.keys() else "linear"
    
    grid_points = np.array([grid_x.flatten(), grid_y.flatten()]).T
    
    return scipy.interpolate.griddata(grid_points, values.flatten(), (x, y), method=method)
    
    
@register_interpolator
def rect_bivariate_spline(
        grid_x: np.ndarray, 
        grid_y: np.ndarray, 
        values: np.ndarray, 
        x: Union[float, np.ndarray],
        y: Union[float, np.ndarray], 
        **kwargs: Any,
) -> np.ndarray:
    """RectBivariateSpline interpolation through the given points

    Interpolation is based on scipy.interpolate.RectBivariateSpline module.
    
    Args:
        grid_x: (n,m) Array with x-positions for each grid point 
        grid_y: (n,m) Array with y-positions for each grid point 
        values: (n,m) Array with data values for each grid point
        x:            x-position
        y:            y-position
        kwargs:       Keyword arguments passed on to the RectBivariateSpline-interpolator.

    Returns:
        Interpolated value in data grid for a given position
    """
    # Note: The data point coordinates need to be sorted by increasing order. Therefore the y- (grid_y) and z-values
    #       (values) has to be rearranged.
    interp = scipy.interpolate.RectBivariateSpline(np.flip(grid_y[:,0]), grid_x[0], np.flipud(values))
    
    return interp.ev(np.array(y),np.array(x))
    
    
@register_interpolator
def regular_grid_interpolator(
        grid_x: np.ndarray, 
        grid_y: np.ndarray, 
        values: np.ndarray, 
        x: Union[float, np.ndarray],
        y: Union[float, np.ndarray], 
        **kwargs: Any,
) -> np.ndarray:
    """RegularGridInterpolator interpolation through the given points

    Interpolation is based on scipy.interpolate.RegularGridInterpolator module.
    
    Args:
        grid_x: (n,m) Array with x-positions for each grid point 
        grid_y: (n,m) Array with y-positions for each grid point 
        values: (n,m) Array with data values for each grid point
        x:            x-position
        y:            y-position
        kwargs:       Keyword arguments passed on to the RegularGridInterpolator-interpolator.

    Returns:
        Interpolated value in data grid for a given position
    """
    interp = scipy.interpolate.RegularGridInterpolator((np.flip(grid_y[:,0]), grid_x[0]), np.flipud(values))
    if type(x) == float or type(x) == np.float64:
        x = np.array([x])
        y = np.array([y])
    points = list(map(lambda coord: list(coord), zip(y,x)))

    return interp(points)
    
       
#
# AUXILIARY FUNCTIONS
#    
def _get_interpolator(name: str) -> Callable:
    """Return an interpolation function

    Interpolation functions are registered by the @register_interpolator-decorator. The name-parameter corresponds to
    the function name of the interpolator.

    Args:
        name:  Name of interpolator.

    Returns:
        Interpolation function with the given name.
    """
    try:
        return _INTERPOLATORS[name]
    except KeyError:
        interpolator_list = ", ".join(interpolators())
        raise exceptions.UnknownPluginError(
            f"Interpolator '{name}' is not defined. Available interpolators are {interpolator_list}."
        ) from None
    




