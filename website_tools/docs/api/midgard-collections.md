# midgard.collections


## midgard.collections.enums
Framework for working with enumerations

**Description:**

Custom enumerations used for structured names. You can add your own enumerations in your own application by importing
`register_enum` and using that to register your own enums.

References:

[1] RINEX Version 3.04 (2018): RINEX The receiver independent exchange format version 3.04, November 23, 2018


**Example:**

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


### **BeidouFreqNum2Freq**

Full name: `midgard.collections.enums.BeidouFreqNum2Freq`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **BeidouFrequency**

Full name: `midgard.collections.enums.BeidouFrequency`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

BeiDou frequencies in Hz

### **ExitStatus**

Full name: `midgard.collections.enums.ExitStatus`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Exit status definition

### **GPSFrequency**

Full name: `midgard.collections.enums.GPSFrequency`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

GPS frequencies in Hz

### **GalileoFreqNum2Freq**

Full name: `midgard.collections.enums.GalileoFreqNum2Freq`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **GalileoFrequency**

Full name: `midgard.collections.enums.GalileoFrequency`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Galileo frequencies in Hz

### **GlonassFreqNum2Freq**

Full name: `midgard.collections.enums.GlonassFreqNum2Freq`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **Gnss3DigitIdToId**

Full name: `midgard.collections.enums.Gnss3DigitIdToId`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

RINEX GNSS 3-digit identifier to RINEX GNSS identifier

### **GnssIdTo3DigitId**

Full name: `midgard.collections.enums.GnssIdTo3DigitId`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

RINEX GNSS RINEX identifier to GNSS 3-digit identifier

### **GnssIdToName**

Full name: `midgard.collections.enums.GnssIdToName`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

RINEX GNSS identifier to GNSS name

### **GnssIdToReferenceSystem**

Full name: `midgard.collections.enums.GnssIdToReferenceSystem`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

RINEX GNSS RINEX identifier to relevant GNSS reference system name

### **GnssNameToId**

Full name: `midgard.collections.enums.GnssNameToId`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

GNSS name to RINEX GNSS identifier

### **GpsFreqNum2Freq**

Full name: `midgard.collections.enums.GpsFreqNum2Freq`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **IrnssFreqNum2Freq**

Full name: `midgard.collections.enums.IrnssFreqNum2Freq`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **IrnssFrequency**

Full name: `midgard.collections.enums.IrnssFrequency`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

IRNSS frequencies in Hz

### **LogColor**

Full name: `midgard.collections.enums.LogColor`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Colors used when logging

### **LogLevel**

Full name: `midgard.collections.enums.LogLevel`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Levels used when deciding how much log output to show

### **NotGiven**

Full name: `midgard.collections.enums.NotGiven`

Signature: `()`

Dummy class used as a marker for a argument not given, used instead of None because None is valid value

### **QzssFreqNum2Freq**

Full name: `midgard.collections.enums.QzssFreqNum2Freq`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **QzssFrequency**

Full name: `midgard.collections.enums.QzssFrequency`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

QZSS frequencies in Hz

### **RefSysNameToEpsg**

Full name: `midgard.collections.enums.RefSysNameToEpsg`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Reference system name to EPSG code

### **SbasFreqNum2Freq**

Full name: `midgard.collections.enums.SbasFreqNum2Freq`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **SbasFrequency**

Full name: `midgard.collections.enums.SbasFrequency`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

SBAS frequencies in Hz

### **WriteLevel**

Full name: `midgard.collections.enums.WriteLevel`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Levels used when deciding which fields of a dataset and other information to write to disk

### **enums**()

Full name: `midgard.collections.enums.enums`

Signature: `() -> List[str]`

Return a list of available enums

**Returns:**

Names of available enums.


### **exit_status**

Full name: `midgard.collections.enums.exit_status`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Exit status definition

### **get_enum**()

Full name: `midgard.collections.enums.get_enum`

Signature: `(name: str) -> enum.EnumMeta`

