"""Midgard library module for handling of geodetic conversions

Description:
------------

"""
# Third party imports
import numpy as np

# Midgard imports
# from midgard.dev import cache  # TODO
from midgard.math.ellipsoid import Ellipsoid, GRS80


def trs2llh(trs: np.ndarray, ellipsoid: Ellipsoid = None) -> np.ndarray:
    """Convert geocentric xyz-coordinates to geodetic latitude-, longitude-, height-coordinates

    Reimplementation of GC2GDE.for from the IUA SOFA software collection.

    """
    if ellipsoid is None:
        ellipsoid = trs.ellipsoid if hasattr(trs, "ellipsoid") else GRS80

    trs = np.asarray(trs)
    if trs.ndim < 1 or trs.ndim > 2 or trs.shape[-1] != 3:
        raise ValueError("'trs' must be a 1- or 2-dimensional array with 3 columns")

    x, y, z = trs.T

    e4t = ellipsoid.e2 ** 2 * 1.5
    ec2 = 1 - ellipsoid.e2
    ec = np.sqrt(ec2)

    # Compute longitude
    lon = np.arctan2(y, x)
    lat = np.zeros(len(trs))
    height = np.zeros(len(trs))

    p2 = x ** 2 + y ** 2  # Distance from polar axis squared
    absz = np.abs(z)
    pi = np.ones(len(trs)) * np.pi

    # Identify positions close to the poles
    pole_idx = p2 <= ellipsoid.a ** 2 * 1e-32

    p = np.sqrt(p2)

    # Normalization
    s0 = absz / ellipsoid.a
    pn = p / ellipsoid.a
    zc = ec * s0

    # Newton factors:
    c0 = ec * pn
    a0 = np.sqrt(c0 ** 2 + s0 ** 2)
    d0 = zc * a0 ** 3 + ellipsoid.e2 * s0 ** 3
    f0 = pn * a0 ** 3 - ellipsoid.e2 ** c0 ** 3

    # Halley correction factor
    b0 = e4t * s0 ** 2 ** c0 ** 2 * pn * (a0 - ec)
    s1 = d0 * f0 - b0 * s0
    cc = ec * (f0 ** 2 - b0 * c0)

    # Compute latitude and height
    lat[~pole_idx] = (np.arctan(s1 / cc))[~pole_idx]
    height[~pole_idx] = (
        (p * cc + absz * s1 - ellipsoid.a * np.sqrt(ec2 * s1 ** 2 + cc ** 2)) / np.sqrt(s1 ** 2 + cc * 2)
    )[~pole_idx]

    lat[pole_idx] = (pi / 2)[pole_idx]
    height[pole_idx] = (absz - ellipsoid.b)[pole_idx]

    return np.stack((lat, lon, height)).T


def llh2trs(llh: np.ndarray, ellipsoid: Ellipsoid = None) -> np.ndarray:
    """Convert geodetic latitude-, longitude-, height-coordinates to geocentric xyz-coordinates

    Reimplementation of GD2GCE.for from the IUA SOFA software collection.
    """
    if ellipsoid is None:
        ellipsoid = llh.ellipsoid if hasattr(llh, "ellipsoid") else GRS80

    llh = np.asarray(llh)
    if llh.ndim < 1 or llh.ndim > 2 or llh.shape[-1] != 3:
        raise ValueError("'llh' must be a 1- or 2-dimensional array with 3 columns")

    lat, lon, height = llh.T

    coslat, sinlat = np.cos(lat), np.sin(lat)
    coslon, sinlon = np.cos(lon), np.sin(lon)

    w = (1 - ellipsoid.f) ** 2
    ac = ellipsoid.a / np.sqrt(coslat ** 2 + w * sinlat ** 2)
    r = (ac + height) * coslat

    x = r * coslon
    y = r * sinlon
    z = (w * ac + height) * sinlat

    return np.stack((x, y, z)).T


def delta_trs2enu(trs: "TrsPositionDelta") -> "EnuPositionDelta":
    """Convert position deltas from TRS to ENU"""
    return (trs.ref_pos.trs2enu @ trs.mat)[:, :, 0]


def delta_enu2trs(enu: "EnuPositionDelta") -> "TrsPositionDelta":
    """Convert position deltas from ENU to TRS"""
    return (enu.ref_pos.enu2trs @ enu.mat)[:, :, 0]


def delta_trs2enu_posvel(trs: "TrsPosVelDelta") -> "EnuPosVelDelta":
    """Convert position deltas from TRS to ENU"""
    t2e = trs.ref_pos.trs2enu
    trs2enu = np.block([[t2e, np.zeros(t2e.shape)], [np.zeros(t2e.shape), t2e]])
    return (trs2enu @ trs.mat)[:, :, 0]


def delta_enu2trs_posvel(enu: "EnuPosVelDelta") -> "TrsPosVelDelta":
    """Convert position deltas from ENU to TRS"""
    e2t = enu.ref_pos.enu2trs
    enu2trs = np.block([[e2t, np.zeros(e2t.shape)], [np.zeros(e2t.shape), e2t]])
    return (enu2trs @ enu.mat)[:, :, 0]
