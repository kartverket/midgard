# midgard.data


## midgard.data._h5utils
Simple utilities used by Dataset when dealing with HDF5 files



### **decode_h5attr**()

Full name: `midgard.data._h5utils.decode_h5attr`

Signature: `(attr: Any) -> Any`

Convert hdf5 attribute back to its original datatype

### **encode_h5attr**()

Full name: `midgard.data._h5utils.encode_h5attr`

Signature: `(data: Any) -> Any`

Convert a basic data type to something that can be saved as a hdf5 attribute

## midgard.data._position
 Module for dealing with positions, velocities and position corrections in different coordinate systems


### **PosBase**

Full name: `midgard.data._position.PosBase`

Signature: `()`

Base class for the various position and velocity arrays

### **PosVelArray**

Full name: `midgard.data._position.PosVelArray`

Signature: `(val, ellipsoid=Ellipsoid(name='GRS80', a=6378137, f_inv=298.257222101, description='Used by ITRS'), **pos_args)`

Base class for Position and Velocity arrays

This PosVelArray should not be instantiated. Instead instantiate one of
the system specific subclasses, typically using the Position factory
function.


### **PosVelDeltaArray**

Full name: `midgard.data._position.PosVelDeltaArray`

Signature: `(val, ref_pos, **delta_args)`

Base class for position and velocity deltas

This PosVelDeltaArray should not be instantiated. Instead instantiate one
of the system specific subclasses, typically using the PositionDelta
factory function.


### **PositionArray**

Full name: `midgard.data._position.PositionArray`

Signature: `(val, ellipsoid=Ellipsoid(name='GRS80', a=6378137, f_inv=298.257222101, description='Used by ITRS'), **pos_args)`

Base class for Position arrays

This PositionArray should not be instantiated. Instead instantiate one of
the system specific subclasses, typically using the Position factory
function.


### **PositionDeltaArray**

Full name: `midgard.data._position.PositionDeltaArray`

Signature: `(val, ref_pos, **delta_args)`

Base class for position deltas

This PositionDeltaArray should not be instantiated. Instead instantiate one
of the system specific subclasses, typically using the PositionDelta
factory function.


### **VelocityArray**

Full name: `midgard.data._position.VelocityArray`

Signature: `(val, ref_pos, **vel_args)`

Base class for Velocity arrays

This VelocityArray should not be instantiated. Instead instantiate one of
the system specific subclasses. The intended usage will be through a PosVelArray


### **VelocityDeltaArray**

Full name: `midgard.data._position.VelocityDeltaArray`

Signature: `(val, ref_pos, **vel_args)`

Base class for Velocity arrays

This VelocityArray should not be instantiated. Instead instantiate one of
the system specific subclasses. The intended usage will be through a PosVelArray


### **register_attribute**()

Full name: `midgard.data._position.register_attribute`

Signature: `(cls: Callable, name: str) -> None`

Function used to register new attributes on position arrays

The registered attributes will be available as attributes on PositionArray
and its subclasses. In addition, each attribute can be given as a parameter
when creating a PositionArray.

The reason for using this register-function instead of a regular attribute
is to allow additional attributes to be added on all position systems.

**Args:**

- `cls`:      Class to register the attribute for
- `name`:     Name of attribute


### **register_field**()

Full name: `midgard.data._position.register_field`

Signature: `(units: List[str], dependence: str = None) -> Callable`

Decorator used to register fields and their units

**Args:**
 
units:             units for the field (tuple of strings)
dependance:        name of attribute that needs to be set for field to make sense


### **register_system**()

Full name: `midgard.data._position.register_system`

Signature: `(convert_to: Dict[str, Callable] = None, convert_from: Dict[str, Callable] = None) -> Callable[[Callable], Callable]`

Decorator used to register new position systems

The system name is read from the .system attribute of the Position class.

**Args:**

- `convert_to`:    Functions used to convert to other systems.
- `convert_from`:  Functions used to convert from other systems.

**Returns:**

Decorator registering system.


## midgard.data._time
Array with time epochs


### **GpsTime**

Full name: `midgard.data._time.GpsTime`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **GpsTimeDelta**

Full name: `midgard.data._time.GpsTimeDelta`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **TaiTime**

