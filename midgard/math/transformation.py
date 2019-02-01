"""Midgard library module for handling of geodetic conversions

Description:
------------

"""

# Standard library imports
from collections import namedtuple

# Third party imports
import numpy as np

# Midgard imports
# from midgard.dev import cache  # TODO
from midgard.math import ellipsoid


# Todo: Move ellipsoid to its own module: math.ellipsoid, implement b, e2 etc as properties
Ellipsoid = namedtuple("Ellipsoid", ("name", "a", "f"))
WGS72 = Ellipsoid(name="WGS72", a=6378135, f=1 / 298.26)
WGS84 = Ellipsoid(name="WGS84", a=6378137, f=1 / 298.257223563)
GRS80 = Ellipsoid(name="GRS80", a=6378137, f=1 / 298.257222101)


def trs2llh(trs: np.ndarray, ellipsoid: ellipsoid.Ellipsoid = ellipsoid.GRS80) -> np.ndarray:
    """Convert geocentric xyz-coordinates to geodetic latitude-, longitude-, height-coordinates

    Ref: Datums and Map projections, Jonathan Iliffe and Roger Lott, section 2.2.4
    """
    trs = np.asarray(trs)
    if trs.ndim < 1 or trs.ndim > 2 or trs.shape[-1] != 3:
        raise ValueError("'trs' must be a 1- or 2-dimensional array with 3 columns")

    x, y, z = trs.T

    p = np.sqrt(x ** 2 + y ** 2)  # Equation (2.12)
    u = np.arctan2(z * ellipsoid.a, p * ellipsoid.b)  # Equation (2.13)

    lon = np.arctan2(y, x)  # Equation (2.9)
    lat = np.arctan2(
        z + ellipsoid.eps * ellipsoid.b * np.sin(u) ** 3, p - ellipsoid.e2 * ellipsoid.a * np.cos(u) ** 3
    )  # Equation (2.10)
    v = ellipsoid.a / np.sqrt(1 - ellipsoid.e2 * np.sin(lat) ** 2)  # Equation (C.1)
    height = p / np.cos(lat) - v  # Equation (2.11)

    return np.stack((lat, lon, height)).T


def llh2trs(llh: np.ndarray, ellipsoid: ellipsoid.Ellipsoid = ellipsoid.GRS80) -> np.ndarray:
    """Convert geodetic latitude-, longitude-, height-coordinates to geocentric xyz-coordinates

    Ref: Datums and Map projections, Jonathan Iliffe and Roger Lott, section 2.2.4
    """
    llh = np.asarray(llh)
    if llh.ndim < 1 or llh.ndim > 2 or llh.shape[-1] != 3:
        raise ValueError("'llh' must be a 1- or 2-dimensional array with 3 columns")

    lat, lon, height = llh.T

    coslat, sinlat = np.cos(lat), np.sin(lat)
    coslon, sinlon = np.cos(lon), np.sin(lon)

    v = ellipsoid.a / np.sqrt(1 - ellipsoid.e2 * sinlat ** 2)  # Equation (C.1)
    x = (v + height) * coslat * coslon  # Equation (2.6)
    y = (v + height) * coslat * sinlon  # Equation (2.7)
    z = ((1 - ellipsoid.e2) * v + height) * sinlat  # Equation (2.8)

    return np.stack((x, y, z)).T
