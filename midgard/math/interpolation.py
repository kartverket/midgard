"""Methods for interpolating in numpy arrays

Description:
------------

Different interpolation methods are decorated with `@register_interpolator` and will then become available for use as
`kind` in `interpolate` and `moving_window`.


Example:
--------

    >>> import numpy as np
    >>> np.set_printoptions(precision=3, suppress=True)
    >>> x = np.linspace(-1, 1, 11)
    >>> y = x**3 - x
    >>> y
    array([ 0.   ,  0.288,  0.384,  0.336,  0.192,  0.   , -0.192, -0.336,
           -0.384, -0.288,  0.   ])

    >>> x_new = np.linspace(-0.8, 0.8, 11)
    >>> interpolate(x, y, x_new, kind='cubic')
    array([ 0.288,  0.378,  0.369,  0.287,  0.156, -0.   , -0.156, -0.287,
           -0.369, -0.378, -0.288])


Developer info:
---------------

To add your own interpolators, you can simply decorate your interpolator functions with `@register_interpolator`. Your
interpolator function should have the signature

    (x: np.ndarray, y: np.ndarray) -> Callable

For instance, the following would implement a terrible interpolation function that sets all values to zero:

    from midgard.math.interpolation import register_interpolator

    @register_interpolator
    def zero(x: np.ndarray, y: np.ndarray) -> Callable:

        def _zero(x_new: np.ndarray) -> np.ndarray:
            return np.zeros(y.shape)

        return _zero

This function would then be available as an interpolator. For instance, one could do

    >>> interpolate(x, y, x_new, kind='zero')  # doctest: +SKIP
    array([0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.])

"""
# Standard library imports
from typing import Any, Callable, Dict, List

# Third party imports
import numpy as np
import scipy.interpolate
import scipy.misc

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


def get_interpolator(name: str) -> Callable:
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


def interpolate(x: np.ndarray, y: np.ndarray, x_new: np.ndarray, *, kind: str, **ipargs: Any) -> np.ndarray:
    """Interpolate values from one x-array to another

    See `interpolators()` for a list of valid interpolators.

    Args:
        x:       1-dimensional array with original x-values.
        y:       Array with original y-values.
        x_new:   1-dimensional array with new x-values.
        kind:    Name of interpolator to use.
        ipargs:  Keyword arguments passed on to the interpolator.

    Returns:
        Array of interpolated y-values.
    """
    interpolator = get_interpolator(kind)(x, y, **ipargs)
    return interpolator(x_new)


def interpolate_with_derivative(
    x: np.ndarray, y: np.ndarray, x_new: np.ndarray, *, kind: str, dx: float = 0.5, **ipargs: Any
) -> np.ndarray:
    """Interpolate values from one x-array to another as well as find derivatives

    See `interpolators()` for a list of valid interpolators.

    Args:
        x:      1-dimensional array with original x-values.
        y:      Array with original y-values.
        x_new:  1-dimensional array with new x-values.
        kind:   Name of interpolator to use.
        dx:     Values at x ± dx are used to determine derivative.
        ipargs:  Keyword arguments passed on to the interpolator.

    Returns:
        Tuple with array of interpolated y-values and array of derivatives.
    """
    interpolator = get_interpolator(kind)(x, y, **ipargs)
    y_new = interpolator(x_new)
    y_dot = scipy.misc.derivative(interpolator, x_new, dx=dx)

    return y_new, y_dot


@register_interpolator
def lagrange(
    x: np.ndarray, y: np.ndarray, *, window: int = 10, bounds_error: bool = True, assume_sorted: bool = False
) -> Callable:
    """Computes the lagrange polynomial passing through a certain set of points

    See https://en.wikipedia.org/wiki/Lagrange_polynomial

    Uses `window` of the original points to calculate the Lagrange polynomials. The window of points is chosen by
    finding the closest original point and essentially picking the `window // 2` indices on either side.

    Args:
        x:              1-dimensional array with original x-values.
        y:              Array with original y-values.
        window:         Number of points used in interpolation.
        bounds_error:   If True, a ValueError is raised if extrapolation is attempted.
        assume_sorted:  If True, x must be an array of monotonically increasing values.

    Returns:
        Lagrange interpolation function.
    """
    # Check input
    if x.ndim != 1:
        raise ValueError(f"The x array must have exactly one dimension, currently x.ndim={x.ndim}.")
    if y.ndim < 1:
        raise ValueError(f"The y array must have at least one dimension, currently y.ndim={y.ndim}.")
    if len(y) != len(x):
        raise ValueError("x and y arrays must be equal in length along the first axis.")
    if window < 3:
        raise ValueError("The window should be at least 3")
    if window > len(x):
        raise ValueError(f"x and y arrays must have at least window={window} entries")

    # Sort the input according to the x-array
    if not assume_sorted:
        sort_idxs = np.argsort(x)
        x, y = x[sort_idxs], y[sort_idxs]

    # Check that x values are monotonically increasing
    if not all(np.diff(x) > 0):
        raise ValueError("expected x to be a sorted array with unique values")

    # Rescale x values to avoid numerical instability
    _xm, _xs = x.mean(), x.std()
    x_scaled = (x - _xm) / _xs

    # Indices to use during calculation of polynomial values
    indices = np.eye(window) == 0

    def _lagrange(x_new: np.ndarray) -> np.ndarray:
        """Interpolate using a Lagrange polynomial"""
        if bounds_error and x_new.min() < x.min():
            raise ValueError(f"Value {x_new.min()} in x_new is below the interpolation range {x.min()}.")
        if bounds_error and x_new.max() > x.max():
            raise ValueError(f"Value {x_new.max()} in x_new is above the interpolation range {x.max()}.")

        y_new = np.zeros(x_new.shape[:1] + y.shape[1:])
        x_new_scaled = (x_new - _xm) / _xs

        # Figure out which points to use for the interpolation
        start_idxs = np.abs(x[:, None] - x_new[None, :]).argmin(axis=0) - window // 2
        start_idxs[start_idxs < 0] = 0
        start_idxs[start_idxs > len(x) - window] = len(x) - window

        # Interpolate for each unique set of interpolation points
        for idx in np.unique(start_idxs):
            y_idx = start_idxs == idx
            x_wd, y_wd = x_scaled[idx : idx + window], y[idx : idx + window]
            diff_x = np.subtract(*np.meshgrid(x_wd, x_wd)) + np.eye(window)

            r = np.array(
                [
                    np.prod((x_new_scaled[y_idx, None] - x_wd[idxs]) / diff_x[idxs, i], axis=1)
                    for i, idxs in enumerate(indices)
                ]
            )
            y_new[y_idx] = r.T @ y_wd
        return y_new

    return _lagrange


