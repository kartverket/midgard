"""Array with time epochs
"""

from typing import Optional

# Third party imports
import numpy as np

# Midgard imports
from midgard.data._time import TimeArray, TimeDeltaArray


def Time(
    val: np.ndarray,
    scale: str,
    fmt: str,
    val2: Optional[np.ndarray] = None,
    _jd1: Optional[np.ndarray] = None,
    _jd2: Optional[np.ndarray] = None,
) -> "TimeArray":
    """Factory for creating TimeArrays for different systems

    See each time class for exact optional parameters.

    Args:
        val:     Array of time values.
        val2:    Optional second array for extra precision.
        scale:   Name of time scale.
        fmt:  Format of values given in val and val2.

    Returns:
        Array with epochs in the given time scale and format
    """
    return TimeArray.create(val=val, val2=val2, scale=scale, fmt=fmt, _jd1=_jd1, _jd2=_jd2)


def TimeDelta(val: np.ndarray, scale: str, fmt: str, val2: Optional[np.ndarray] = None) -> "TimeDeltaArray":
    """Factory for creating TimeArrays for different systems

    See each time class for exact optional parameters.

    Args:
        val:     Array of time values.
        val2:    Optional second array for extra precision.
        scale:   Name of time scale.
        fmt:  Format of values given in val and val2.

    Returns:
        Array with epochs in the given time scale and format
    """
    return TimeDeltaArray.create(val=val, val2=val2, scale=scale, fmt=fmt)


def is_time(val):
    try:
        return val.cls_name == "TimeArray"
    except AttributeError:
        return False


def is_timedelta(val):
    try:
        return val.cls_name == "TimeDeltaArray"
    except AttributeError:
        return False


# Make classmethods available
Time.now = TimeArray.now
Time.is_time = is_time
Time.is_timedelta = is_timedelta
