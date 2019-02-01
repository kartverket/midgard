"""Perform Chi-square test for residuals

Description:
------------

Perform Chi-square test for residuals. Degrees of freedom (df) refers to the number of values that are free to vary df
= number of valid satellites (nv) - number of parameters to be estimated (nx) - 1.  GNSS solution validation based on
the argument alpha, the level of significance (e.g. 99%), and defines the rejection level of the crossing events.  Note
that this is different from the false alarm rate, which instead refers to error type I

"""

# Standard library imports
import sys
from typing import Callable, Tuple
import warnings

# Third party imports
import numpy as np
from numpy import linalg as LA
from scipy import stats

# Midgard imports
from midgard.dev import log

# =========================================================== #
# [3] The following constants MUST be defined or configurable #
# =========================================================== #
MAX_GDOPS = 30.0  # 30 is defined as upper bound for GDOP
MIN_EL_MASK = 10.0  # minimum elevation mask
SOL_MIN_VALID_SATS = 4.0  # minimum valid satellite to compute the solution


def compute_DOPS(az: np.array, el: np.array, logger: Callable = log.info) -> Tuple[float, float, float, float]:
    """Compute DOP (dilution of precision)

    In case of error, dop[0]-dop[3] are set to 0 and a warning is raised.

    Args:
        az:      Satellite azimuth angles (radians).
        el:      Satellite elevation angles (radians).
        logger:  Logger to handle messages.

    Returns:
        Tuple with DOP values: `(GDOP, PDOP, HDOP, VDOP)`.
    """

    # Remove satellites below elevation mask
    idx = el >= MIN_EL_MASK
    if np.any(~idx):
        logger(f"Remove {np.sum(~idx)} satellites based on elevation mask")
        az = az[idx]
        el = el[idx]

    # Make sure that we have enough valid satellites
    n_valid_sats = np.sum(idx)
    if n_valid_sats < SOL_MIN_VALID_SATS:
        raise ValueError(
            f"Not enough valid observation={n_valid_sats}, at least {SOL_MIN_VALID_SATS} observations are needed ...!"
        )

    # Construct the design matrix H based on observed & valid satellites
    # =================================================================== #
    #                                                                     #
    #       | cos(e1)sin(a1)   cos(e1)cos(a1)   sin(e1)   1  |            #
    #       | cos(e2)sin(a2)   cos(e2)cos(a2)   sin(e2)   1  |            #
    #       | cos(e3)sin(a3)   cos(e3)cos(a3)   sin(a3)   1  |            #
    #  H =  | cos(e4)sin(a4)   cos(e4)cos(a4)   sin(e4)   1  |            #
    #       |    ..               ..             ..      ..  |            #
    #       | cos(e_n)sin(a_n) cos(e_n)cos(a_n) sin(a_n)  1  |            #
    # =================================================================== #
    H = np.stack((np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el), np.ones(el.shape)), axis=1)
    Q = H.T @ H

    # User info
    logger("Q=H^t*H::")
    logger(Q)

    # Check if the inverse of Q exists by computing the conditional number OR computation of the determinant
    if not np.isfinite(np.linalg.cond(Q)):
        raise ValueError("Error computing the inverse of the co-factor matrix Q")
    else:
        Q = np.linalg.inv(Q)
        gdop = np.sqrt(np.trace(Q))
        pdop = np.sqrt(np.trace(Q[0:3]))
        hdop = np.sqrt(np.trace(Q[0:2]))
        vdop = np.sqrt(np.trace(Q[0:1]))
    return gdop, pdop, hdop, vdop


