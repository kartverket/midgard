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
from midgard.collections import enums
from midgard.dev import log
from midgard.files import files


def obstype_to_freq(sys: str, obstype: str) -> float:
    """Get GNSS frequency based on given GNSS observation type

    Args:
        sys:     GNSS identifier (e.g. 'E', 'G', ...)
        obstype: Observation type (e.g. 'L1', 'P1', 'C1X', ...)

    Return:
        GNSS frequency in [Hz]
    """
    try:
        freq = getattr(enums, "gnss_freq_" + sys)[getattr(enums, "gnss_num2freq_" + sys)["f" + obstype[1]]]
    except KeyError:
        log.fatal(f"Frequency for GNSS '{sys}' and observation type '{obstype}' is not defined.")

    return freq


def get_number_of_satellites(systems: np.ndarray, satellites: np.ndarray, epochs: np.ndarray) -> np.ndarray:
    """Get number of satellites per epoch

    Args:
        satellites:     Array with satellite PRN number together with GNSS identifier (e.g. G07)
        systems:        Array with GNSS identifiers (e.g. G, E, R, ...)
        epochs:         Array with observation epochs (e.g. as datetime objects)

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
