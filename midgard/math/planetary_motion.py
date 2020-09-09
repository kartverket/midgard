#!/usr/bin/env python3
"""Midgard library for planetary motion

Example:
--------

    from migard.math import planetary_motion
"""


# Standard library imports
from typing import Tuple

# Third party imports
import numpy as np

# Midgard imports
from midgard.math import rotation


def findsun(time: "Time") -> np.ndarray:
    """Obtains the position vector of the Sun in relation to Earth (in ECEF).

    This routine is a reimplementation of routine findSun() in model.c of gLAB 3.0.0 software. The gLAB 3.0.0 software
    core excecutables are distributed under the Apache License version 2.0 related to following copyright and license:

    COPYRIGHT 2009 - 2016 GAGE/UPC & ESA

    LICENSED UNDER THE APACHE LICENSE, VERSION 2.0 (THE "LICENSE"); YOU MAY NOT USE THIS ROUTINE EXCEPT IN COMPLIANCE 
    WITH THE LICENSE. YOU MAY OBTAIN A COPY OF THE LICENSE AT

    HTTP://WWW.APACHE.ORG/LICENSES/LICENSE-2.0

    UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING, SOFTWARE DISTRIBUTED UNDER THE LICENSE IS DISTRIBUTED ON 
    AN "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED. SEE THE LICENSE FOR THE 
    SPECIFIC LANGUAGE GOVERNING PERMISSIONS AND LIMITATIONS UNDER THE LICENSE.

    Args:
        time:    Time object

    Returns:
        Sun position vector given in ECEF [m]
    """
    AU = 1.495_978_70e8
    gstr, slong, sra, sdec = gsdtime_sun(time)

    sun_pos_x = np.cos(np.deg2rad(sdec)) * np.cos(np.deg2rad(sra)) * AU
    sun_pos_y = np.cos(np.deg2rad(sdec)) * np.sin(np.deg2rad(sra)) * AU
    sun_pos_z = np.sin(np.deg2rad(sdec)) * AU
    sun_pos_eci = np.vstack((sun_pos_x, sun_pos_y, sun_pos_z)).T

    # Rotate from inertial to non inertial system (ECI to ECEF)
    sun_pos_ecef = np.squeeze(rotation.R3(np.deg2rad(gstr)) @ sun_pos_eci.T)

    return sun_pos_ecef


def gsdtime_sun(time: "Time") -> Tuple[np.ndarray]:
    """Get position of the sun (low-precision)

    This routine is a reimplementation of routine GSDtime_sun() in model.c of gLAB 3.0.0 software. The gLAB 3.0.0 
    software core excecutables are distributed under the Apache License version 2.0 related to following copyright and 
    license:

    COPYRIGHT 2009 - 2016 GAGE/UPC & ESA

    LICENSED UNDER THE APACHE LICENSE, VERSION 2.0 (THE "LICENSE"); YOU MAY NOT USE THIS ROUTINE EXCEPT IN COMPLIANCE 
    WITH THE LICENSE. YOU MAY OBTAIN A COPY OF THE LICENSE AT

    HTTP://WWW.APACHE.ORG/LICENSES/LICENSE-2.0

    UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING, SOFTWARE DISTRIBUTED UNDER THE LICENSE IS DISTRIBUTED ON 
    AN "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED. SEE THE LICENSE FOR THE 
    SPECIFIC LANGUAGE GOVERNING PERMISSIONS AND LIMITATIONS UNDER THE LICENSE.

    Args:
        time:    Time object

    Returns:
        Tuple with following entries:

    | Elements  |   Description                                |
    |-----------|----------------------------------------------|
    | gstr      | GMST0 (to go from ECEF to inertial) [deg]    |
    | slong     | Sun longitude [deg]                          |
    | sra       | Sun right Ascension [deg]                    |
    | sdec      | Sun declination in [deg]                     |
    """
    jd = time.mjd_int - 15019.5
    frac = time.jd_frac
    vl = np.mod(279.696_678 + 0.985_647_335_4 * jd, 360)
    gstr = np.mod(279.690_983 + 0.985_647_335_4 * jd + 360 * frac + 180, 360)
    g = np.deg2rad(np.mod(358.475_845 + 0.985_600_267 * jd, 360))

    slong = vl + (1.91946 - 0.004_789 * jd / 36525) * np.sin(g) + 0.020_094 * np.sin(2 * g)
    obliq = np.deg2rad(23.45229 - 0.013_012_5 * jd / 36525)

    slp = np.deg2rad(slong - 0.005_686)
    sind = np.sin(obliq) * np.sin(slp)
    cosd = np.sqrt(1 - sind * sind)
    sdec = np.rad2deg(np.arctan2(sind, cosd))

    sra = 180 - np.rad2deg(np.arctan2(sind / cosd / np.tan(obliq), -np.cos(slp) / cosd))

    return gstr, slong, sra, sdec
