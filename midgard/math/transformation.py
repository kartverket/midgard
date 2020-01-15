"""Midgard library module for handling of geodetic conversions

Description:
------------

"""
# Standard library imports
from functools import lru_cache

# Third party imports
import numpy as np

# Midgard imports
from midgard.math import rotation
from midgard.math.constant import constant
from midgard.math.ellipsoid import Ellipsoid, GRS80
from midgard.math import nputil


def trs2llh(trs: np.ndarray, ellipsoid: Ellipsoid = None) -> np.ndarray:
    """Convert geocentric xyz-coordinates to geodetic latitude-, longitude-, height-coordinates

    Reimplementation of GC2GDE.for from the IUA SOFA software collection.

    """
    if ellipsoid is None:
        ellipsoid = trs.ellipsoid if hasattr(trs, "ellipsoid") else GRS80

    trs = nputil.HashArray(trs)
    if trs.ndim < 1 or trs.ndim > 2 or trs.shape[-1] != 3:
        raise ValueError("'trs' must be a 1- or 2-dimensional array with 3 columns")

    return _trs2llh(trs, ellipsoid)


@lru_cache()
def _trs2llh(trs: nputil.HashArray, ellipsoid: Ellipsoid) -> np.ndarray:
    x, y, z = trs.T

    e4t = ellipsoid.e2 ** 2 * 1.5
    ec2 = 1 - ellipsoid.e2
    ec = np.sqrt(ec2)

    # Compute longitude
    lon = np.arctan2(y, x)
    lat = np.zeros(len(trs)) if trs.ndim == 2 else 0
    height = np.zeros(len(trs)) if trs.ndim == 2 else 0

    p2 = x ** 2 + y ** 2  # Distance from polar axis squared
    absz = np.abs(z)
    pi = np.ones(len(trs)) * np.pi if trs.ndim == 2 else np.pi

    # Identify positions close to the poles
    pole_idx = p2 <= ellipsoid.a ** 2 * 1e-32

    p = np.sqrt(p2)

    # Normalization
    s0 = absz / ellipsoid.a
    pn = p / ellipsoid.a
    zc = ec * s0

    # Newton correction factors:
    c0 = ec * pn
    a0 = np.sqrt(c0 ** 2 + s0 ** 2)
    d0 = zc * a0 ** 3 + ellipsoid.e2 * s0 ** 3
    f0 = pn * a0 ** 3 - ellipsoid.e2 * c0 ** 3

    # Halley correction factor
    b0 = e4t * s0 ** 2 * c0 ** 2 * pn * (a0 - ec)
    s1 = d0 * f0 - b0 * s0
    cc = ec * (f0 ** 2 - b0 * c0)

    # Compute latitude and height
    tmp_lat = np.arctan(s1 / cc)
    tmp_height = (p * cc + absz * s1 - ellipsoid.a * np.sqrt(ec2 * s1 ** 2 + cc ** 2)) / np.sqrt(s1 ** 2 + cc ** 2)

    if trs.ndim == 2:
        lat[~pole_idx] = tmp_lat[~pole_idx]
        height[~pole_idx] = tmp_height[~pole_idx]

        lat[pole_idx] = (pi / 2)[pole_idx]
        height[pole_idx] = (absz - ellipsoid.b)[pole_idx]
    else:
        if pole_idx:
            lat = pi / 2
            height = absz - ellipsoid.b
        else:
            lat = tmp_lat
            height = tmp_height

    # Restore sign of latitude
    lat *= np.sign(z)

    return np.stack((lat, lon, height)).T


def llh2trs(llh: np.ndarray, ellipsoid: Ellipsoid = None) -> np.ndarray:
    """Convert geodetic latitude-, longitude-, height-coordinates to geocentric xyz-coordinates

    Reimplementation of GD2GCE.for from the IUA SOFA software collection.
    """
    if ellipsoid is None:
        ellipsoid = llh.ellipsoid if hasattr(llh, "ellipsoid") else GRS80

    llh = nputil.HashArray(llh)
    if llh.ndim < 1 or llh.ndim > 2 or llh.shape[-1] != 3:
        raise ValueError("'llh' must be a 1- or 2-dimensional array with 3 columns")

    return _llh2trs(llh, ellipsoid)


@lru_cache()
def _llh2trs(llh: nputil.HashArray, ellipsoid: Ellipsoid) -> np.ndarray:
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


