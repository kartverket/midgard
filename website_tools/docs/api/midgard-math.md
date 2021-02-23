# midgard.math


## midgard.math.constant
Midgard library module defining an assortment of constants

**Description:**

This module provides constants that are used within the Midgard project. The actual constants are defined in the
`constants.conf` file (see the file list for location). See that file for references and for adding or changing
constants.

The constants are stored as module variables so they can be used simply as `constant.c` as in the example above. Some
models use particular values for constants that are different from the conventional ones. This is handled by the source
parameter. For instance, the EGM 2008 gravity field is calculated with a value for GM different from the IERS
Conventions value, using::

    constant.get('GM', source='egm_2008')

instead of simply `constant.GM`.


**Example:**

    >>> from midgard.math.constant import Constant
    >>> print(f"The speed of light is {constant.c:0.2f}")
    The speed of light is 299792458.00


**Todo:**

Rewrite as a class instead of a module, to have somewhat cleaner code (and be more consistent with things like
lib.unit).



### **Constant**

Full name: `midgard.math.constant.Constant`

Signature: `() -> None`



### constant (Constant)
`constant = Constant('/home/kirann/miniconda3/lib/python3.8/site-packages/midgard/math/constant.txt')`


## midgard.math.ellipsoid
Midgard library module for handling Earth ellipsoids

**Description:**



### **Ellipsoid**

Full name: `midgard.math.ellipsoid.Ellipsoid`

Signature: `(name: str, a: float, f_inv: float, description: str) -> None`

Ellipsoid(name: str, a: float, f_inv: float, description: str)

### GRS80 (Ellipsoid)
`GRS80 = Ellipsoid(name='GRS80', a=6378137, f_inv=298.257222101, description='Used by ITRS')`


### IERS2003 (Ellipsoid)
`IERS2003 = Ellipsoid(name='IERS2003', a=6378136.6, f_inv=298.25642, description='IERS conventions 2003, p. 12')`


### IERS2010 (Ellipsoid)
`IERS2010 = Ellipsoid(name='IERS2010', a=6378136.6, f_inv=298.25642, description='IERS conventions 2010, p. 18')`


### WGS72 (Ellipsoid)
`WGS72 = Ellipsoid(name='WGS72', a=6378135, f_inv=298.26, description='WGS72')`


### WGS84 (Ellipsoid)
`WGS84 = Ellipsoid(name='WGS84', a=6378137, f_inv=298.257223563, description='Used by GPS')`


### **get**()

Full name: `midgard.math.ellipsoid.get`

Signature: `(ellipsoid: str) -> 'Ellipsoid'`

Get an ellipsoid by name

### sphere (Ellipsoid)
`sphere = Ellipsoid(name='sphere', a=6371008.8, f_inv=inf, description='Regular sphere, mean radius')`


## midgard.math.interpolation
Methods for interpolating in numpy arrays

**Description:**

Different interpolation methods are decorated with `@register_interpolator` and will then become available for use as
`kind` in `interpolate` and `moving_window`.


**Example:**

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


**Developer info:**

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



### **barycentric_interpolator**()

Full name: `midgard.math.interpolation.barycentric_interpolator`

Signature: `(x: numpy.ndarray, y: numpy.ndarray, **ipargs: Any) -> Callable`

The interpolating polynomial through the given points

Uses the scipy.interpolate.BarycentricInterpolator function behind the scenes.

**Args:**

- `x`:       1-dimensional array with original x-values.
- `y`:       Array with original y-values.
- `ipargs`:  Keyword arguments passed on to the scipy-interpolator.

**Returns:**

Barycentric interpolation function


### **cubic**()

Full name: `midgard.math.interpolation.cubic`

Signature: `(x: numpy.ndarray, y: numpy.ndarray, **ipargs: Any) -> Callable`

Cubic spline interpolation through the given points

Uses the scipy.interpolate.interp1d function with kind='cubic' behind the scenes.

**Args:**

- `x`:       1-dimensional array with original x-values.
- `y`:       Array with original y-values.
- `ipargs`:  Keyword arguments passed on to the interp1d-interpolator.

**Returns:**

Cubic spline interpolation function


### **get_interpolator**()

Full name: `midgard.math.interpolation.get_interpolator`

Signature: `(name: str) -> Callable`

Return an interpolation function

Interpolation functions are registered by the @register_interpolator-decorator. The name-parameter corresponds to
the function name of the interpolator.

