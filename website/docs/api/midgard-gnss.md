# midgard.gnss


## midgard.gnss.compute_dops
Compute DOP (dilution of precision)

**Description:**

Calculate GDOP, PDOP, TDOP, HDOP and VDOP based on elevation and azimuth between station and satellite for each 
observation epoch.


### **compute_dops**()

Full name: `midgard.gnss.compute_dops.compute_dops`

Signature: `(az: numpy.ndarray, el: numpy.ndarray) -> Tuple[numpy.ndarray, ...]`

Compute dilution of precision (DOP) for an observation epoch

It should be noted, that the weight of observations is not considered. The observation weight matrix is assumed to
be an identity matrix. The cofactor matrix Q is related to a topocentric coordinate system (north, east, up):

            | q_nn q_ne q_nu q_nt |
        Q = | q_ne q_ee q_eu q_et |
            | q_nu q_eu q_nn q_nt |
            | q_nt q_et q_nt q_tt |

Reference: Banerjee, P. and Bose, A. (1996): "Evaluation of GPS PDOP from elevation and azimuth of satellites",
    Indian Journal of Radio & Space Physics, Vol. 25, April 1996, pp. 110-113

**Args:**

- `az`:  Satellite azimuth angle (radians)
- `el`:  Satellite elevation angle (radians)

**Returns:**

Tuple with GDOP, PDOP, TDOP, HDOP and VDOP


## midgard.gnss.gnss
Midgard library module including functions for GNSS modeling

**Example:**

    from migard.gnss import gnss

**Description:**

This module will provide functions for GNSS modeling.


### **get_number_of_satellites**()

Full name: `midgard.gnss.gnss.get_number_of_satellites`

Signature: `(systems: numpy.ndarray, satellites: numpy.ndarray, epochs: numpy.ndarray) -> numpy.ndarray`

Get number of satellites per epoch

**Args:**

- `satellites`:     Array with satellite PRN number together with GNSS identifier (e.g. G07)
- `systems`:        Array with GNSS identifiers (e.g. G, E, R, ...)
- `epochs`:         Array with observation epochs (e.g. as datetime objects)

**Returns:**

Number of satellites per epoch


### **get_rinex_file_version**()

Full name: `midgard.gnss.gnss.get_rinex_file_version`

Signature: `(file_path: pathlib.PosixPath) -> str`

Get RINEX file version for a given file path

**Args:**

- `file_path`:  File path.

**Returns:**

RINEX file version


### **obstype_to_freq**()

Full name: `midgard.gnss.gnss.obstype_to_freq`

Signature: `(sys: str, obstype: str) -> float`

Get GNSS frequency based on given GNSS observation type

**Args:**

- `sys`:     GNSS identifier (e.g. 'E', 'G', ...)
- `obstype`: Observation type (e.g. 'L1', 'P1', 'C1X', ...)

Return:
    GNSS frequency in [Hz]


## midgard.gnss.rec_velocity_est


### E_OMGA (float)
`E_OMGA = 7.2921151467e-05`


### epilog (str)
`epilog = '\n**EXAMPLE**\n    rec_velocity_est.py \n    args:\n    NONE\n               \n**COPYRIGHT**\n    | Copyright 2019, by the Geodetic Institute, NMA\n    | All rights reserved\n\n**AUTHORS**\n    | Mohammed Ouassou \n    | Geodetic Institute, NMA\n    | Kartverksveien 21, N-3511\n    | Hønefoss, Norway\n  \n'`


### lambda_E1 (float)
`lambda_E1 = 0.19029367279836487`


### prolog (str)
`prolog = '\n**PROGRAM**\n    rec_velocity_est.py\n      \n**PURPOSE**\n   "GNSS Receiver velocity estimation by Doppler measurements\n    \n    Doppler shift, affecting  the frequency of the signal received from  a GNSS satellite, is related to the user-satellite relative motion \n    and is useful to study  the receiver  motion.  Using measurements from at least four simultaneous Doppler measurements, Least Square (LS) \n    or Kalman filter (KF) estimation techniques can be employed to obtain an estimate of the four unknown dx=(Vx, Vy, Vz, rate(cdt) ).\n    \n    FACTS:\n        F.1 The design matrix  H of the Doppler based velocity model is the same as the pseudorange  case. Constellation geometry influences the \n            velocity accuracy according to DOP.\n        F.2 The measurement errors is composed of systematic errors (orbital errors, atmosphere, and so forth) and the measurement noise. \n            Noting that the Doppler is the time derivative of the carrier phase, the systematic Doppler errors are the time derivative of the \n            carrier phase errors and changing slowly with time. The magnitude is at the level of millimeters per seconds. \n        F.3 Geometry factors influences the estimation process.    \n        F.4 The implementation is based on the paper of Mark Petovello (GNSS solutions).\n    \n    VALIDATION:\n        V.1 CNES software package SPRING is used to validate the implemented SPV.\n        V.2 Solution validation is based on Chi-square test and GDOP values on epoch-by-epoch basis\n   \n**USAGE**\n'`


### **spvDoppler**

Full name: `midgard.gnss.rec_velocity_est.spvDoppler`

Signature: `(z, H, x, dx, Qx)`



## midgard.gnss.solution_validation


### **comp_quality_indicators**()

Full name: `midgard.gnss.solution_validation.comp_quality_indicators`

Signature: `(sol_vc_mat: numpy.ndarray) -> tuple`

Compute quality indicators

Following quality indicators are computed
    1. compute the standard error ellipse(SEE)
    2. compute the distance root mean squared (DRMS)
    3. compute the circular error probable (CEP)

**Args:**

- `sol_vc_mat`:    Variance-covariance matrix of the unknown

**Returns:**

Tuple with DRMS, CEP and SEE


### epilog (str)
`epilog = '\n**EXAMPLE**\n    sol_validation (residuals, alpha_sign_level n_params)\n    args:\n    residuals       (I): postfit residuals \n    alpha_sign_level(I): alpha significance level and defines the rejection area.\n                         possible values of alpha = 0.05 (95%), 0.01 (99%) and 0.001 (99.9%)\n    n_params        (I): number of estimated parameters (states).\n    \n\nKeywords: Chi-square distribution,\n'`


### **get_my_parser**()

Full name: `midgard.gnss.solution_validation.get_my_parser`

Signature: `()`



### **main**()

Full name: `midgard.gnss.solution_validation.main`

Signature: `()`

Main program for testing solution validation implementation

#TODO: This should be done via midgard/tests/gnss !!!


### prolog (str)
`prolog = '\n**PROGRAM**\n    solution_validation.py\n      \n**PURPOSE**\n    Perform Chi-square test for residuals. Degrees of freedom (df) refers to the number of values that\n    are free to vary df = number of valid satellites (nv) - number of parameters to be estimated (nx) - 1.\n    GNSS solution validation based on the argument alpha, the level of significance (e.g. 99%), and\n    defines the rejection level of the crossing events. \n    Note that this is different from the false alarm rate, which instead refers to error type I\n    \n**USAGE**\n'`


### **sol_validation**()

Full name: `midgard.gnss.solution_validation.sol_validation`

Signature: `(residuals: numpy.ndarray, alpha_siglev: float, n_params: int = 4) -> bool`

Validating the GNSS solution is carried out using Chi-square test

Use Chi-square test for outlier detection and rejection. 

**Args:**

- `residuals`:      Postfit residuals for all satellites in each epoch 
- `alpha_siglev`:   Alpha significance level
- `n_params`:       Number of parameters (states), normally 4 parameters for station coordinates and receiver clock

**Returns:**

Array containing False for observations to throw away.
