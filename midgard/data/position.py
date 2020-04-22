"""Array with positions
"""

from typing import Any

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import _position
from midgard.data._position import PositionArray, PositionDeltaArray, PosVelArray, PosVelDeltaArray
from midgard.math import transformation as trans


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


def PositionDelta(val: np.ndarray, system: str, ref_pos: "PositionArray", **delta_args: Any) -> "PositionDeltaArray":
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
    return PosVelArray.create(val, system, **pos_args)


def PosVelDelta(val: np.ndarray, system: str, ref_pos: "PosVelArray", **delta_args: Any) -> "PosVelDeltaArray":
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
    return PosVelDeltaArray.create(val, system, ref_pos, **delta_args)


def is_position(val):
    try:
        return val.cls_name == "PositionArray"
    except AttributeError:
        return False


def is_position_delta(val):
    try:
        return val.cls_name == "PositionDeltaArray"
    except AttributeError:
        return False


def is_posvel(val):
    try:
        return val.cls_name == "PosVelArray"
    except AttributeError:
        return False


def is_posvel_delta(val):
    try:
        return val.cls_name == "PosVelDeltaArray"
    except AttributeError:
        return False


#
# Attributes
#
_position.register_attribute(PosVelArray, "other")
_position.register_attribute(PositionArray, "other")

#
# Position systems
#
@_position.register_system(convert_to=dict(llh=trans.trs2llh))
class TrsPosition(PositionArray):

    system = "trs"
    column_names = ("x", "y", "z")
    _units = ("meter", "meter", "meter")


@_position.register_system(convert_to=dict(trs=trans.llh2trs))
class LlhPosition(PositionArray):

    system = "llh"
    column_names = ("lat", "lon", "height")
    _units = ("radians", "radians", "meter")


#
# Position delta systems
#
@_position.register_system(convert_to=dict(enu=trans.delta_trs2enu))
class TrsPositionDelta(PositionDeltaArray):

    system = "trs"
    column_names = ("x", "y", "z")
    _units = ("meter", "meter", "meter")


@_position.register_system(convert_to=dict(trs=trans.delta_enu2trs))
class EnuPositionDelta(PositionDeltaArray):

    system = "enu"
    column_names = ("east", "north", "up")
    _units = ("meter", "meter", "meter")


@_position.register_system(convert_to=dict())
class AcrPositionDelta(PositionDeltaArray):

    system = "acr"
    column_names = ("along", "cross", "radial")
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
@_position.register_system(convert_to=dict())
class TrsVelocityDelta(_position.VelocityDeltaArray):

    system = "trs"
    column_names = ("x", "y", "z")
    _units = ("meter/second", "meter/second", "meter/second")


@_position.register_system(convert_to=dict())
class EnuVelocityDelta(_position.VelocityDeltaArray):

    system = "enu"
    column_names = ("veast", "vnorth", "vup")
    _units = ("meter/second", "meter/second", "meter/second")


@_position.register_system(convert_to=dict())
class AcrVelocityDelta(_position.VelocityDeltaArray):

    system = "acr"
    column_names = ("valong", "vcross", "vradial")
    _units = ("meter/second", "meter/second", "meter/second")


#
# PosVel systems
#
@_position.register_system(convert_to=dict(kepler=trans.trs2kepler))
class TrsPosVel(PosVelArray):

    system = "trs"
    column_names = ("x", "y", "z", "vx", "vy", "vz")
    _units = ("meter", "meter", "meter", "meter/second", "meter/second", "meter/second")


@_position.register_system(convert_to=dict(trs=trans.kepler2trs))
class KeplerPosVel(PosVelArray):

    system = "kepler"
    column_names = ("a", "e", "i", "Omega", "omega", "E")
    _units = ("meter", "unitless", "radians", "radians", "radians", "radians")

    @property
    @_position.register_field(units=("radians",))
    def M(self):
        r"""Compute mean anomaly.

        Determination of mean anomaly is based on Eq. 2.65 in :cite:`montenbruck2012`.

        Returns:
            numpy.ndarray: Mean anomaly in [rad]
        """
        e = self.kepler.e
        E = self.kepler.E
        return E - e * np.sin(E)

    @property
    @_position.register_field(units=("radians",))
    def f(self):
        r"""Compute true anomaly.

        Determination of true anomaly is based on Eq. 2.67 in :cite:`montenbruck2012`.

        Returns:
            numpy.ndarray: True anomaly in [rad]
        """
        e = self.kepler.e
        E = self.kepler.E
        return np.arctan2(np.sqrt(1 - e ** 2) * np.sin(E), (np.cos(E) - e))


#
# PosVelDelta systems
#
@_position.register_system(convert_to=dict(enu=trans.delta_trs2enu_posvel, acr=trans.delta_trs2acr_posvel))
class TrsPosVelDelta(PosVelDeltaArray):

    system = "trs"
    column_names = ("x", "y", "z", "vx", "vy", "vz")
    _units = ("meter", "meter", "meter", "meter/second", "meter/second", "meter/second")


@_position.register_system(convert_to=dict(trs=trans.delta_enu2trs_posvel))
class EnuPosVelDelta(PosVelDeltaArray):

    system = "enu"
    column_names = ("east", "north", "up", "veast", "vnorth", "vup")
    _units = ("meter", "meter", "meter", "meter/second", "meter/second", "meter/second")


@_position.register_system(convert_to=dict(trs=trans.delta_acr2trs_posvel))
class AcrPosVelDelta(PosVelDeltaArray):

    system = "acr"
    column_names = ("along", "cross", "radial", "valong", "vcross", "vradial")
    _units = ("meter", "meter", "meter", "meter/second", "meter/second", "meter/second")
