"""Framework for working with enumerations

Description:
------------

Custom enumerations used for structured names. You can add your own enumerations in your own application by importing
`register_enum` and using that to register your own enums.

References:

[1] RINEX Version 3.04 (2018): RINEX The receiver independent exchange format version 3.04, November 23, 2018


Example:
--------

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
"""

# Standard library imports
import colorama
import enum
from typing import Any, Callable, Dict, List

# Midgard imports
from midgard.dev import exceptions


# Dictionary of Enumerations. Populated by the @register_enum-decorators.
_ENUMS: Dict[str, enum.EnumMeta] = dict()


class NotGiven:
    """Dummy class used as a marker for a argument not given, used instead of None because None is valid value"""

    pass


def register_enum(name: str) -> Callable[[enum.EnumMeta], enum.EnumMeta]:
    """Register a named Enumeration

    This allows for getting Enumerations with the get_enum-function.

    Args:
        name:  Name used for Enumeration.

    Returns:
        Decorator that registers an Enumeration.
    """

    def register_decorator(enum_cls: enum.EnumMeta) -> enum.EnumMeta:
        _ENUMS[name] = enum_cls
        globals()[name] = enum_cls
        return enum_cls

    return register_decorator


def enums() -> List[str]:
    """Return a list of available enums

    Returns:
        Names of available enums.
    """
    return sorted(_ENUMS)


def get_enum(name: str) -> enum.EnumMeta:
    """Return a named Enumeration

    Names are defined by the @register_enum-decorator. If the name-parameter is not a valid enum, the function will
    raise an UnknownEnumError and list the available enumerations.

    Args:
        name:  Name used for Enumeration.

    Returns:
        Enumeration with the given name.
    """
    try:
        return _ENUMS[name]
    except KeyError:
        valid_enums = ", ".join(e for e in _ENUMS)
        raise exceptions.UnknownEnumError(
            f"Enumeration '{name}' is not defined. Available enumerations are {valid_enums}."
        ) from None


def get_value(name: str, value: str, default: Any = NotGiven) -> enum.Enum:
    """Return the value of a named Enumeration

    Names are defined by the @register_enum-decorator.

    Args:
        name:     Name used for Enumeration.
        value:    Value of Enumeration.
        default:  Optional object returned if enumeration does not contain value

    Returns:
        Value of enumeration with the given name.
    """
    try:
        return get_enum(name)[value]
    except KeyError:
        if default is NotGiven:
            valid_values = ", ".join(v.name for v in get_enum(name))  # type: ignore
            raise ValueError(
                f"Value '{value}' is not valid for a {name}-enumeration. Valid values are {valid_values}."
            ) from None
        else:
            return default


def has_value(name: str, value: str) -> bool:
    """Check whether a named Enumeration defines a given value

    Args:
        name:     Name used for Enumeration.
        value:    Value of Enumeration.

    Returns:
        True if Enumeration defines value, False otherwise
    """
    return value in get_enum(name).__members__


#
# ENUMS
#
@register_enum("exit_status")
class ExitStatus(int, enum.Enum):
    """Exit status definition"""

    ok = 0
    warn = 1
    error = 2
    fatal = 3


@register_enum("log_level")
class LogLevel(int, enum.Enum):
    """Levels used when deciding how much log output to show"""

    all = enum.auto()
    debug = enum.auto()
    info = enum.auto()
    warn = enum.auto()
    error = enum.auto()
    fatal = enum.auto()
    none = enum.auto()


@register_enum("log_color")
class LogColor(str, enum.Enum):
    """Colors used when logging"""

    warn = colorama.Fore.YELLOW
    error = colorama.Fore.RED
    fatal = colorama.Style.BRIGHT + colorama.Fore.RED


@register_enum("write_level")
class WriteLevel(enum.IntEnum):
    """Levels used when deciding which fields of a dataset and other information to write to disk"""

    detail = enum.auto()
    analysis = enum.auto()
    operational = enum.auto()


## Define relation between GNSS frequency number and GNSS frequency name (RINEX format definition)
#
#  References: RINEX 3.04 format [1], section 5.1
#
# Overview over frequency number (1 .. 9) and observation code dependent on GNSS with the GNSS RINEX identifiers:
#
#  C = Beidou
#  E = Galileo
#  G = GPS
#  I = IRNSS
#  J = QZSS
#  S = SBAS
# __________________________________
#  freq |  C     E    G   I   J   S
# ______|___________________________
#   1   |  B1    E1   L1      L1  L1
#   2   |  B1_2       L2      L2
#   5   |  B2a   E5a  L5  L5  L5  L5
#   6   |  B3    E6           L6
#   7   |  B2b   E5b
#   8   |  B2    E5
#   9   |                 S
# ______|___________________________


@register_enum("gnss_num2freq_C")
class BeidouFreqNum2Freq(str, enum.Enum):
    f1 = "B1"
    f2 = "B1_2"
    f5 = "B2a"
    f6 = "B3"
    f7 = "B2b"
    f8 = "B2"