Full name: `midgard.data._time.TaiTime`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **TaiTimeDelta**

Full name: `midgard.data._time.TaiTimeDelta`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **TcgTime**

Full name: `midgard.data._time.TcgTime`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **TcgTimeDelta**

Full name: `midgard.data._time.TcgTimeDelta`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **TimeArray**

Full name: `midgard.data._time.TimeArray`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`

Base class for time objects. Is immutable to allow the data to be hashable

### **TimeBase**

Full name: `midgard.data._time.TimeBase`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`

Base class for TimeArray and TimeDeltaArray

### **TimeDate**

Full name: `midgard.data._time.TimeDate`

Signature: `(val, val2=None, scale=None)`



### **TimeDateTime**

Full name: `midgard.data._time.TimeDateTime`

Signature: `(val, val2=None, scale=None)`



### **TimeDecimalYear**

Full name: `midgard.data._time.TimeDecimalYear`

Signature: `(val, val2=None, scale=None)`

Time as year with decimal number. (Ex: 2000.0). Variable year length.

### **TimeDeltaArray**

Full name: `midgard.data._time.TimeDeltaArray`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`

Base class for time delta objects. Is immutable to allow the data to be hashable

### **TimeDeltaDateTime**

Full name: `midgard.data._time.TimeDeltaDateTime`

Signature: `(val, val2=None, scale=None)`

Time delta as datetime's timedelta

### **TimeDeltaDay**

Full name: `midgard.data._time.TimeDeltaDay`

Signature: `(val, val2=None, scale=None)`

Time delta in days

### **TimeDeltaFormat**

Full name: `midgard.data._time.TimeDeltaFormat`

Signature: `(val, val2=None, scale=None)`

Base class for Time Delta formats

### **TimeDeltaJD**

Full name: `midgard.data._time.TimeDeltaJD`

Signature: `(val, val2=None, scale=None)`

Time delta as Julian days

### **TimeDeltaSec**

Full name: `midgard.data._time.TimeDeltaSec`

Signature: `(val, val2=None, scale=None)`

Time delta in seconds

### **TimeFormat**

Full name: `midgard.data._time.TimeFormat`

Signature: `(val, val2=None, scale=None)`



### **TimeGPSSec**

Full name: `midgard.data._time.TimeGPSSec`

Signature: `(val, val2=None, scale=None)`

Number of seconds since the GPS epoch 1980-01-06 00:00:00 UTC.

### **TimeGPSWeekSec**

Full name: `midgard.data._time.TimeGPSWeekSec`

Signature: `(val, val2=None, scale=None)`

GPS weeks and seconds.

### **TimeIso**

Full name: `midgard.data._time.TimeIso`

Signature: `(val, val2=None, scale=None)`

ISO 8601 compliant date-time format “YYYY-MM-DD HH:MM:SS.sss…” without the T

### **TimeIsot**

Full name: `midgard.data._time.TimeIsot`

Signature: `(val, val2=None, scale=None)`

ISO 8601 compliant date-time format “YYYY-MM-DDTHH:MM:SS.sss…” 

### **TimeJD**

Full name: `midgard.data._time.TimeJD`

Signature: `(val, val2=None, scale=None)`



### **TimeJulianYear**

Full name: `midgard.data._time.TimeJulianYear`

Signature: `(val, val2=None, scale=None)`

Time as year with decimal number. (Ex: 2000.0). Fixed year length.

### **TimeMJD**

Full name: `midgard.data._time.TimeMJD`

Signature: `(val, val2=None, scale=None)`

Modified Julian Date time format.

This represents the number of days since midnight on November 17, 1858.
For example, 51544.0 in MJD is midnight on January 1, 2000.


### **TimePlotDate**

Full name: `midgard.data._time.TimePlotDate`

Signature: `(val, val2=None, scale=None)`

Matplotlib date format

Matplotlib represents dates using floating point numbers specifying the number
of days since 0001-01-01 UTC, plus 1.  For example, 0001-01-01, 06:00 is 1.25,
not 0.25. Values < 1, i.e. dates before 0001-01-01 UTC are not supported.

Warning: This requires matplotlib version 3.2.2 or lower


### **TimeStr**

Full name: `midgard.data._time.TimeStr`

Signature: `(val, val2=None, scale=None)`

Base class for text based time. 

### **TimeYearDoy**

Full name: `midgard.data._time.TimeYearDoy`

Signature: `(val, val2=None, scale=None)`



### **TimeYyDddSssss**

Full name: `midgard.data._time.TimeYyDddSssss`

Signature: `(val, val2=None, scale=None)`

Time as 2 digit year, doy and second of day.

Text based format "yy:ddd:sssss"
    yy     - decimal year without century
    ddd    - zero padded decimal day of year
    sssss  - zero padded seconds since midnight

    Note   -  Does not support leap seconds

    Returns:
        Time converted to yydddssss format



### **TimeYyyyDddSssss**

Full name: `midgard.data._time.TimeYyyyDddSssss`

Signature: `(val, val2=None, scale=None)`

Time as 4-digit year, doy and second of day.

Text based format "yyyy:ddd:sssss"
    yyyy   - decimal year with century
    ddd    - zero padded decimal day of year
    sssss  - zero padded seconds since midnight

    Note   -  Does not support leap seconds

    Returns:
        Time converted to yydddssss format



### **TtTime**

Full name: `midgard.data._time.TtTime`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **TtTimeDelta**

Full name: `midgard.data._time.TtTimeDelta`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **UtcTime**

Full name: `midgard.data._time.UtcTime`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **UtcTimeDelta**

Full name: `midgard.data._time.UtcTimeDelta`

Signature: `(val, fmt, val2=None, _jd1=None, _jd2=None)`



### **delta_gps_tai**()

Full name: `midgard.data._time.delta_gps_tai`

Signature: `(time: 'TimeArray') -> 'np_float'`



### **delta_tai_tt**()

Full name: `midgard.data._time.delta_tai_tt`

Signature: `(time: 'TimeArray') -> 'np_float'`



### **delta_tai_utc**()

Full name: `midgard.data._time.delta_tai_utc`

Signature: `(time: 'TimeArray') -> 'np_float'`



### **delta_tcg_tt**()

Full name: `midgard.data._time.delta_tcg_tt`

Signature: `(time: 'TimeArray') -> 'np_float'`



### np_float (TypeVar)
`np_float = ~np_float`


### **read_tai_utc**()

Full name: `midgard.data._time.read_tai_utc`

Signature: `()`



### **register_format**()

Full name: `midgard.data._time.register_format`

Signature: `(cls: Callable) -> Callable`

Decorator used to register new time formats

The format name is read from the .format attribute of the TimeFormat class.


### **register_scale**()

Full name: `midgard.data._time.register_scale`

Signature: `(convert_to: Dict[str, Callable] = None, convert_from: Dict[str, Callable] = None) -> Callable[[Callable], Callable]`

Decorator used to register new time scales

The scale name is read from the .scale attribute of the Time class.

**Args:**

- `convert_to`:    Functions used to convert to other scales.
- `convert_from`:  Functions used to convert from other scales.

**Returns:**

Decorator registering scale.


## midgard.data.collection
 A collection of fields 

Also serves as base class for dataset


### **Collection**

Full name: `midgard.data.collection.Collection`

Signature: `()`



## midgard.data.dataset
A dataset for handling time series data

**Description:**



### **Dataset**

Full name: `midgard.data.dataset.Dataset`

Signature: `(num_obs: int = 0) -> None`

A dataset representing fields of data arrays

### **Meta**

Full name: `midgard.data.dataset.Meta`

Signature: `(dict=None, /, **kwargs)`



### field_type (str)
`field_type = 'time_delta'`


## midgard.data.fieldtypes
Field types that can be used by Dataset



### **fieldtype**()

Full name: `midgard.data.fieldtypes.fieldtype`

Signature: `(data: Any) -> Callable`

Find correct field type for given data

### **function**()

Full name: `midgard.data.fieldtypes.function`

Signature: `(plugin_name: str) -> Callable`

Function creating new field

### **names**()

Full name: `midgard.data.fieldtypes.names`

Signature: `() -> List[str]`

Names of fieldtype plugins

## midgard.data.fieldtypes._fieldtype
Abstract class used to define different types of tables for a Dataset



### **FieldType**

Full name: `midgard.data.fieldtypes._fieldtype.FieldType`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`