def trs2kepler(trs: "TrsPosVel") -> "KeplerPosVel":
    """Compute Keplerian elements for elliptic orbit based on orbit position and velocity vector given in ITRS.

    The used equations are described in Section 2.2.4 in Montenbruck :cite:`montenbruck2012`.

    The position and velocity vector in ITRS and GM must be given in consistent units, which are [m], [m/s] and
    [m^3/s^2]. The resulting unit of the semimajor axis is implied by the unity of the position vector, i.e. [m].

    .. note::
    The function cannot be used with position/velocity vectors describing a circular or non-inclined orbit.

    Returns:
        tuple with numpy.ndarray types: Tuple with following Keplerian elements:

    ===============  ======  ==================================================================================
     Keys             Unit     Description
    ===============  ======  ==================================================================================
     a                m       Semimajor axis
     e                        Eccentricity of the orbit
     i                rad     Inclination
     Omega            rad     Right ascension of the ascending node
     omega            rad     Argument of perigee
     E                rad     Eccentric anomaly
    ===============  ======  ==================================================================================
    """
    r_norm = nputil.norm(trs.pos)  # Norm of position vector
    v_norm = nputil.norm(trs.vel)  # Norm of velocity vector

    # Normalized areal velocity (unit vector)
    h = np.cross(trs.pos, trs.vel)
    h_norm = nputil.norm(h)
    h_unit = nputil.unit_vector(h)
    h_x = nputil.take(h_unit, 0)
    h_y = nputil.take(h_unit, 1)
    h_z = nputil.take(h_unit, 2)

    i = np.arctan2(np.sqrt(h_x ** 2 + h_y ** 2), h_z)  # Inclination
    Omega = np.arctan2(h_x, -h_y)  # Right ascension of ascending node
    a = 1 / (2.0 / r_norm - v_norm ** 2 / constant.GM)  # Semi-major axis
    p = h_norm ** 2 / constant.GM  # Semi-latus rectum
    e = np.sqrt(1 - p / a)  # Eccentricity
    n = np.sqrt(constant.GM / a ** 3)  # Mean motion

    if trs.ndim == 1:
        einsum = np.einsum("i, i", trs.pos, trs.vel)
    else:
        einsum = np.einsum("ij, ij->i", trs.pos, trs.vel)

    E = np.arctan2(einsum, (a ** 2 * n) * (1 - r_norm / a))  # Eccentric anomaly
    vega = np.arctan2(np.sqrt(1 - e ** 2) * np.sin(E), (np.cos(E) - e))  # True anomaly
    u = np.arctan2(trs.pos.z, -trs.pos.x * h_y + trs.pos.y * h_x)  # Argument of latitude
    omega = u - vega  # Argument of perigee

    if trs.ndim == 1:
        if omega < 0:
            omega += 2 * np.pi
    else:
        omega[omega < 0] += 2 * np.pi

    return np.stack((a, e, i, Omega, omega, E)).T


def kepler2trs(kepler: "KeplerPosVel") -> "TrsPosVel":
    r"""Compute orbit position and velocity vector in geocentric equatorial coordinate system based on Keplerian
    elements for elliptic orbits.

    The implementation is based on Section 2.2.3 in :cite:`montenbruck2012`.

    """

    num_obs = 1 if kepler.ndim == 1 else len(kepler)
    cosE = np.cos(kepler.E)
    sinE = np.sin(kepler.E)
    fac = np.sqrt((1 - kepler.e) * (1 + kepler.e))
    r = kepler.a * (1 - kepler.e * cosE)  # Distance
    v = np.sqrt(constant.GM * kepler.a) / r  # Velocity

    # Transformation from spherical to cartesian orbital coordinate system
    r_orb = np.array([kepler.a * (cosE - kepler.e), kepler.a * fac * sinE, np.zeros(num_obs)])
    v_orb = np.array([-v * sinE, v * fac * cosE, np.zeros(num_obs)])

    # Transformation from cartesian orbital to geocentric equatorial coordinate system
    PQW = rotation.R3(-kepler.Omega) @ rotation.R1(-kepler.i) @ rotation.R3(-kepler.omega)
    R = np.squeeze(PQW @ np.expand_dims(r_orb.T, axis=r_orb.ndim))
    V = np.squeeze(PQW @ np.expand_dims(v_orb.T, axis=v_orb.ndim))

    return np.hstack((R, V))


def delta_trs2enu(trs: "TrsPositionDelta") -> "EnuPositionDelta":
    """Convert position deltas from TRS to ENU"""
    return np.squeeze(trs.ref_pos.trs2enu @ trs.mat)


def delta_enu2trs(enu: "EnuPositionDelta") -> "TrsPositionDelta":
    """Convert position deltas from ENU to TRS"""
    return np.squeeze(enu.ref_pos.enu2trs @ enu.mat)


def delta_trs2enu_posvel(trs: "TrsPosVelDelta") -> "EnuPosVelDelta":
    """Convert position deltas from TRS to ENU"""
    t2e = trs.ref_pos.trs2enu
    trs2enu = np.block([[t2e, np.zeros(t2e.shape)], [np.zeros(t2e.shape), t2e]])
    return np.squeeze(trs2enu @ trs.mat)


def delta_trs2acr_posvel(trs: "TrsPosVelDelta") -> "AcrPosVelDelta":
    """Convert position deltas from TRS to ACR"""
    t2a = trs.ref_pos.trs2acr
    trs2acr = np.block([[t2a, np.zeros(t2a.shape)], [np.zeros(t2a.shape), t2a]])
    return np.squeeze(trs2acr @ trs.mat)


def delta_enu2trs_posvel(enu: "EnuPosVelDelta") -> "TrsPosVelDelta":
    """Convert position deltas from ENU to TRS"""
    e2t = enu.ref_pos.enu2trs
    enu2trs = np.block([[e2t, np.zeros(e2t.shape)], [np.zeros(e2t.shape), e2t]])
    return np.squeeze(enu2trs @ enu.mat)


def delta_acr2trs_posvel(acr: "AcrPosVelDelta") -> "TrsPosVelDelta":
    """Convert position deltas from ACR to TRS"""
    a2t = acr.ref_pos.acr2trs
    acr2trs = np.block([[a2t, np.zeros(a2t.shape)], [np.zeros(a2t.shape), a2t]])
    return np.squeeze(acr2trs @ acr.mat)
