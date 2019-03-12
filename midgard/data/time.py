"""Array with time epochs
"""

from typing import Optional

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import _time_scales  # noqa
from midgard.data._time import TimeArray

# from midgard.data._position_delta import PositionDeltaArray


def Time(
    val: np.ndarray,
    scale: str,
    format: str,
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
        format:  Format of values given in val and val2.

    Returns:
        Array with epochs in the given time scale and format
    """
    return TimeArray.create(val=val, val2=val2, scale=scale, format=format, _jd1=_jd1, _jd2=_jd2)


# Make classmethods available
Time.FORMATS = TimeArray.FORMATS  # Todo?
Time.SCALES = TimeArray.SCALES
Time.now = TimeArray.now
