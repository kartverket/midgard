"""Klobuchar model for computing the ionospheric time-delay correction.

Description:
------------

Compute the ionospheric time-delay correction for the single-frequency by
broadcast model (klobuchar model).  GPS and Beidu satellite navigation systems
use this model. The implementation is based on original paper of Klobuchar
(1987). The Klobuchar model is also described in Figure 20-4 in IS-GPS-200J.


References:
-----------

- IS-GPS-200J (2018): "Global positioning systems directorate systems engineering & integration interface
    specification IS-GPS-200, Navstar GPS space Segment/Navigation user segment interfaces, 25. April 2018

- Klobuchar, J.A. (1987): "Ionospheric Time-Delay Algorithm for Single-Frequency GPS Users", IEEE Transactions
    on Aerospace and Electronic Systems, Vol. AES-23, No. 3, May 1987, https://scinapse.io/papers/2058160370

- Sanz Subirana, J., Juan Zornoza, J.M. and Hernandez-Pajares, M. (2013): "GNSS data processing - Volume I:
    Fundamentals and Algorithms", TM-23/1, European Space Agency, May 2013

"""
# Standard library imports
import argparse

# Third party constants
import numpy as np

# Midgard imports
from midgard.dev import log
from midgard.math.constant import constant


def klobuchar(time, ion_coeffs, rec_pos, az, el, freq_l1, freq=None, logger=log.debug):
    """Compute the ionospheric time-delay correction for the single-frequency by broadcast  model (klobuchar model)

    GPS and  BeiDou satellite navigation systems use this model. The implementation is based on original paper of
    Klobuchar, J.A. Ionospheric Time-Delay Algorithm for Single-Frequency GPS Users
    https://scinapse.io/papers/2058160370

    Args:
        time:       GPST
        ion_coeffs: iono model parameters {a0,a1,a2,a3,b0,b1,b2,b3} as vector
        rec_pos:    receiver position {lat,lon,h} [rad, rad, m] as vector
        az:         azimuth angle [rad]
        el:         elevation angle [rad]
        system:     GNSS system
        freq_l1:    L1 frequency of given GNSS in [Hz]
        freq:       Frequency in [Hz] for which ionospheric delay should be determined.
        logger:     Function that logs

    Returns:
        iono_delay:    computed path delay for given frequency [m]
        L1_variance:   corresponding variance [m^2]

    TODO: freq_L1 should be determined in klobuchar routine and argument be replaced by system. constants needed in
          Midgard.
    """

    # check the input args, and rename them
    if len(ion_coeffs) != 8:
        raise ValueError(f"klobuchar_model()::number of iono coefficients={len(ion_coeffs)}, required 8")
    alpha, beta = ion_coeffs[:4], ion_coeffs[4:]

    logger(" klobuchar_model():: input ionosphere parameters (alpha's and  beta's) are:")
    logger(f" \t Alpha coeffs= {alpha[0]:.2E},{alpha[1]:.2E},{alpha[2]:.2E},{alpha[3]:.2E}")
    logger(f" \t Beta coeffs = {beta[0]:.2E},{beta[1]:.2E},{beta[2]:.2E},{beta[3]:.2E}")

    # input data checks
    if rec_pos[2] < -1e3 or el <= 0.0:
        raise ValueError(
            f"klobuchar_model():: Invalid input parameters --> "
            f"site height={rec_pos[2]:.2f}, elevation={el:.2f} [radians]"
        )

    if np.linalg.norm(ion_coeffs, ord=8) <= 0.0:
        raise ValueError(
            "klobuchar_model():: Invalid input parameters --> "
            "missing ionosphere model parameters (a0, a1, a2, a3, b0, b1, b2, b3) .."
        )

    # ==================================================== #
    # 1. calculate the Earth centered angle (semi-circle)  #
    # ==================================================== #
    psi = 0.0137 / (el / np.pi + 0.11) - 0.022

    # ==================================================== #
    # 2. sub-ionospheric latitude/longitude (semi-circle)  #
    # ==================================================== #
    phi = (rec_pos[0] / np.pi) + psi * np.cos(az)
    # +TODO: old
    # phi = 0.416 if phi > 0.416 else -0.416
    # -TODO: old
    if phi > 0.416:
        phi = 0.416
    elif phi < -0.416:
        phi = -0.416
    phi_ = phi

    # ==================================================== #
    # 3. compute the sub-ionospheric  longitude           #
    # ==================================================== #
    lam = rec_pos[1] / np.pi + psi * np.sin(az) / np.cos(phi * np.pi)

    # ==================================================== #
    #   4. compute geomagnetic latitude (semi-circle)      #
    # ==================================================== #
    phi += 0.064 * np.cos((lam - 1.617) * np.pi)

    # ==================================================== #
    #       5. find the  local time (s)                    #
    # ==================================================== #
    # +TODO: old
    # # tt  = 43200.0*lam + time2gpst(t, week);
    # tt = t
    # tt -= np.floor(tt / 86400.0) * 86400.0  #  0<=tt<86400
    # -TODO: old
    tt = 43200.0 * lam + time
    tt -= np.floor(tt / 86400.0) * 86400.0  # Seconds of day (0<=tt<86400)
    # TODO: Do we need that?
    if tt > 86400.0:
        tt -= 86400.0
    elif tt < 0.0:
        tt += 86400.0

    # ==================================================== #
    #       6. compute the slant factor                    #
    # ==================================================== #
    f = 1.0 + 16.0 * (0.53 - el / np.pi) ** 3  # elevation angle shall be in cycle

    # ==================================================== #
    #       7.  compute the L1 ionospheric time delay      #
    # ==================================================== #
    amp = ion_coeffs[0] + phi * (ion_coeffs[1] + phi * (ion_coeffs[2] + phi * ion_coeffs[3]))  # compute the amplitude
    per = ion_coeffs[4] + phi * (ion_coeffs[5] + phi * (ion_coeffs[6] + phi * ion_coeffs[7]))  # compute the periode
    amp = 0.0 if amp < 0.0 else amp
    per = 72000.0 if per < 72000.0 else per
    x = 2.0 * np.pi * (tt - 50400.0) / per
    L1_delay = (
        constant.c * f * (5e-9 + amp * (1.0 + x * x * (-0.5 + x * x / 24.0)))
        if (np.fabs(x) < 1.57)
        else constant.c * f * 5e-9
    )

    # ==================================================== #
    #  8.  Ionospheric time delay for given frequency     #
    # ==================================================== #
    # The ionospheric delay for another frequency than GPS L1 or BeiDou B1 can be determined via Eq. 5.5 in Sanz
    # Subirana et al. (2013).
    if freq is None:
        iono_delay = L1_delay
    else:
        iono_delay = (freq_l1 / freq) ** 2 * L1_delay

    # ========================================================= #
    # define ERR_BRDCI 0.5:  broadcast iono model error factor  #
    # ========================================================= #
    # TODO: How to determine variance for other GNSS frequencies?
    L1_variance = (L1_delay * 0.5) ** 2

    #  debuging info
    logger(" ===================================       OUTPUT     ============================================")
    logger(f"\t[1] Earth-centered angle      = {psi:11.5f} [semicircles]")
    logger(f"\t[2] sub-ionospheric latitude  = {phi_:11.5f} [semicircles]")
    logger(f"\t[3] sub-ionospheric longitude = {lam:11.5f} [semicircles]")
    logger(f"\t[4] geomagnetic     latitude  = {phi:11.5f} [semicircles]")
    logger(f"\t[5] local time                = {tt:11.5f} [seconds]")
    logger(f"\t[6] slant factor              = {f:11.5f} ")
    logger(f"\t[7] amplitude                 = {amp:11.5e}")
    logger(f"\t[8] period                    = {per:11.5f}")
    logger(
        f"\t[9] ionosphere delay for frequency {freq * 1e-6:11.2f} Mhz and the corresponding variance are: "
        f"{iono_delay:.5f} (m) and {L1_variance:.5f} (m^2)"
    )
    logger(" ================================================================================================")

    return iono_delay, L1_variance


def main():
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
