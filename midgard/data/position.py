"""Array with positions
"""

from typing import Any

# Third party imports
import numpy as np

# Midgard imports
from midgard.data._position import PositionArray
from midgard.data._position_delta import PositionDeltaArray


def Position(val: np.ndarray, system: str, **pos_args: Any) -> "PositionArray":
    """Factory for creating PositionArrays for different systems

    See each position class for exact optional parameters.

    Args:
        val:       Array of position values.
        system:    Name of position system.
        pos_args:  Additional arguments used to create the PositionArray.

    Returns:
        Array with positions in the given system.
    """
    return PositionArray.create(val, system, **pos_args)


def PositionDelta(val: np.ndarray, system: str, ref_pos: PositionArray, **delta_args: Any) -> PositionDeltaArray:
    """Factory for creating PositionArrays for different systems

    See each position class for exact optional parameters.

    Args:
        val:         Array of position values.
        system:      Name of position system.
        ref_pos:     Reference position.
        delta_args:  Additional arguments used to create the PositionArray.

    Returns:
        Array with positions in the given system.
    """
    return PositionDeltaArray.create(val, system, ref_pos, **delta_args)
