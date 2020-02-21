"""Compute DOP (dilution of precision)

Description:
------------

Calculate GDOP, PDOP, TDOP, HDOP and VDOP based on elevation and azimuth between station and satellite for each 
observation epoch.
"""

# Standard library imports
from typing import Tuple

# External library imports
import numpy as np

# Midgard imports
from midgard.dev import log


def compute_dops(az: np.ndarray, el: np.ndarray) -> Tuple[np.ndarray, ...]:
    """Compute dilution of precision (DOP) for an observation epoch

    It should be noted, that the weight of observations is not considered. The observation weight matrix is assumed to
    be an identity matrix. The cofactor matrix Q is related to a topocentric coordinate system (north, east, up):

                | q_nn q_ne q_nu q_nt |
            Q = | q_ne q_ee q_eu q_et |
                | q_nu q_eu q_nn q_nt |
                | q_nt q_et q_nt q_tt |

    Reference: Banerjee, P. and Bose, A. (1996): "Evaluation of GPS PDOP from elevation and azimuth of satellites",
        Indian Journal of Radio & Space Physics, Vol. 25, April 1996, pp. 110-113

    Args:
        az:  Satellite azimuth angle (radians)
        el:  Satellite elevation angle (radians)

    Returns:
        Tuple with GDOP, PDOP, TDOP, HDOP and VDOP
    """

    # Construct the design matrix H based on observed & valid satellites
    #
    #       | -cos(e1) * cos(a1)   -cos(e1) * sin(a1)   -sin(e1)   1  |
    #       | -cos(e2) * cos(a2)   -cos(e2) * sin(a2)   -sin(e2)   1  |
    #       | -cos(e3) * cos(a3)   -cos(e3) * sin(a3)   -sin(a3)   1  |
    #  H =  | -cos(e4) * cos(a4)   -cos(e4) * sin(a4)   -sin(e4)   1  |
    #       |         ..                   ..              ..     ..  |
    #       | -cos(en) * cos(an)   -cos(en) * sin(an)   -sin(an)   1  |
    # H = np.stack((np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el), np.ones(el.shape)), axis=1)
    H = np.stack((-np.cos(el) * np.cos(az), -np.cos(el) * np.sin(az), -np.sin(el), np.ones(el.shape)), axis=1)
    Q = H.T @ H  # H^t*H

    # User info
    log.debug("Q=H^t*H::")
    log.debug(Q)

    # Check if the inverse of Q exists by computing the conditional number (or computation of the detereminant)
    if not np.isfinite(np.linalg.cond(Q)):
        log.warn("Error by computing the inverse of the co-factor matrix Q (DOP determination).")
        return None, None, None, None, None

    else:
        Q = np.linalg.inv(Q)  # (H*H^t)^{-1}
        gdop = np.sqrt(np.trace(Q))  # GDOP
        pdop = np.sqrt(np.trace(Q[0:3]))  # PDOP
        hdop = np.sqrt(np.trace(Q[0:2]))  # HDOP
        vdop = np.sqrt(Q[2, 2])  # VDOP
        tdop = np.sqrt(Q[3, 3])  # TDOP

    return gdop, pdop, tdop, hdop, vdop
