"""Array with positions
"""

from typing import Any

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import _position
from midgard.math import transformation


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
    return _position.PositionArray.create(val, system, **pos_args)


def PositionDelta(
    val: np.ndarray, system: str, ref_pos: _position.PositionArray, **delta_args: Any
) -> _position.PositionDeltaArray:
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
    return _position.PositionDeltaArray.create(val, system, ref_pos, **delta_args)


def PosVel(val: np.ndarray, system: str, **pos_args: Any) -> "PosVelArray":
    """Factory for creating PosVelArrays for different systems

    See each position class for exact optional parameters.

    Args:
        val:       Array of position values.
        system:    Name of position system.
        pos_args:  Additional arguments used to create the PosVelArray.

    Returns:
        Array with positions in the given system.
    """
    return _position.PosVelArray.create(val, system, **pos_args)


def PosVelDelta(
    val: np.ndarray, system: str, ref_pos: _position.PosVelArray, **delta_args: Any
) -> _position.PosVelDeltaArray:
    """Factory for creating PosVelArrays for different systems

    See each position class for exact optional parameters.

    Args:
        val:         Array of position values.
        system:      Name of position system.
        ref_pos:     Reference position.
        delta_args:  Additional arguments used to create the PosVelArray.

    Returns:
        Array with positions in the given system.
    """
    return _position.PosVelDeltaArray.create(val, system, ref_pos, **delta_args)


#
# Attributes
#
_position.register_attribute(_position.PosVelArray, "other", _position.PosVelArray)
_position.register_attribute(_position.PositionArray, "other", _position.PositionArray)

#
# Position systems
#
@_position.register_system(convert_to=dict(llh=transformation.trs2llh))
class TrsPosition(_position.PositionArray):

    system = "trs"
    column_names = ("x", "y", "z")
    _units = ("meter", "meter", "meter")


@_position.register_system(convert_to=dict(trs=transformation.llh2trs))
class LlhPosition(_position.PositionArray):

    system = "llh"
    column_names = ("lat", "lon", "height")
    _units = ("radians", "radians", "meter")


#
# Position delta systems
#
@_position.register_system(convert_to=dict(enu=transformation.delta_trs2enu))
class TrsPositionDelta(_position.PositionDeltaArray):

    system = "trs"
    column_names = ("x", "y", "z")
    _units = ("meter", "meter", "meter")


@_position.register_system(convert_to=dict(trs=transformation.delta_enu2trs))
class EnuPositionDelta(_position.PositionDeltaArray):

    system = "enu"
    column_names = ("east", "north", "up")
    _units = ("meter", "meter", "meter")


#
# Velocity systems
#
@_position.register_system(convert_to=dict())
class TrsVelocity(_position.VelocityArray):

    system = "trs"
    column_names = ("x", "y", "z")
    _units = ("meter/second", "meter/second", "meter/second")


#
# Velocity delta systems
#
@_position.register_system(convert_to=dict(enu=transformation.delta_trs2enu))
class TrsVelocityDelta(_position.VelocityDeltaArray):

    system = "trs"
    column_names = ("x", "y", "z")
    _units = ("meter/second", "meter/second", "meter/second")


@_position.register_system(convert_to=dict(trs=transformation.delta_enu2trs))
class EnuVelocityDelta(_position.VelocityDeltaArray):

    system = "enu"
    column_names = ("veast", "vnorth", "vup")
    _units = ("meter/second", "meter/second", "meter/second")


#
# PosVel systems
#
@_position.register_system(convert_to=dict())
class TrsPosVel(_position.PosVelArray):

    system = "trs"
    column_names = ("x", "y", "z", "vx", "vy", "vz")
    _units = ("meter", "meter", "meter", "meter/second", "meter/second", "meter/second")


#
# PosVelDelta systems
#
@_position.register_system(convert_to=dict(enu=transformation.delta_trs2enu_posvel))
class TrsPosVelDelta(_position.PosVelDeltaArray):

    system = "trs"
    column_names = ("x", "y", "z", "vx", "vy", "vz")
    _units = ("meter", "meter", "meter", "meter", "meter", "meter")


@_position.register_system(convert_to=dict(trs=transformation.delta_enu2trs_posvel))
class EnuPosVelDelta(_position.PosVelDeltaArray):

    system = "enu"
    column_names = ("east", "north", "up", "veast", "vnorth", "vup")
    _units = ("meter", "meter", "meter", "meter/second", "meter/second", "meter/second")