Abstract class representing a type of field in the Dataset

## midgard.data.fieldtypes.bool
A Dataset boolean field


### **BoolField**

Full name: `midgard.data.fieldtypes.bool.BoolField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.collection
A Dataset collection field consisting of other fields



### **CollectionField**

Full name: `midgard.data.fieldtypes.collection.CollectionField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.float
A Dataset float field



### **FloatField**

Full name: `midgard.data.fieldtypes.float.FloatField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.position
A Dataset position field



### **PositionField**

Full name: `midgard.data.fieldtypes.position.PositionField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.position_delta
A Dataset position delta field



### **PositionDeltaField**

Full name: `midgard.data.fieldtypes.position_delta.PositionDeltaField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.posvel
A Dataset position field



### **PosVelField**

Full name: `midgard.data.fieldtypes.posvel.PosVelField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.posvel_delta
A Dataset position delta field



### **PosVelDeltaField**

Full name: `midgard.data.fieldtypes.posvel_delta.PosVelDeltaField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.sigma
A Dataset sigma field


### **SigmaField**

Full name: `midgard.data.fieldtypes.sigma.SigmaField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.text
A Dataset text field



### **TextField**

Full name: `midgard.data.fieldtypes.text.TextField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.time
A Dataset time field


### **TimeField**

Full name: `midgard.data.fieldtypes.time.TimeField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.fieldtypes.time_delta
A Dataset time field