**Args:**

- `name`:  Name of interpolator.

**Returns:**

Interpolation function with the given name.


### **interpolate**()

Full name: `midgard.math.interpolation.interpolate`

Signature: `(x: numpy.ndarray, y: numpy.ndarray, x_new: numpy.ndarray, *, kind: str, **ipargs: Any) -> numpy.ndarray`

Interpolate values from one x-array to another

See `interpolators()` for a list of valid interpolators.

**Args:**

- `x`:       1-dimensional array with original x-values.
- `y`:       Array with original y-values.
- `x_new`:   1-dimensional array with new x-values.
- `kind`:    Name of interpolator to use.
- `ipargs`:  Keyword arguments passed on to the interpolator.

**Returns:**

Array of interpolated y-values.


### **interpolate_with_derivative**()

Full name: `midgard.math.interpolation.interpolate_with_derivative`

Signature: `(x: numpy.ndarray, y: numpy.ndarray, x_new: numpy.ndarray, *, kind: str, dx: float = 0.5, **ipargs: Any) -> numpy.ndarray`

Interpolate values from one x-array to another as well as find derivatives

See `interpolators()` for a list of valid interpolators.

**Args:**

- `x`:      1-dimensional array with original x-values.
- `y`:      Array with original y-values.
- `x_new`:  1-dimensional array with new x-values.
- `kind`:   Name of interpolator to use.
- `dx`:     Values at x ± dx are used to determine derivative.
- `ipargs`:  Keyword arguments passed on to the interpolator.

**Returns:**

Tuple with array of interpolated y-values and array of derivatives.


### **interpolated_univariate_spline**()

Full name: `midgard.math.interpolation.interpolated_univariate_spline`

Signature: `(x: numpy.ndarray, y: numpy.ndarray, **ipargs: Any) -> Callable`

One-dimensional interpolating spline for the given points

Uses the scipy.interpolate.InterpolatedUnivariateSpline function behind the scenes.

The original only deals with one-dimensional y arrays, so multiple calls are made for higher dimensional y
arrays. The dimensions are handled independently of each other.

**Args:**

- `x`:       1-dimensional array with original x-values.
- `y`:       Array with original y-values.
- `ipargs`:  Keyword arguments passed on to the scipy-interpolator.

**Returns:**

Interpolating spline function


### **interpolators**()

Full name: `midgard.math.interpolation.interpolators`

Signature: `() -> List[str]`

Return a list of available interpolators

**Returns:**

Names of available interpolators.


### **lagrange**()

Full name: `midgard.math.interpolation.lagrange`

Signature: `(x: numpy.ndarray, y: numpy.ndarray, *, window: int = 10, bounds_error: bool = True, assume_sorted: bool = False) -> Callable`

Computes the lagrange polynomial passing through a certain set of points

See https://en.wikipedia.org/wiki/Lagrange_polynomial

Uses `window` of the original points to calculate the Lagrange polynomials. The window of points is chosen by
finding the closest original point and essentially picking the `window // 2` indices on either side.

**Args:**

- `x`:              1-dimensional array with original x-values.
- `y`:              Array with original y-values.
- `window`:         Number of points used in interpolation.
- `bounds_error`:   If True, a ValueError is raised if extrapolation is attempted.
- `assume_sorted`:  If True, x must be an array of monotonically increasing values.

**Returns:**

Lagrange interpolation function.


### **linear**()

Full name: `midgard.math.interpolation.linear`

Signature: `(x: numpy.ndarray, y: numpy.ndarray, **ipargs: Any) -> Callable`

Linear interpolation through the given points

Uses the scipy.interpolate.interp1d function with kind='linear' behind the scenes.

**Args:**

- `x`:       1-dimensional array with original x-values.
- `y`:       Array with original y-values.
- `ipargs`:  Keyword arguments passed on to the interp1d-interpolator.

**Returns:**

Linear interpolation function


### **register_interpolator**()

Full name: `midgard.math.interpolation.register_interpolator`

Signature: `(func: Callable) -> Callable`

Register an interpolation function

This function should be used as a @register_interpolator-decorator

**Args:**

- `func`: Function that will be registered as an interpolator.

**Returns:**

Same function.


## midgard.math.linear_regression
Midgard library module for linear regression

**Description:**



### **LinearRegression**

Full name: `midgard.math.linear_regression.LinearRegression`