Return a named Enumeration

Names are defined by the @register_enum-decorator. If the name-parameter is not a valid enum, the function will
raise an UnknownEnumError and list the available enumerations.

**Args:**

- `name`:  Name used for Enumeration.

**Returns:**

Enumeration with the given name.


### **get_value**()

Full name: `midgard.collections.enums.get_value`

Signature: `(name: str, value: str, default: Any = <class 'midgard.collections.enums.NotGiven'>) -> enum.Enum`

Return the value of a named Enumeration

Names are defined by the @register_enum-decorator.

**Args:**

- `name`:     Name used for Enumeration.
- `value`:    Value of Enumeration.
- `default`:  Optional object returned if enumeration does not contain value

**Returns:**

Value of enumeration with the given name.


### **gnss_3digit_id_to_id**

Full name: `midgard.collections.enums.gnss_3digit_id_to_id`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

RINEX GNSS 3-digit identifier to RINEX GNSS identifier

### **gnss_freq_C**

Full name: `midgard.collections.enums.gnss_freq_C`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

BeiDou frequencies in Hz

### **gnss_freq_E**

Full name: `midgard.collections.enums.gnss_freq_E`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Galileo frequencies in Hz

### **gnss_freq_G**

Full name: `midgard.collections.enums.gnss_freq_G`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

GPS frequencies in Hz

### **gnss_freq_I**

Full name: `midgard.collections.enums.gnss_freq_I`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

IRNSS frequencies in Hz

### **gnss_freq_J**

Full name: `midgard.collections.enums.gnss_freq_J`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

QZSS frequencies in Hz

### **gnss_freq_S**

Full name: `midgard.collections.enums.gnss_freq_S`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

SBAS frequencies in Hz

### **gnss_id_to_3digit_id**

Full name: `midgard.collections.enums.gnss_id_to_3digit_id`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

RINEX GNSS RINEX identifier to GNSS 3-digit identifier

### **gnss_id_to_name**

Full name: `midgard.collections.enums.gnss_id_to_name`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

RINEX GNSS identifier to GNSS name

### **gnss_id_to_reference_system**

Full name: `midgard.collections.enums.gnss_id_to_reference_system`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

RINEX GNSS RINEX identifier to relevant GNSS reference system name

### **gnss_name_to_id**

Full name: `midgard.collections.enums.gnss_name_to_id`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

GNSS name to RINEX GNSS identifier

### **gnss_num2freq_C**

Full name: `midgard.collections.enums.gnss_num2freq_C`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **gnss_num2freq_E**

Full name: `midgard.collections.enums.gnss_num2freq_E`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **gnss_num2freq_G**

Full name: `midgard.collections.enums.gnss_num2freq_G`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **gnss_num2freq_I**

Full name: `midgard.collections.enums.gnss_num2freq_I`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **gnss_num2freq_J**

Full name: `midgard.collections.enums.gnss_num2freq_J`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **gnss_num2freq_R**

Full name: `midgard.collections.enums.gnss_num2freq_R`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **gnss_num2freq_S**

Full name: `midgard.collections.enums.gnss_num2freq_S`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

An enumeration.

### **has_value**()

Full name: `midgard.collections.enums.has_value`

Signature: `(name: str, value: str) -> bool`

Check whether a named Enumeration defines a given value

**Args:**

- `name`:     Name used for Enumeration.
- `value`:    Value of Enumeration.

**Returns:**

True if Enumeration defines value, False otherwise


### **log_color**

Full name: `midgard.collections.enums.log_color`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Colors used when logging

### **log_level**

Full name: `midgard.collections.enums.log_level`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Levels used when deciding how much log output to show

### **ref_sys_name_to_epsg**

Full name: `midgard.collections.enums.ref_sys_name_to_epsg`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Reference system name to EPSG code

### **register_enum**()

Full name: `midgard.collections.enums.register_enum`

