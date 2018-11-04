#!/usr/bin/env python3
# -*- encoding=utf8 -*-
# Author        :  Mohammed Ouassou
# Date          :  October 11, 2018
# Organization  :  NMA, Geodetic Institute

prolog = """
**PROGRAM**
    klobuchar_model.py
      
**PURPOSE**
    compute the ionospheric time-delay correction for the single-frequency by broadcast  model (klobuchar model).
    GPS and  Beidu satellite navigation systems use this model.
    The implementation is based on original paper of Klobuchar, J.A.
    Ionospheric Time-Delay Algorithm for Single-Frequency GPS Users
    https://scinapse.io/papers/2058160370

**USAGE**
"""
epilog = """
**EXAMPLE**
    klobuchar_model.py(time, ion_coeffs, rec_pos, azel)
    args:
    time        (I)  : GPST
    ion_coeffs  (I)  : iono model parameters {a0,a1,a2,a3,b0,b1,b2,b3} as vector
    rec_pos     (I)  : receiver position {lat,lon,h} [rad, rad, m] as vector
    azel        (I)  : azimuth/elevation angle {az,el} [rad] as vector 
    freq        (I)  : string, e.g. L1, L2, L5 (TODO: Not implemented)
    logger      (I)  : Function that logs
    l_result    (O)  : list containing the following parameters
        L1_delay   : computed path delay on L1 [m]
        L1_variance: correspong variance [m^2]
        
    
               
**COPYRIGHT**
    | Copyright 2018, by the Geodetic Institute, NMA
    | All rights reserved

**AUTHORS**
    | Mohammed Ouassou 
    | Geodetic Institute, NMA
    | Kartverksveien 21, N-3511
    | Hønefoss, Norway

Keywords: Klobuchar model, Nequick broadcast model
"""
#

# ================================ #
#   [1]   Import system modules    #
# " =============================== #
import argparse
import numpy as np
import scipy.constants as sp_c

# ====================================== #
# [2] import user defined  modules (TBD) #
# ====================================== #