### **TimeDeltaField**

Full name: `midgard.data.fieldtypes.time_delta.TimeDeltaField`

Signature: `(num_obs, name, val=None, unit=None, write_level=None, multiplier=1, **field_args)`



## midgard.data.position
Array with positions


### **AcrPosVelDelta**

Full name: `midgard.data.position.AcrPosVelDelta`

Signature: `(val, ref_pos, **delta_args)`



### **AcrPositionDelta**

Full name: `midgard.data.position.AcrPositionDelta`

Signature: `(val, ref_pos, **delta_args)`



### **AcrVelocityDelta**

Full name: `midgard.data.position.AcrVelocityDelta`

Signature: `(val, ref_pos, **vel_args)`



### **EnuPosVelDelta**

Full name: `midgard.data.position.EnuPosVelDelta`

Signature: `(val, ref_pos, **delta_args)`



### **EnuPositionDelta**

Full name: `midgard.data.position.EnuPositionDelta`

Signature: `(val, ref_pos, **delta_args)`



### **EnuVelocityDelta**

Full name: `midgard.data.position.EnuVelocityDelta`

Signature: `(val, ref_pos, **vel_args)`



### **KeplerPosVel**

Full name: `midgard.data.position.KeplerPosVel`

Signature: `(val, ellipsoid=Ellipsoid(name='GRS80', a=6378137, f_inv=298.257222101, description='Used by ITRS'), **pos_args)`



### **LlhPosition**

Full name: `midgard.data.position.LlhPosition`

Signature: `(val, ellipsoid=Ellipsoid(name='GRS80', a=6378137, f_inv=298.257222101, description='Used by ITRS'), **pos_args)`



### **PosVel**()

Full name: `midgard.data.position.PosVel`

Signature: `(val: numpy.ndarray, system: str, **pos_args: Any) -> 'PosVelArray'`

Factory for creating PosVelArrays for different systems

See each position class for exact optional parameters.

**Args:**

- `val`:       Array of position values.
- `system`:    Name of position system.
- `pos_args`:  Additional arguments used to create the PosVelArray.

**Returns:**

Array with positions in the given system.


### **PosVelDelta**()

Full name: `midgard.data.position.PosVelDelta`

Signature: `(val: numpy.ndarray, system: str, ref_pos: 'PosVelArray', **delta_args: Any) -> 'PosVelDeltaArray'`

Factory for creating PosVelArrays for different systems

See each position class for exact optional parameters.

**Args:**

- `val`:         Array of position values.
- `system`:      Name of position system.
- `ref_pos`:     Reference position.
- `delta_args`:  Additional arguments used to create the PosVelArray.

**Returns:**

Array with positions in the given system.


### **Position**()

Full name: `midgard.data.position.Position`