Signature: `(name: str) -> Callable[[enum.EnumMeta], enum.EnumMeta]`

Register a named Enumeration

This allows for getting Enumerations with the get_enum-function.

**Args:**

- `name`:  Name used for Enumeration.

**Returns:**

Decorator that registers an Enumeration.


### **write_level**

Full name: `midgard.collections.enums.write_level`

Signature: `(value, names=None, *, module=None, qualname=None, type=None, start=1)`

Levels used when deciding which fields of a dataset and other information to write to disk

## midgard.collections.plate_motion_models
Dataclass for handling tectonic plate motion models

**Description:**

You can add your own tectonic plate motion models via adding at the end of file:
    
    <model name> = PlateMotionModel(
                    name: <model name>
                    description: <model description>
                    pole: <List with rotation pole definitions for different tectonics plate>
    )


**Example:**

import numpy as np
from midgard.collections import plate_motion_models

# Get list with available plate models
models = 


# Get PlateMotionModel instance for a given tectonic name
model = plate_motion_models.get("itrf2014")

# Get RotationPole object for Eurasian tectonic plate
pole = model.get_pole("eura", unit="radian per year")

# Determine station velocity for given station position
pos = np.array([2102928.189605, 721619.617278, 5958196.398820])
pole_vec = [pole.wx, pole.wy, pole.wz]
vel = np.cross(pole_vec, pos)


### **PlateMotionModel**

Full name: `midgard.collections.plate_motion_models.PlateMotionModel`

Signature: `(name: str, description: str, poles: Dict[str, object]) -> None`

Dataclass for plate motion model

**Attributes:**

- `name`:        Name of plate motion model
- `description`: Description of plate motion model
- `poles`:       Dictionary with rotation pole definition for defined tectonic plates


### **RotationPole**

Full name: `midgard.collections.plate_motion_models.RotationPole`

Signature: `(name: str, wx: float, wy: float, wz: float, dwx: float, dwy: float, dwz: float, unit: str, description: str) -> None`

Dataclass for plate motion model

**Attributes:**

- `name`:           Name of tectonic plate
wx, wy, wx:     Rotation pole (angular velocity) components
dwx, dwy, dwz:  Standard deviation of rotation pole components
- `unit`:           Unit of rotation pole entries
- `description`:    Description of tectonic plate


### **get**()

Full name: `midgard.collections.plate_motion_models.get`

Signature: `(model: str) -> 'PlateMotionModel'`

Get a tectonic plate motion model by name

**Args:**

- `model`: Plate motion model name

**Returns:**

Instance of PlateMotionModel dataclass