# ======================================== #
#   FUNCTION 1: get_my_parser()            #
# ======================================== #
def get_my_parser():
    parser = argparse.ArgumentParser(
        description=prolog, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # parser.add_argument('-t', action='store', dest='input', required=True, help=' required GPST  ')
    # parser.add_argument('-r', action='store', dest='input', required=True, help=' required receiver position {lat,lon,h} (rad,m) as vector');
    # parser.add_argument('-p', action='store', dest='input', required=True, help=' iono model parameters {a0,a1,a2,a3,b0,b1,b2,b3} as vector');
    # parser.add_argument('-a', action='store', dest='input', required=True, help=' azimuth/elevation angle {az,el} [rad]');

    return parser


# ============================================ #
#  FUNCTION 2: Klobuchar Broadcast algorithm   #
# ============================================ #
def klobuchar(t, ion_coeffs, rec_pos, az, el, logger=print):
    """Compute the ionospheric time-delay correction for the single-frequency by broadcast  model (klobuchar model)
    
    GPS and  Beidu satellite navigation systems use this model.
    The implementation is based on original paper of Klobuchar, J.A.
    Ionospheric Time-Delay Algorithm for Single-Frequency GPS Users
    https://scinapse.io/papers/2058160370
    
    Args:
        time:       GPST
        ion_coeffs: iono model parameters {a0,a1,a2,a3,b0,b1,b2,b3} as vector
        rec_pos:    receiver position {lat,lon,h} [rad, rad, m] as vector
        az:         azimuth angle [rad]
        el:         elevation angle [rad]
        logger:     Function that logs

    Returns:
        L1_delay:    computed path delay on L1 [m]
        L1_variance: corresponding variance [m^2]
    """

    # variables declaration
    PI = np.pi
    CLIGHT = sp_c.c
    alpha, beta = ion_coeffs[:4], ion_coeffs[4:]

    # check the input args
    if len(ion_coeffs) != 8:
        raise ValueError(f"klobuchar_model()::number of iono coefficients={len(ion_coeffs)}, required 8")

    logger(" klobuchar_model():: input ionosphere parameters (alpha's and  beta's) are:")
    logger(f" \t Alpha coeffs= {alpha[0]:.2E},{alpha[1]:.2E},{alpha[2]:.2E},{alpha[3]:.2E}")
    logger(f" \t Beta coeffs = {beta[0]:.2E},{beta[1]:.2E},{beta[2]:.2E},{beta[3]:.2E}")

    # input data checks
    if rec_pos[2] < -1e3 or el <= 0.0:
        raise ValueError(
            f"klobuchar_model():: Invalid input parameters --> site height={rec_pos[2]:.2f}, elevation={el:.2f} [radians]"
        )

    if np.linalg.norm(ion_coeffs, ord=8) <= 0.0:
        raise ValueError(
            "klobuchar_model():: Invalid input parameters --> missing ionosphere model parameters (a0,a1,a2,a3,b0,b1,b2,b3) .."
        )

    # ==================================================== #
    # 1. calculate the Earth centered angle (semi-circle)  #
    # ==================================================== #
    psi = 0.0137 / (el / PI + 0.11) - 0.022

    # ==================================================== #
    # 2. sub-ionospheric latitude/longitude (semi-circle)  #
    # ==================================================== #
    phi = rec_pos[0] / PI + psi * np.cos(az)
    phi = 0.416 if phi > 0.416 else -0.416
    phi_ = phi

    # ==================================================== #
    # 3. compute the sub-ionospheric  longitude           #
    # ==================================================== #
    lam = rec_pos[1] / PI + psi * np.sin(az) / np.cos(phi * PI)

    # ==================================================== #
    #   4. compute geomagnetic latitude (semi-circle)      #
    # ==================================================== #
    phi += 0.064 * np.cos((lam - 1.617) * PI)

    # ==================================================== #
    #       5. find the  local time (s)                    #
    # ==================================================== #
    # tt  = 43200.0*lam + time2gpst(t, week);
    tt = t
    tt -= np.floor(tt / 86400.0) * 86400.0  #  0<=tt<86400

    # ==================================================== #
    #       6. compute the slant factor                    #
    # ==================================================== #
    f = 1.0 + 16.0 * (0.53 - el / PI) ** 3  # elevation angle shall be in cycle

    # ==================================================== #
    #       7.  compute the ionospheric time delay         #
    # ==================================================== #
    amp = ion_coeffs[0] + phi * (ion_coeffs[1] + phi * (ion_coeffs[2] + phi * ion_coeffs[3]))  # compute the amplitude
    per = ion_coeffs[4] + phi * (ion_coeffs[5] + phi * (ion_coeffs[6] + phi * ion_coeffs[7]))  # compute the periode
    amp = 0.0 if amp < 0.0 else amp
    per = 72000.0 if per < 72000.0 else per
    x = 2.0 * PI * (tt - 50400.0) / per
    L1_delay = (
        CLIGHT * f * (5e-9 + amp * (1.0 + x * x * (-0.5 + x * x / 24.0))) if (np.fabs(x) < 1.57) else CLIGHT * f * 5e-9
    )

    # ========================================================= #
    # define ERR_BRDCI 0.5:  broadcast iono model error factor  #
    # ========================================================= #
    L1_variance = (L1_delay * 0.5) ** 2

    #  debuging info
    logger(" ===================================       OUTPUT     ============================================")
    logger(f"\t[1] Earth-centered angle      = {psi:10.5f} [semicircles]")
    logger(f"\t[2] sub-ionospheric latitude  = {phi_:10.5f} [semicircles]")
    logger(f"\t[3] sub-ionospheric longitude = {lam:10.5f} [semicircles]")
    logger(f"\t[4] geomagnetic     latitude  = {phi:10.5f} [semicircles]")
    logger(f"\t[5] local time                = {tt:10.5f} [seconds]")
    logger(f"\t[6] slant factor              = {f:10.5f} ")
    logger(
        f"\t[7] ionosphere delay on L1 and the corresponding variance are: {L1_delay:.5f} (m) and {L1_variance:.5f} (m^2)"
    )
    logger(" ================================================================================================")

    return L1_delay, L1_variance


def main():
    # read command line arguments
    parser = get_my_parser()
    results = parser.parse_args()

    # ================================================ #
    # these values are copied from Klobuchar  trest    #
    # ================================================ #
    tt = 50700.0
    ion_coeffs = np.array([3.82e-8, 1.49e-8, -1.79e-7, 0, 1.43e5, 0.0, -3.28e5, 1.13e5])
    rec_pos = np.array([40.0 / 180.0, -100.0 / 180.0, 170])
    az = 240.0 / 180
    el = 20.0 / 180

    delay, variance = klobuchar(tt, ion_coeffs, rec_pos, az, el)

    # user info
    print(f" Ionospheric path delay on L1= {delay:.5f} [m] and the corresponding variance={variance:.5f} [m^2]")


if __name__ == "__main__":
    main()