Signature: `(val: numpy.ndarray, system: str, **pos_args: Any) -> 'PositionArray'`

Factory for creating PositionArrays for different systems

See each position class for exact optional parameters.

**Args:**

- `val`:       Array of position values.
- `system`:    Name of position system.
- `pos_args`:  Additional arguments used to create the PositionArray.

**Returns:**

Array with positions in the given system.


### **PositionDelta**()

Full name: `midgard.data.position.PositionDelta`

Signature: `(val: numpy.ndarray, system: str, ref_pos: 'PositionArray', **delta_args: Any) -> 'PositionDeltaArray'`

Factory for creating PositionArrays for different systems

See each position class for exact optional parameters.

**Args:**

- `val`:         Array of position values.
- `system`:      Name of position system.
- `ref_pos`:     Reference position.
- `delta_args`:  Additional arguments used to create the PositionArray.

**Returns:**

Array with positions in the given system.


### **TrsPosVel**

Full name: `midgard.data.position.TrsPosVel`

Signature: `(val, ellipsoid=Ellipsoid(name='GRS80', a=6378137, f_inv=298.257222101, description='Used by ITRS'), **pos_args)`



### **TrsPosVelDelta**

Full name: `midgard.data.position.TrsPosVelDelta`

Signature: `(val, ref_pos, **delta_args)`



### **TrsPosition**

Full name: `midgard.data.position.TrsPosition`

Signature: `(val, ellipsoid=Ellipsoid(name='GRS80', a=6378137, f_inv=298.257222101, description='Used by ITRS'), **pos_args)`



### **TrsPositionDelta**

Full name: `midgard.data.position.TrsPositionDelta`

Signature: `(val, ref_pos, **delta_args)`



### **TrsVelocity**

Full name: `midgard.data.position.TrsVelocity`

Signature: `(val, ref_pos, **vel_args)`



### **TrsVelocityDelta**

Full name: `midgard.data.position.TrsVelocityDelta`

Signature: `(val, ref_pos, **vel_args)`



### **is_position**()

Full name: `midgard.data.position.is_position`

Signature: `(val)`



### **is_position_delta**()

Full name: `midgard.data.position.is_position_delta`

Signature: `(val)`



### **is_posvel**()

Full name: `midgard.data.position.is_posvel`

Signature: `(val)`



### **is_posvel_delta**()

Full name: `midgard.data.position.is_posvel_delta`

Signature: `(val)`



## midgard.data.sigma
Array with sigma values

See https://docs.scipy.org/doc/numpy/user/basics.subclassing.html for information about subclassing Numpy arrays.

SigmaArray is a regular Numpy array with an added field, sigma.


### **SigmaArray**

Full name: `midgard.data.sigma.SigmaArray`

Signature: `(values, sigma=None, unit=None)`



## midgard.data.time
Array with time epochs


### **Time**()

Full name: `midgard.data.time.Time`

Signature: `(val: numpy.ndarray, scale: str, fmt: str, val2: Union[numpy.ndarray, NoneType] = None, _jd1: Union[numpy.ndarray, NoneType] = None, _jd2: Union[numpy.ndarray, NoneType] = None) -> 'TimeArray'`

Factory for creating TimeArrays for different systems

See each time class for exact optional parameters.

**Args:**

- `val`:     Array of time values.
- `val2`:    Optional second array for extra precision.
- `scale`:   Name of time scale.
- `fmt`:  Format of values given in val and val2.

**Returns:**

Array with epochs in the given time scale and format


### **TimeDelta**()

Full name: `midgard.data.time.TimeDelta`

Signature: `(val: numpy.ndarray, scale: str, fmt: str, val2: Union[numpy.ndarray, NoneType] = None) -> 'TimeDeltaArray'`

Factory for creating TimeArrays for different systems

See each time class for exact optional parameters.

**Args:**

- `val`:     Array of time values.
- `val2`:    Optional second array for extra precision.
- `scale`:   Name of time scale.
- `fmt`:  Format of values given in val and val2.

**Returns:**

Array with epochs in the given time scale and format


### **is_time**()

Full name: `midgard.data.time.is_time`

Signature: `(val)`



### **is_timedelta**()

Full name: `midgard.data.time.is_timedelta`

Signature: `(val)`

