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


def get_number_of_satellites(systems: np.ndarray, satellites: np.ndarray, epochs: np.ndarray) -> np.ndarray:
    """Get number of satellites per epoch

    Args:
        satellites:     Array with satellite PRN number together with GNSS identifier (e.g. G07)
        systems:        Array with GNSS identifiers (e.g. G, E, R, ...)
        epochs:         Array with observation epochs

    Returns:
        Number of satellites per epoch
    """
    num_satellite = np.zeros((len(systems)))

    for sys in set(systems):
        idx_sys = systems == sys
        num_satellite_epoch = np.zeros((len(systems[idx_sys])))

        for epoch in set(epochs):
            idx = epochs[idx_sys] == epoch
            num_satellite_epoch[idx] = len(satellites[idx_sys][idx])

        num_satellite[idx_sys] = num_satellite_epoch

    return num_satellite


def get_rinex_file_version(file_path: pathlib.PosixPath) -> str:
    """ Get RINEX file version for a given file path

    Args:
        file_path:  File path.
        
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