@register_enum("gnss_num2freq_E")
class GalileoFreqNum2Freq(str, enum.Enum):
    f1 = "E1"
    f5 = "E5a"
    f6 = "E6"
    f7 = "E5b"
    f8 = "E5"


@register_enum("gnss_num2freq_G")
class GpsFreqNum2Freq(str, enum.Enum):
    f1 = "L1"
    f2 = "L2"
    f5 = "L5"


@register_enum("gnss_num2freq_R")
class GlonassFreqNum2Freq(str, enum.Enum):
    f1 = "G1"
    f2 = "G2"
    f3 = "G3"
    f4 = "G1a"
    f6 = "G2a"


@register_enum("gnss_num2freq_I")
class IrnssFreqNum2Freq(str, enum.Enum):
    f5 = "L5"
    f9 = "S"


@register_enum("gnss_num2freq_J")
class QzssFreqNum2Freq(str, enum.Enum):
    f1 = "L1"
    f2 = "L2"
    f5 = "L5"
    f6 = "L6"


@register_enum("gnss_num2freq_S")
class SbasFreqNum2Freq(str, enum.Enum):
    f1 = "L1"
    f5 = "L5"


## GNSS frequencies
#
#  Unit: \f$ s^{-1} \f$.
#
#  References: RINEX 3.04 format [1], section 5.1
#
@register_enum("gnss_freq_C")
class BeidouFrequency(float, enum.Enum):
    """BeiDou frequencies in Hz"""

    B1 = f1 = 1575.42e6
    B1_2 = f2 = 1561.098e6
    B2a = f5 = 1176.45e6
    B2b = f7 = 1207.14e6
    B2 = f8 = 1191.795e6
    B3 = f6 = 1268.52e6


@register_enum("gnss_freq_E")
class GalileoFrequency(float, enum.Enum):
    """Galileo frequencies in Hz"""

    E1 = f1 = 1575.42e6
    E5 = f8 = 1191.795e6
    E5a = f5 = 1176.45e6
    E5b = f7 = 1207.140e6
    E6 = f6 = 1278.75e6


@register_enum("gnss_freq_G")
class GPSFrequency(float, enum.Enum):
    """GPS frequencies in Hz"""

    L1 = f1 = 1575.42e6
    L2 = f2 = 1227.60e6
    L5 = f5 = 1176.45e6


@register_enum("gnss_freq_I")
class IrnssFrequency(float, enum.Enum):
    """IRNSS frequencies in Hz"""

    L5 = f5 = 1176.45e6
    S = f9 = 2492.028e6


@register_enum("gnss_freq_J")
class QzssFrequency(float, enum.Enum):
    """QZSS frequencies in Hz"""

    L1 = f1 = 1575.42e6
    L2 = f2 = 1227.60e6
    L5 = f5 = 1176.45e6
    L6 = f6 = 1278.75e6


@register_enum("gnss_freq_S")
class SbasFrequency(float, enum.Enum):
    """SBAS frequencies in Hz"""

    L1 = f1 = 1575.42e6
    L5 = f5 = 1176.45e6


## RINEX GNSS identifier to GNSS name
#
#  References: RINEX 3.04 format [1], section 5.1
#
@register_enum("gnss_id_to_name")
class GnssIdToName(str, enum.Enum):
    """RINEX GNSS identifier to GNSS name"""

    C = "BeiDou"
    E = "Galileo"
    G = "GPS"
    I = "IRNSS"
    J = "QZSS"
    R = "GLONASS"
    S = "SBAS"


@register_enum("gnss_name_to_id")
class GnssNameToId(str, enum.Enum):
    """GNSS name to RINEX GNSS identifier"""

    beidou = "C"
    galileo = "E"
    gps = "G"
    irnss = "I"
    qzss = "J"
    glonass = "R"
    sbas = "S"


@register_enum("gnss_3digit_id_to_id")
class Gnss3DigitIdToId(str, enum.Enum):
    """RINEX GNSS 3-digit identifier to RINEX GNSS identifier"""

    BDS = "C"
    GAL = "E"
    GPS = "G"
    IRN = "I"
    QZS = "J"
    GLO = "R"


@register_enum("gnss_id_to_3digit_id")
class GnssIdTo3DigitId(str, enum.Enum):
    """RINEX GNSS RINEX identifier to GNSS 3-digit identifier"""

    C = "BDS"
    E = "GAL"
    G = "GPS"
    I = "IRN"
    J = "QZS"
    R = "GLO"


@register_enum("gnss_id_to_reference_system")
class GnssIdToReferenceSystem(str, enum.Enum):
    """RINEX GNSS RINEX identifier to relevant GNSS reference system name"""

    C = "cgcs2000"
    E = "gtrf"
    G = "wgs84"
    I = "wgs84"
    J = "jgs"
    R = "pz_90"


# Examples

# from midgard.collections import enums
# enums.get_value("gnss_freq_G", "L1")
# enums.get_value("gnss_freq_G", "L1") + 1

# enums.get_enum("gnss_freq_G")
# enums.get_enum("gnss_freq_G").L1
# enums.get_enum("gnss_freq_G").L1 + 1

# enums.gnss_freq_G.L1
# enums.gnss_freq_G.L1 * 2