def comp_quality_indicators(sol_vc_mat: np.array, logger: Callable = log.info) -> Tuple[float, float, float]:
    """Compute quality indicators

    This function computes

    1. compute the distance root mean squared (DRMS)
    2. compute the circular error probable (CEP)
    3. compute the standard error ellipse (SEE)

    Args:
        sol_vc_mat:  variance-covariance matrix of the unknown
        logger:      to handle messages

    Returns:
        Tuple with quality indicators: `(DRMS, CEP, SEE)`
    """

    # 1. compute the standard error ellipse(SEE). Requires to compute
    #    lam_min, lam_max and the orientation angle (alpha)
    eig_val, eig_vec = LA.eig(sol_vc_mat)
    lambda_max = np.max(np.diag(eig_val))
    idx_a = np.argmax(eig_val)
    a = np.sqrt(lambda_max)  # TODO: a is currently not used
    lambda_min = np.min(np.diag(eig_val))
    idx_b = np.argmin(eig_val)
    b = np.sqrt(lambda_min)  # TODO: b is currently not used

    # direction of the largest vector
    alpha = np.degrees(np.arctan2(eig_val[1, idx_a], eig_val[0, idx_b]))
    SEE = [lambda_max, lambda_min, alpha]

    # 2. compute the distance root mean squred  (DRMS)
    DRMS = np.sqrt(sol_vc_mat[0, 0] + sol_vc_mat[1, 1])

    # 3. compute the circular error probable (CEP)
    std_of_unknown = np.sqrt(np.diag(sol_vc_mat))
    std_ratio = std_of_unknown[0] / std_of_unknown[1]
    if .2 <= std_ratio <= 1.0:
        CEP = 0.589 * (std_of_unknown[0] + std_of_unknown[1])
    else:
        CEP = .0

    return DRMS, CEP, SEE


def sol_validation(residuals, alpha_siglev, n_params, az, el, logger=log.info) -> bool:
    """Validate a GNSS solution

    Validating  the GNSS solution is carried out by performing the following tasks:

    1. Chi-square test as outlier detection and rejections
    2. compute DOPS values
    3. compute the standard error ellipse
    4. compute the distance root mean squred (DRMS) <- TODO
    5. compute the circular error probable (CEP) <- TODO
    6. implementation of internal reliability
    7. implementation of external reliability

    Args:
        residuals:     Postfit residuals
        alpha_siglev:  Alpha significance level
        n_val_sats:    Number of valid satellites
        n_params:      Number of parameters (states)
        az:            Array containing the azimuth values
        el:            Array containing the elevation values
        logger:        To handle messages

    Returns:
        True if solution is validated, False otherwise.
    """
    # Remove satellites below elevation mask
    idx = el >= MIN_EL_MASK
    if np.any(~idx):
        logger(f"Remove {np.sum(~idx)} satellites based on elevation mask")
        az = az[idx]
        el = el[idx]
        residuals = residuals[idx]

    # chi-square validation of residuals
    vv = residuals.T @ residuals  # sum (v(i) * v(i))

    # regular checks
    n_val_sats = len(residuals)
    df = n_val_sats - n_params - 1
    chi_sqr = stats.chi2.ppf(1 - alpha_siglev, df=df)

    if df > 0 and vv > chi_sqr:
        logger(
            f"sol_validation():: Error,  number of valid sats={n_val_sats:03} vv={vv:.2f} "
            f"chi-square value={chi_sqr:.2f}--> TEST NOT PASSED  "
        )
        return False

    else:
        logger(
            f"sol_validation():: number of valid sats={n_val_sats:02} vv={vv:.2f} < chi-square value={chi_sqr:.2f} "
            f"--> Test passed for alpha significance level={(1.0 - alpha_siglev) * 100:.2f} %"
        )
        return True

    """ TODO
    # 1.  Compute DOPS
    dops_vals = compute_DOPS(az, el, logger=logger)
    if dops_vals[0] <= 0.0 or dops_vals[0] > MAX_GDOPS:
        logger(
            f"sol_validation():: compute_DOPS(): not valid solution, number of valid sats={n_val_sats:02d} and  GDOP={dops_vals[0]:.2f}"
        )

    logger(f" DOPS results::")
    logger(f" compute_DOPS(): GDOP={dops_vals[0]:.2f}")
    logger(f" compute_DOPS(): PDOP={dops_vals[1]:.2f}")
    logger(f" compute_DOPS(): HDOP={dops_vals[2]:.2f}")
    logger(f" compute_DOPS(): PDOP={dops_vals[3]:.2f}")
    """
