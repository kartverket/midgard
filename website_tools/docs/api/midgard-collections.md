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