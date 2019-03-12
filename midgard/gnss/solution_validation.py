#!/usr/bin/env python3
# -*- encoding=utf8 -*-
# =============================================
# Author        :  Mohammed Ouassou
# Date          :  October 11, 2018
# Organization  :  NMA, Geodetic Institute
# =============================================

prolog = """
**PROGRAM**
    solution_validation.py
      
**PURPOSE**
    Perform Chi-square test for residuals. Degrees of freedom (df) refers to the number of values that
    are free to vary df = number of valid satellites (nv) - number of parameters to be estimated (nx) - 1.
    GNSS solution validation based on the argument alpha, the level of significance (e.g. 99%), and
    defines the rejection level of the crossing events. 
    Note that this is different from the false alarm rate, which instead refers to error type I
    
**USAGE**
"""
epilog = """
**EXAMPLE**
    sol_validation (residuals, alpha_sign_level n_params)
    args:
    residuals       (I): postfit residuals 
    alpha_sign_level(I): alpha significance level and defines the rejection area.
                         possible values of alpha = 0.05 (95%), 0.01 (99%) and 0.001 (99.9%)
    n_params        (I): number of estimated parameters (states).
    

Keywords: Chi-square distribution,
"""

# Standard library imports
import sys
from typing import Callable, Tuple
import warnings

# External library imports
import argparse
import numpy as np
from scipy import stats

# Midgard imports
from midgard.dev import log


# Define the function parser
def get_my_parser():
    parser = argparse.ArgumentParser(
        description=prolog, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    return parser


def compute_dops(az: np.ndarray, el: np.ndarray, el_mask: float = 0, min_num_sats: int = 4) -> Tuple[np.ndarray, ...]:
    """Compute DOP (dilution of precision)

    Args:
        az:  Satellite azimuth angle (radians)
        el:  Satellite elevation angle (radians)
        el_mask: Elevation cut-off angle (radians)
        min_num_sats: Minimum number of satellites for a valid solution

    Returns:
        Tuple with GDOP, PDOP, HDOP and VDOP
    """
    gdop = np.array([0.0])
    pdop = np.array([0.0])
    hdop = np.array([0.0])
    vdop = np.array([0.0])

    # Make sure that we have enough valid satellites
    n_valid_sats = np.sum(el >= el_mask)
    if n_valid_sats < min_num_sats:
        log.warn(
            f"Not enough valid observation={n_valid_sats:02d}, at least {min_num_sats:02d} observations are needed ...!"
        )
        return gdop, pdop, hdop, vdop

    # Construct the design matrix H based on observed & valid satellites
    #    NB: treat H as a vector
    #
    #       | cos(e1)sin(a1)   cos(e1)cos(a1)   sin(e1)   1  |
    #       | cos(e2)sin(a2)   cos(e2)cos(a2)   sin(e2)   1  |
    #       | cos(e3)sin(a3)   cos(e3)cos(a3)   sin(a3)   1  |
    #  H =  | cos(e4)sin(a4)   cos(e4)cos(a4)   sin(e4)   1  |
    #       |    ..               ..             ..      ..  |
    #       | cos(e_n)sin(a_n) cos(e_n)cos(a_n) sin(a_n)  1  |
    H = np.stack((np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el), np.ones(el.shape)), axis=1)
    Q = H.T @ H  # H^t*H

    # User info
    log.debug("Q=H^t*H::")
    log.debug(Q)

    # Check if the inverse of Q exists by computing the conditional number OR computation of the detereminant
    if not np.isfinite(np.linalg.cond(Q)):
        log.warn("error computing the inverse of the co-factor matrix Q")

    else:
        Q = np.linalg.inv(Q)  # (H*H^t)^{-1}
        gdop = np.sqrt(np.trace(Q))  # GDOP
        pdop = np.sqrt(np.trace(Q[0:3]))  # PDOP
        hdop = np.sqrt(np.trace(Q[0:2]))  # HDOP
        vdop = np.sqrt(np.trace(Q[0:1]))  # VDOP

    return gdop, pdop, hdop, vdop