Signature: `(x: numpy.ndarray, y: numpy.ndarray) -> None`

LinearRegression(x: numpy.ndarray, y: numpy.ndarray)

## midgard.math.nputil
Utility wrapper for numpy functions

Makes sure numpy functions can be called in a similar fashion for different use cases
 + both 1- and 2-dimensional input
 + both single values and arrays



### **HashArray**

Full name: `midgard.math.nputil.HashArray`

Signature: `(val)`



### **col**()

Full name: `midgard.math.nputil.col`

Signature: `(vector)`



### **hashable**()

Full name: `midgard.math.nputil.hashable`

Signature: `(func)`

Decorator for functions with numpy arrays as input arguments that will benefit from caching

Example:

from midgard.math import nputil
from functools import lru_cache

@nputil.hashable
@lru_cache()
def test_func(a: np.ndarray, b: np.ndarray = None)
    do_something
    return something


### **norm**()

Full name: `midgard.math.nputil.norm`

Signature: `(vector)`



### **row**()

Full name: `midgard.math.nputil.row`

Signature: `(vector)`



### **take**()

Full name: `midgard.math.nputil.take`

Signature: `(vector, item)`



### **unit_vector**()

Full name: `midgard.math.nputil.unit_vector`

Signature: `(vector)`



## midgard.math.planetary_motion
Midgard library for planetary motion

**Example:**

    from migard.math import planetary_motion


### **findsun**()

Full name: `midgard.math.planetary_motion.findsun`

Signature: `(time: 'Time') -> numpy.ndarray`

Obtains the position vector of the Sun in relation to Earth (in ECEF).

This routine is a reimplementation of routine findSun() in model.c of gLAB 3.0.0 software. The gLAB 3.0.0 software
core excecutables are distributed under the Apache License version 2.0 related to following copyright and license:

COPYRIGHT 2009 - 2016 GAGE/UPC & ESA

LICENSED UNDER THE APACHE LICENSE, VERSION 2.0 (THE "LICENSE"); YOU MAY NOT USE THIS ROUTINE EXCEPT IN COMPLIANCE 
WITH THE LICENSE. YOU MAY OBTAIN A COPY OF THE LICENSE AT

HTTP://WWW.APACHE.ORG/LICENSES/LICENSE-2.0

UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING, SOFTWARE DISTRIBUTED UNDER THE LICENSE IS DISTRIBUTED ON 
AN "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED. SEE THE LICENSE FOR THE 
SPECIFIC LANGUAGE GOVERNING PERMISSIONS AND LIMITATIONS UNDER THE LICENSE.

**Args:**

- `time`:    Time object

**Returns:**

Sun position vector given in ECEF [m]


### **gsdtime_sun**()

Full name: `midgard.math.planetary_motion.gsdtime_sun`

Signature: `(time: 'Time') -> Tuple[numpy.ndarray]`

Get position of the sun (low-precision)

This routine is a reimplementation of routine GSDtime_sun() in model.c of gLAB 3.0.0 software. The gLAB 3.0.0 
software core excecutables are distributed under the Apache License version 2.0 related to following copyright and 
license:

COPYRIGHT 2009 - 2016 GAGE/UPC & ESA

LICENSED UNDER THE APACHE LICENSE, VERSION 2.0 (THE "LICENSE"); YOU MAY NOT USE THIS ROUTINE EXCEPT IN COMPLIANCE 
WITH THE LICENSE. YOU MAY OBTAIN A COPY OF THE LICENSE AT

HTTP://WWW.APACHE.ORG/LICENSES/LICENSE-2.0

UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING, SOFTWARE DISTRIBUTED UNDER THE LICENSE IS DISTRIBUTED ON 
AN "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED. SEE THE LICENSE FOR THE 
SPECIFIC LANGUAGE GOVERNING PERMISSIONS AND LIMITATIONS UNDER THE LICENSE.

**Args:**

- `time`:    Time object

**Returns:**

Tuple with following entries:

| Elements  |   Description                                |
|-----------|----------------------------------------------|
| gstr      | GMST0 (to go from ECEF to inertial) [deg]    |
| slong     | Sun longitude [deg]                          |
| sra       | Sun right Ascension [deg]                    |
| sdec      | Sun declination in [deg]                     |


## midgard.math.rotation
Library for basic rotation matrices

**Description:**

Creates rotation matrices for rotation around the axes of a right handed Cartesian coordinate system and
their derivatives.