### itrf2008 (PlateMotionModel)
`itrf2008 = PlateMotionModel(name='itrf2008', description='ITRF2008 plate motion model', poles={'amur': RotationPole(name='amur', wx=-0.19, wy=-0.442, wz=0.915, dwx=0.04, dwy=0.051, dwz=0.049, unit='milliarcsecond per year', description='Amurian plate'), 'anta': RotationPole(name='anta', wx=-0.252, wy=-0.302, wz=0.643, dwx=0.008, dwy=0.006, dwz=0.009, unit='milliarcsecond per year', description='Antarctic plate'), 'arab': RotationPole(name='arab', wx=1.202, wy=-0.054, wz=1.485, dwx=0.082, dwy=0.1, dwz=0.063, unit='milliarcsecond per year', description='Arabian plate'), 'aust': RotationPole(name='aust', wx=1.504, wy=1.172, wz=1.228, dwx=0.007, dwy=0.007, dwz=0.007, unit='milliarcsecond per year', description='Australian plate'), 'carb': RotationPole(name='carb', wx=0.049, wy=-1.088, wz=0.664, dwx=0.201, dwy=0.417, dwz=0.146, unit='milliarcsecond per year', description='Caribbean plate'), 'eura': RotationPole(name='eura', wx=-0.083, wy=-0.534, wz=0.775, dwx=0.008, dwy=0.007, dwz=0.008, unit='milliarcsecond per year', description='Eurasian plate'), 'indi': RotationPole(name='indi', wx=1.232, wy=0.303, wz=1.54, dwx=0.031, dwy=0.128, dwz=0.03, unit='milliarcsecond per year', description='Indian plate'), 'nazc': RotationPole(name='nazc', wx=-0.333, wy=-1.551, wz=1.625, dwx=0.011, dwy=0.029, dwz=0.013, unit='milliarcsecond per year', description='Nazca plate'), 'noam': RotationPole(name='noam', wx=0.035, wy=-0.662, wz=-0.1, dwx=0.008, dwy=0.009, dwz=0.008, unit='milliarcsecond per year', description='North American plate'), 'nubi': RotationPole(name='nubi', wx=0.095, wy=-0.598, wz=0.723, dwx=0.009, dwy=0.007, dwz=0.009, unit='milliarcsecond per year', description='Nubia plate'), 'pcfc': RotationPole(name='pcfc', wx=-0.411, wy=1.036, wz=-2.166, dwx=0.007, dwy=0.007, dwz=0.009, unit='milliarcsecond per year', description='Pacific plate'), 'soam': RotationPole(name='soam', wx=-0.243, wy=-0.311, wz=-0.154, dwx=0.009, dwy=0.01, dwz=0.009, unit='milliarcsecond per year', description='South American plate'), 'soma': RotationPole(name='soma', wx=-0.08, wy=-0.745, wz=0.897, dwx=0.028, dwy=0.03, dwz=0.012, unit='milliarcsecond per year', description='Somali plate')})`


### itrf2014 (PlateMotionModel)
`itrf2014 = PlateMotionModel(name='itrf2014', description='ITRF2014 plate motion model', poles={'anta': RotationPole(name='anta', wx=-0.248, wy=-0.324, wz=0.675, dwx=0.004, dwy=0.004, dwz=0.008, unit='milliarcsecond per year', description='Antarctic plate'), 'arab': RotationPole(name='arab', wx=1.154, wy=-0.136, wz=1.444, dwx=0.02, dwy=0.022, dwz=0.014, unit='milliarcsecond per year', description='Arabian plate'), 'aust': RotationPole(name='aust', wx=1.51, wy=1.182, wz=1.215, dwx=0.004, dwy=0.004, dwz=0.004, unit='milliarcsecond per year', description='Australian plate'), 'eura': RotationPole(name='eura', wx=-0.085, wy=-0.531, wz=0.77, dwx=0.004, dwy=0.002, dwz=0.005, unit='milliarcsecond per year', description='Eurasian plate'), 'indi': RotationPole(name='indi', wx=1.154, wy=-0.005, wz=1.454, dwx=0.027, dwy=0.117, dwz=0.035, unit='milliarcsecond per year', description='Indian plate'), 'nazc': RotationPole(name='nazc', wx=-0.333, wy=-1.544, wz=1.623, dwx=0.006, dwy=0.015, dwz=0.007, unit='milliarcsecond per year', description='Nazca plate'), 'noam': RotationPole(name='noam', wx=0.024, wy=-0.694, wz=-0.063, dwx=0.002, dwy=0.005, dwz=0.004, unit='milliarcsecond per year', description='North American plate'), 'nubi': RotationPole(name='nubi', wx=0.099, wy=-0.614, wz=0.733, dwx=0.004, dwy=0.003, dwz=0.003, unit='milliarcsecond per year', description='Nubia plate'), 'pcfc': RotationPole(name='pcfc', wx=-0.409, wy=1.047, wz=-2.169, dwx=0.003, dwy=0.004, dwz=0.004, unit='milliarcsecond per year', description='Pacific plate'), 'soam': RotationPole(name='soam', wx=-0.27, wy=-0.301, wz=-0.14, dwx=0.006, dwy=0.006, dwz=0.003, unit='milliarcsecond per year', description='South American plate'), 'soma': RotationPole(name='soma', wx=-0.121, wy=-0.794, wz=0.884, dwx=0.035, dwy=0.034, dwz=0.008, unit='milliarcsecond per year', description='Somali plate')})`