def comp_quality_indicators(sol_vc_mat: np.ndarray) -> tuple:
    """Compute quality indicators

    Following quality indicators are computed
        1. compute the standard error ellipse(SEE)
        2. compute the distance root mean squared (DRMS)
        3. compute the circular error probable (CEP)

    Args:
        sol_vc_mat:    Variance-covariance matrix of the unknown

    Returns:
        Tuple with DRMS, CEP and SEE
    """

    # 1. Compute the standard error ellipse(SEE). Requires to compute
    #    lam_min, lam_max and the orientation angle (alpha)
    eig_val, eig_vec = np.linalg.eig(sol_vc_mat)
    lambda_max = np.max(np.diag(eig_val))
    idx_a = np.argmax(eig_val)
    a = np.sqrt(lam_max)
    lambda_min = np.min(np.diag(eig_val))
    idx_b = np.argmin(eig_val)
    b = np.sqrt(lam_min)

    # Direction of the largest vector
    alpha = arctan2(eig_val[1, idx_a], eig_val[0, idx_b]) * 180 / np.pi
    see = [lambda_max, lambda_min, alpha]

    # 2. Compute the distance root mean squred  (DRMS)
    drms = np.sqrt(sol_vc_mat[0, 0] + sol_vc_mat[1, 1])

    # 3. Compute the circular error probable (CEP)
    std_of_unknown = np.sqrt(np.diag(sol_vc_mat))
    std_ratio = std_of_unknown[0] / std_of_unknown[1]
    if .2 <= std_ratio <= 1.0:
        cep = 0.589 * (std_of_unknown[0] + std_of_unknown[1])
    else:
        cep = .0

    return drms, cep, see


def sol_validation(residuals: np.ndarray, alpha_siglev: float, n_params: int = 4) -> bool:
    """Validating the GNSS solution is carried out using Chi-square test

    Use Chi-square test for outlier detection and rejection. 

    Args:
        residuals:      Postfit residuals for all satellites in each epoch 
        alpha_siglev:   Alpha significance level
        n_params:       Number of parameters (states), normally 4 parameters for station coordinates and receiver clock

    Returns:
        Array containing False for observations to throw away.
    """

    # Regular checks
    num_obs = len(residuals)
    df = num_obs - n_params - 1
    if df < 0:
        log.warn(f"sol_validattion():: degree of freedom < 0 (df = {df}) --> TEST NOT PASSED")
        return False

    # Chi-square validation of residuals
    vv = np.dot(residuals, residuals)  # sum (v(i) * v(i))
    chi_sqr = stats.chi2.ppf(1 - alpha_siglev, df=df)

    if vv > chi_sqr:
        log.debug(
            f"sol_validattion():: number of valid obs={num_obs:03} vv={vv:.2f} chi-square value={chi_sqr:.2f}--> TEST NOT PASSED"
        )
        return False

    else:
        log.debug(
            f"sol_validation():: number of valid obs={num_obs:02} vv={vv:.2f} < chi-square value={chi_sqr:.2f} --> TEST PASSED for alpha significance level= {(1.0-alpha_siglev)*100:.2f} %"
        )
        return True


def main():
    """Main program for testing solution validation implementation

    #TODO: This should be done via midgard/tests/gnss !!!
    """
    log.init(log_level="info")

    # Upper bound for GDOP
    max_gdops = 30.0

    # Read command line arguments
    parser = get_my_parser()
    results = parser.parse_args()
    no_print = lambda _: None

    # User info/test
    log.info(f" number of arguments ={len(sys.argv):d}")
    log.info(f" program name        ={sys.argv}")

    # Testing the implemented function
    if len(sys.argv) == 1:
        i_res_cnt = 9
        n_val_sats = i_res_cnt
        alpha_siglev = 0.01
        n_params = 5
        my_residuals = np.random.normal(0.0, 1, size=i_res_cnt)
        az, el = np.random.normal(60, 30, size=(2 * n_val_sats)).reshape(-1, 2).T
        my_result = sol_validation(my_residuals, alpha_siglev, n_params)

        dops_vals = compute_dops(az, el)

        if dops_vals[0] <= 0.0 or dops_vals[0] > max_gdops:
            log.warn(
                f"sol_validation():: compute_dops(): not valid solution, number of valid sats={n_val_sats:02d} and  GDOP={dops_vals[0]:.2f}"
            )

        log.info(f" DOPS results::")
        log.info(f" compute_dops(): GDOP={dops_vals[0]:.2f}")
        log.info(f" compute_dops(): PDOP={dops_vals[1]:.2f}")
        log.info(f" compute_dops(): HDOP={dops_vals[2]:.2f}")
        log.info(f" compute_dops(): PDOP={dops_vals[3]:.2f}")


if __name__ == "__main__":
    main()
