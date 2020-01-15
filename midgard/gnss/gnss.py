#!/usr/bin/env python3
"""Midgard library module including functions for GNSS modeling

Example:
--------

    from migard.gnss import gnss

Description:
------------

This module will provide functions for GNSS modeling.
"""
# Standard library imports
import pathlib
from typing import Tuple

# External library imports
import numpy as np

# Midgard imports
from midgard.dev import log
from midgard.files import files


def get_rinex_file_version(file_path: pathlib.PosixPath) -> str:
    """ Get RINEX file version for a given file key

    Args:
        file_path:  File path to broadcast orbit file.
        
    Returns:
        RINEX file version

    """
    with files.open(file_path, mode="rt") as infile:
        try:
            version = infile.readline().split()[0]
        except IndexError:
            log.fatal(f"Could not find Rinex version in file {file_path}")

    return version


# TODO: This should be removed and replaced by Time class.
def gpssec2jd(wwww: float, sec: float) -> Tuple[float, ...]:
    """Conversion from GPS week and second to Julian Date (JD)

    Args:
        wwww: GPS week
        sec:  GPS second

    Returns:
        tuple:         with following elements

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | jd_day               | Julian day                                                                           |
    | jd_frac              | Fractional part of Julian day                                                        |

    """
    sec_of_day = 86400.0
    jd_1980_01_06 = 2_444_244  # Julian date of 6-Jan-1980 + 0.5 d

    # .. Determine GPS day
    wd = np.floor((sec + 43200.0) / 3600.0 / 24.0)  # 0.5 d = 43200.0 s

    # .. Determine remainder
    fracSec = sec + 43200.0 - wd * 3600.0 * 24.0

    # .. Conversion GPS week and day to from Julian Date (JD)
    jd_day = wwww * 7.0 + wd + jd_1980_01_06
    jd_frac = fracSec / sec_of_day

    return jd_day, jd_frac