### **models**()

Full name: `midgard.collections.plate_motion_models.models`

Signature: `() -> List[str]`

Get a list of available tectonic plate motion models

**Returns:**

List of available tectonic plate motion models



### nnr_morvel56 (PlateMotionModel)
`nnr_morvel56 = PlateMotionModel(name='nnr_morvel56', description='NNR-MORVEL56 plate motion model', poles={'amur': RotationPole(name='amur', wx=-0.26156, wy=-0.40555, wz=0.9541, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Amurian plate'), 'anta': RotationPole(name='anta', wx=-0.17639, wy=-0.33021, wz=0.81844, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Antarctic plate'), 'arab': RotationPole(name='arab', wx=1.30893, wy=-0.19539, wz=1.51601, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Arabian plate'), 'aust': RotationPole(name='aust', wx=1.49003, wy=1.16163, wz=1.26766, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Australian plate'), 'capr': RotationPole(name='capr', wx=1.43757, wy=0.61288, wz=1.53251, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Capricorn plate'), 'carb': RotationPole(name='carb', wx=-0.03846, wy=-0.84045, wz=0.59349, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Caribbean plate'), 'coco': RotationPole(name='coco', wx=-2.16738, wy=-3.17607, wz=1.95327, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Cocos plate'), 'eura': RotationPole(name='eura', wx=-0.15004, wy=-0.50651, wz=0.6045, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Eurasian plate'), 'indi': RotationPole(name='indi', wx=1.24706, wy=-0.07169, wz=1.50832, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Indian plate'), 'juan': RotationPole(name='juan', wx=1.34157, wy=2.32742, wz=-2.12234, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Juan de Fuca plate'), 'lwan': RotationPole(name='lwan', wx=0.22233, wy=-0.59528, wz=0.81012, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Lwandle plate'), 'macq': RotationPole(name='macq', wx=2.64169, wy=0.51589, wz=3.11714, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Macquarie plate'), 'nazc': RotationPole(name='nazc', wx=-0.33251, wy=-1.70109, wz=1.80935, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Nazca plate'), 'noam': RotationPole(name='noam', wx=0.12193, wy=-0.73972, wz=-0.06361, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='North American plate'), 'nubi': RotationPole(name='nubi', wx=0.26008, wy=-0.65822, wz=0.77725, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Nubia plate'), 'pcfc': RotationPole(name='pcfc', wx=-0.43574, wy=0.94737, wz=-2.09883, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Pacific plate'), 'phil': RotationPole(name='phil', wx=1.94255, wy=-1.18388, wz=-2.35735, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Philippine Sea plate'), 'rive': RotationPole(name='rive', wx=-4.55332, wy=-14.62801, wz=5.65195, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Rivera plate'), 'sand': RotationPole(name='sand', wx=3.39908, wy=-2.54932, wz=-2.44715, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Sandwich plate'), 'scot': RotationPole(name='scot', wx=-0.13505, wy=-0.46636, wz=0.20131, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Scotia plate'), 'soam': RotationPole(name='soam', wx=0.07499, wy=-0.78168, wz=0.9342, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='South American plate'), 'soma': RotationPole(name='soma', wx=-0.14054, wy=-0.33384, wz=-0.15092, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Somali plate'), 'sund': RotationPole(name='sund', wx=-0.06815, wy=-0.77587, wz=0.93018, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Sunda plate'), 'sur_': RotationPole(name='sur_', wx=-0.11812, wy=-0.30264, wz=-0.20697, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Sur plate'), 'yang': RotationPole(name='ynag', wx=-0.24434, wy=-0.48751, wz=1.07163, dwx=nan, dwy=nan, dwz=nan, unit='milliarcsecond per year', description='Yangtze plate')})`