For instance, for an XYZ-system, R1 returns a rotation matrix around the x-axis and for an ENU-system, R1 returns a
rotation matrix around the east-axis. dR1 returns the derivative of the R1 matrix with respect to the rotation
angle. All functions are vectorized, so that one rotation matrix is returned per input angle.


**Example:**

>>> from where.lib import rotation
>>> rotation.R1([0, 1])
array([[[ 1.        ,  0.        ,  0.        ],
        [ 0.        ,  1.        ,  0.        ],
        [ 0.        , -0.        ,  1.        ]],

       [[ 1.        ,  0.        ,  0.        ],
        [ 0.        ,  0.54030231,  0.84147098],
        [ 0.        , -0.84147098,  0.54030231]]])



### **R1**()

Full name: `midgard.math.rotation.R1`

Signature: `(angle: ~np_float) -> numpy.ndarray`

Rotation matrix around the first axis

**Args:**

- `angle`:  Scalar, list or numpy array of angles in radians.

**Returns:**

Numpy array:   Rotation matrix or array of rotation matrices.


### **R2**()

Full name: `midgard.math.rotation.R2`

Signature: `(angle: ~np_float) -> numpy.ndarray`

Rotation matrix around the second axis

**Args:**

- `angle`:  Scalar, list or numpy array of angles in radians.

**Returns:**

Numpy array:   Rotation matrix or array of rotation matrices.


### **R3**()

Full name: `midgard.math.rotation.R3`

Signature: `(angle: ~np_float) -> numpy.ndarray`

Rotation matrix around the third axis

**Args:**

- `angle`:  Scalar, list or numpy array of angles in radians.

**Returns:**

Numpy array:   Rotation matrix or array of rotation matrices.


### **dR1**()

Full name: `midgard.math.rotation.dR1`

Signature: `(angle: ~np_float) -> numpy.ndarray`

Derivative of a rotation matrix around the first axis with respect to the rotation angle.

**Args:**

- `angle`:  Scalar, list or numpy array of angles in radians.

**Returns:**

Numpy array:   Rotation matrix or array of rotation matrices.


### **dR2**()

Full name: `midgard.math.rotation.dR2`

Signature: `(angle: ~np_float) -> numpy.ndarray`

Derivative of a rotation matrix around the second axis with respect to the rotation angle

**Args:**

- `angle`:  Scalar, list or numpy array of angles in radians.

**Returns:**

Numpy array:   Rotation matrix or array of rotation matrices.


### **dR3**()

Full name: `midgard.math.rotation.dR3`

Signature: `(angle: ~np_float) -> numpy.ndarray`

Derivative of a rotation matrix around the third axis with respect to the rotation angle

**Args:**

- `angle`:  Scalar, list or numpy array of angles in radians.

**Returns:**

Numpy array:   Rotation matrix or array of rotation matrices.


### **enu2trs**()

Full name: `midgard.math.rotation.enu2trs`

Signature: `(lat: ~np_float, lon: ~np_float) -> numpy.ndarray`

Rotation matrix for rotating an ENU coordinate system to an earth oriented one

See for instance http://www.navipedia.net/index.php/Transformations_between_ECEF_and_ENU_coordinates
This is equal to doing::

    R3(-(np.pi/2 + lon)) @ R1(-(np.pi/2 - lat))

**Args:**

lat (Float or Array):   Latitude of origin of ENU coordinate system.
lon (Float or Array):   Longitude of origin of ENU coordinate system.

**Returns:**

Numpy array:   Rotation matrix or array of rotation matrices.


### np_float (TypeVar)
`np_float = ~np_float`


### **trs2enu**()

Full name: `midgard.math.rotation.trs2enu`

Signature: `(lat: ~np_float, lon: ~np_float) -> numpy.ndarray`

Rotation matrix for rotating an earth oriented coordinate system to an ENU one

See for instance http://www.navipedia.net/index.php/Transformations_between_ECEF_and_ENU_coordinates
This is equal to doing::

    R1(np.pi/2 - lat) @ R3(np.pi/2 + lon)

**Args:**

lat (Float or Array):   Latitude of origin of ENU coordinate system.
lon (Float or Array):   Longitude of origin of ENU coordinate system.

**Returns:**

Numpy array:   Rotation matrix or array of rotation matrices.


## midgard.math.transformation
Midgard library module for handling of geodetic conversions