@register_interpolator
def linear(x: np.ndarray, y: np.ndarray, **ipargs: Any) -> Callable:
    """Linear interpolation through the given points

    Uses the scipy.interpolate.interp1d function with kind='linear' behind the scenes.

    Args:
        x:       1-dimensional array with original x-values.
        y:       Array with original y-values.
        ipargs:  Keyword arguments passed on to the interp1d-interpolator.

    Returns:
        Linear interpolation function
    """
    if y.ndim < 1:
        raise ValueError(f"The y array must have at least one dimension, currently y.ndim={y.ndim}.")

    # Interpolate along axis=0 by default
    ipargs.setdefault("axis", 0)
    return scipy.interpolate.interp1d(x, y, kind="linear", **ipargs)


@register_interpolator
def cubic(x: np.ndarray, y: np.ndarray, **ipargs: Any) -> Callable:
    """Cubic spline interpolation through the given points

    Uses the scipy.interpolate.interp1d function with kind='cubic' behind the scenes.

    Args:
        x:       1-dimensional array with original x-values.
        y:       Array with original y-values.
        ipargs:  Keyword arguments passed on to the interp1d-interpolator.

    Returns:
        Cubic spline interpolation function
    """
    if y.ndim < 1:
        raise ValueError(f"The y array must have at least one dimension, currently y.ndim={y.ndim}.")
    # Interpolate along axis=0 by default
    ipargs.setdefault("axis", 0)
    return scipy.interpolate.interp1d(x, y, kind="cubic", **ipargs)


@register_interpolator
def interpolated_univariate_spline(x: np.ndarray, y: np.ndarray, **ipargs: Any) -> Callable:
    """One-dimensional interpolating spline for the given points

    Uses the scipy.interpolate.InterpolatedUnivariateSpline function behind the scenes.

    The original only deals with one-dimensional y arrays, so multiple calls are made for higher dimensional y
    arrays. The dimensions are handled independently of each other.

    Args:
        x:       1-dimensional array with original x-values.
        y:       Array with original y-values.
        ipargs:  Keyword arguments passed on to the scipy-interpolator.

    Returns:
        Interpolating spline function
    """
    if y.ndim < 1:
        raise ValueError(f"The y array must have at least one dimension, currently y.ndim={y.ndim}.")
    if y.ndim == 1:
        return scipy.interpolate.InterpolatedUnivariateSpline(x, y, **ipargs)

    # Loop over columns in y for higher dimensions
    def _interpolated_univariate_spline(x_new: np.ndarray) -> np.ndarray:
        """Interpolate using an interpolating spline"""
        first_y = (slice(len(y)),)
        first_new = (slice(len(x_new)),)
        y_new = np.zeros(x_new.shape[:1] + y.shape[1:])

        for last_cols in np.ndindex(y.shape[1:]):
            idx_new = first_new + last_cols
            idx_y = first_y + last_cols
            y_new[idx_new] = scipy.interpolate.InterpolatedUnivariateSpline(x, y[idx_y], **ipargs)(x_new)

        return y_new

    return _interpolated_univariate_spline


@register_interpolator
def barycentric_interpolator(x: np.ndarray, y: np.ndarray, **ipargs: Any) -> Callable:
    """The interpolating polynomial through the given points

    Uses the scipy.interpolate.BarycentricInterpolator function behind the scenes.

    Args:
        x:       1-dimensional array with original x-values.
        y:       Array with original y-values.
        ipargs:  Keyword arguments passed on to the scipy-interpolator.

    Returns:
        Barycentric interpolation function
    """
    if y.ndim < 1:
        raise ValueError(f"The y array must have at least one dimension, currently y.ndim={y.ndim}.")
    return scipy.interpolate.BarycentricInterpolator(x, y, **ipargs)
