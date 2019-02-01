"""Time scales and conversions between them

"""
# Standard library imports
from typing import Any, Callable, Dict, List, Tuple

# Third party imports
import numpy as np

# Midgard imports
from midgard.data._time import TimeArray, register_scale
from midgard.math.unit import Unit


#
# Time scale conversions
#
def _utc2tai(utc_jd1, utc_jd2):
    """Convert UTC to TAI"""
    return utc_jd1, utc_jd2


def _tai2utc(tai_jd1, tai_jd2):
    """Convert TAI to UTC"""
    return tai_jd1, tai_jd2


def _tai2tt(tai_jd1, tai_jd2):
    """Convert TAI to UTC"""
    delta = 32.184 * Unit.seconds2day
    return tai_jd1, tai_jd2 + delta


def _tt2tai(tt_jd1, tt_jd2):
    """Convert TT to TAI"""
    delta = 32.184 * Unit.seconds2day
    return tt_jd1, tt_jd2 - delta


def _gps2tai(gps_jd1, gps_jd2):
    """Convert GPS time scale to TAI

    Args:
        gps_jd1:  Float, part 1 of 'gps'-time as a two-part Julian Day.
        gps_jd2:  Float, part 2 of 'gps'-time as a two-part Julian Day.

    Returns:
        2-tuple of floats representing 'tai' as a two-part Julian Day.
    """
    delta = 19 * Unit.seconds2day
    return gps_jd1, gps_jd2 + delta


def _tai2gps(tai_jd1, tai_jd2):
    """Convert from TAI to GPS time scale

    Args:
        tai_jd1:  Float, part 1 of 'tai'-time as a two-part Julian Day.
        tai_jd2:  Float, part 2 of 'tai'-time as a two-part Julian Day.

    Returns:
        2-tuple of floats representing 'gps' as a two-part Julian Day.
    """
    delta = 19 * Unit.seconds2day
    return tai_jd1, tai_jd2 - delta


#
# Time scales
#
@register_scale(convert_to=dict(tai=_utc2tai))
class UtcTime(TimeArray):

    scale = "utc"


@register_scale(convert_to=dict(utc=_tai2utc, tt=_tai2tt, gps=_tai2gps))
class TaiTime(TimeArray):

    scale = "tai"


@register_scale(convert_to=dict(tai=_gps2tai))
class GpsTime(TimeArray):

    scale = "gps"


@register_scale(convert_to=dict(tai=_tt2tai))
class TtTime(TimeArray):

    scale = "tt"