**Description:**



### **delta_acr2trs_posvel**()

Full name: `midgard.math.transformation.delta_acr2trs_posvel`

Signature: `(acr: 'AcrPosVelDelta') -> 'TrsPosVelDelta'`

Convert position deltas from ACR to TRS

### **delta_enu2trs**()

Full name: `midgard.math.transformation.delta_enu2trs`

Signature: `(enu: 'EnuPositionDelta') -> 'TrsPositionDelta'`

Convert position deltas from ENU to TRS

### **delta_enu2trs_posvel**()

Full name: `midgard.math.transformation.delta_enu2trs_posvel`

Signature: `(enu: 'EnuPosVelDelta') -> 'TrsPosVelDelta'`

Convert position deltas from ENU to TRS

### **delta_trs2acr_posvel**()

Full name: `midgard.math.transformation.delta_trs2acr_posvel`

Signature: `(trs: 'TrsPosVelDelta') -> 'AcrPosVelDelta'`

Convert position deltas from TRS to ACR

### **delta_trs2enu**()

Full name: `midgard.math.transformation.delta_trs2enu`

Signature: `(trs: 'TrsPositionDelta') -> 'EnuPositionDelta'`

Convert position deltas from TRS to ENU

### **delta_trs2enu_posvel**()

Full name: `midgard.math.transformation.delta_trs2enu_posvel`

Signature: `(trs: 'TrsPosVelDelta') -> 'EnuPosVelDelta'`

Convert position deltas from TRS to ENU

### **kepler2trs**()

Full name: `midgard.math.transformation.kepler2trs`

Signature: `(kepler: 'KeplerPosVel') -> 'TrsPosVel'`

Compute orbit position and velocity vector in geocentric equatorial coordinate system based on Keplerian
elements for elliptic orbits.

The implementation is based on Section 2.2.3 in :cite:`montenbruck2012`.



### **llh2trs**()

Full name: `midgard.math.transformation.llh2trs`

Signature: `(llh: numpy.ndarray, ellipsoid: midgard.math.ellipsoid.Ellipsoid = None) -> numpy.ndarray`

Convert geodetic latitude-, longitude-, height-coordinates to geocentric xyz-coordinates

Reimplementation of GD2GCE.for from the IUA SOFA software collection.


### **trs2kepler**()

Full name: `midgard.math.transformation.trs2kepler`

Signature: `(trs: 'TrsPosVel') -> 'KeplerPosVel'`

Compute Keplerian elements for elliptic orbit based on orbit position and velocity vector given in ITRS.

The used equations are described in Section 2.2.4 in Montenbruck :cite:`montenbruck2012`.

The position and velocity vector in ITRS and GM must be given in consistent units, which are [m], [m/s] and
[m^3/s^2]. The resulting unit of the semimajor axis is implied by the unity of the position vector, i.e. [m].

.. note::
The function cannot be used with position/velocity vectors describing a circular or non-inclined orbit.

**Returns:**

tuple with numpy.ndarray types: Tuple with following Keplerian elements:

===============  ======  ==================================================================================
 Keys             Unit     Description
===============  ======  ==================================================================================
 a                m       Semimajor axis
 e                        Eccentricity of the orbit
 i                rad     Inclination
 Omega            rad     Right ascension of the ascending node
 omega            rad     Argument of perigee
 E                rad     Eccentric anomaly
===============  ======  ==================================================================================


### **trs2llh**()

Full name: `midgard.math.transformation.trs2llh`

Signature: `(trs: numpy.ndarray, ellipsoid: midgard.math.ellipsoid.Ellipsoid = None) -> numpy.ndarray`

Convert geocentric xyz-coordinates to geodetic latitude-, longitude-, height-coordinates

Reimplementation of GC2GDE.for from the IUA SOFA software collection.



## midgard.math.unit
Midgard library module for handling of SI-unit conversions

**Description:**

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


### **Unit**

Full name: `midgard.math.unit.Unit`

Signature: `(from_unit: str, to_unit: Union[str, NoneType] = None) -> Any`

Unit converter

The implementation of the unit conversion is done in the `_convert_units`-metaclass.


### fid (TextIOWrapper)
`fid = <_io.TextIOWrapper name='/home/kirann/miniconda3/lib/python3.8/site-packages/midgard/math/unit.txt' encoding='utf-8'>`


### np_float (TypeVar)
`np_float = ~np_float`
