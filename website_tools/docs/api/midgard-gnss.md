# midgard.gnss


## midgard.gnss.antenna_calibration
Handling of GNSS antenna calibration information based on ANTEX file

**Description:**

The module includes a class for handling of GNSS antenna information based on read GNSS ANTEX file (see Rothacher, 2010).


**Reference:**

Rothacher, M. and Schmid, R. (2010): "ANTEX: The antenna exchange format", version 1.4, Forschungseinrichtung 
        Satellitengeodäsie, TU München
        
        
**Example:**

# Import AntennaCalibration class
from midgard.gnss.antenna_calibration import AntennaCalibration

# Get instance of AntennaCalibration class by defining ANTEX file path 
ant = AntennaCalibration(file_path="igs14.atx")



### **AntennaCalibration**

Full name: `midgard.gnss.antenna_calibration.AntennaCalibration`

Signature: `(file_path: Union[str, pathlib.PosixPath]) -> None`

A class for representing GNSS antenna calibration data

The attribute "data" is a dictionary with GNSS satellite PRN or receiver antenna as key. The GNSS satellite antenna
corrections are time dependent and saved with "valid from" datetime object entry. The dictionary looks like:

    dout = { <prn> : { <valid from>: { cospar_id:   <value>,
                                       sat_code:    <value>,
                                       sat_type:    <value>,
                                       valid_until: <value>,
                                       azimuth:     <list with azimuth values>,
                                       elevation:   <list with elevation values>,
                                       <frequency>: { azi: [<list with azimuth-elevation dependent corrections>],
                                                      neu: [north, east, up],
                                                      noazi: [<list with elevation dependent corrections>] }}},

             <receiver antenna> : { azimuth:     <list with azimuth values>,
                                    elevation:   <list with elevation values>,
                                    <frequency>: { azi: [<array with azimuth-elevation dependent corrections>],
                                                   neu: [north, east, up],
                                                   noazi: [<list with elevation dependent corrections>] }}}

with following entries:

| Value              | Type              | Description                                                             |
|--------------------|---------------------------------------------------------------------------------------------|
| azi                | numpy.ndarray     | Array with azimuth-elevation dependent antenna correction in [mm] with  |
|                    |                   | the shape: number of azimuth values x number of elevation values.       |
| azimuth            | numpy.ndarray     | List with azimuth values in [rad] corresponding to antenna corrections  |
|                    |                   | given in `azi`.                                                         |
| cospar_id          | str               | COSPAR ID <yyyy-xxxa>: yyyy -> year when the satellite was put in       |
|                    |                   | orbit, xxx -> sequential satellite number for that year, a -> alpha     |
|                    |                   | numeric sequence number within a launch                                 |
| elevation          | numpy.ndarray     | List with elevation values in [rad] corresponding to antenna            |
|                    |                   | corrections given in `azi` or `noazi`.                                  |
| <frequency>        | str               | Frequency identifier (e.g. G01 - GPS L1)                                |
| neu                | list              | North, East and Up eccentricities in [m]. The eccentricities of the     |
|                    |                   | mean antenna phase center is given relative to the antenna reference    |
|                    |                   | point (ARP) for receiver antennas or to the center of mass of the       |
|                    |                   | satellite in X-, Y- and Z-direction.                                    |
| noazi              | numpy.ndarray     | List with elevation dependent (non-azimuth-dependent) antenna           |
|                    |                   | correction in [mm].                                                     |
| <prn>              | str               | Satellite code e.g. GPS PRN, GLONASS slot or Galileo SVID number        |
| <receiver antenna> | str               | Receiver antenna name together with radome code                         |
| sat_code           | str               | Satellite code e.g. GPS SVN, GLONASS number or Galileo GSAT number      |
| sat_type           | str               | Satellite type (e.g. BLOCK IIA)                                         |
| valid_from         | datetime.datetime | Start of validity period of satellite in GPS time                       |
| valid_until        | datetime.datetime | End of validity period of satellite in GPS time                         |


Attributes:
    data (dict):           Data read from GNSS Antenna Exchange (ANTEX) file
    file_path (str):       ANTEX file path

Methods:
    satellite_phase_center_offset(): Determine satellite phase center offset correction vectors given in ITRS
    satellite_type(): Get satellite type from ANTEX file (e.g. BLOCK IIF, GALILEO-1, GALILEO-2, GLONASS-M,
                      BEIDOU-2G, ...)
    _used_date(): Choose correct date for use of satellite antenna corrections


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


## midgard.gnss.klobuchar
Klobuchar model for computing the ionospheric time-delay correction.

**Description:**

Compute the ionospheric time-delay correction for the single-frequency by
broadcast model (klobuchar model).  GPS and Beidu satellite navigation systems
use this model. The implementation is based on original paper of Klobuchar
(1987). The Klobuchar model is also described in Figure 20-4 in IS-GPS-200J.


**References:**

- IS-GPS-200J (2018): "Global positioning systems directorate systems engineering & integration interface
    specification IS-GPS-200, Navstar GPS space Segment/Navigation user segment interfaces, 25. April 2018

- Klobuchar, J.A. (1987): "Ionospheric Time-Delay Algorithm for Single-Frequency GPS Users", IEEE Transactions
    on Aerospace and Electronic Systems, Vol. AES-23, No. 3, May 1987, https://scinapse.io/papers/2058160370

- Sanz Subirana, J., Juan Zornoza, J.M. and Hernandez-Pajares, M. (2013): "GNSS data processing - Volume I:
    Fundamentals and Algorithms", TM-23/1, European Space Agency, May 2013



### **klobuchar**()

Full name: `midgard.gnss.klobuchar.klobuchar`

Signature: `(time, ion_coeffs, rec_pos, az, el, freq_l1, freq=None, logger=functools.partial(<function log at 0x7f04e3d4fe20>, level='debug'))`

Compute the ionospheric time-delay correction for the single-frequency by broadcast  model (klobuchar model)

GPS and  BeiDou satellite navigation systems use this model. The implementation is based on original paper of
Klobuchar, J.A. Ionospheric Time-Delay Algorithm for Single-Frequency GPS Users
https://scinapse.io/papers/2058160370

**Args:**

- `time`:       GPST
- `ion_coeffs`: iono model parameters {a0,a1,a2,a3,b0,b1,b2,b3} as vector
- `rec_pos`:    receiver position {lat,lon,h} [rad, rad, m] as vector
- `az`:         azimuth angle [rad]
- `el`:         elevation angle [rad]
- `system`:     GNSS system
- `freq_l1`:    L1 frequency of given GNSS in [Hz]
- `freq`:       Frequency in [Hz] for which ionospheric delay should be determined.
- `logger`:     Function that logs

**Returns:**

- `iono_delay`:    computed path delay for given frequency [m]
- `L1_variance`:   corresponding variance [m^2]

TODO: freq_L1 should be determined in klobuchar routine and argument be replaced by system. constants needed in
      Midgard.


### **main**()

Full name: `midgard.gnss.klobuchar.main`

Signature: `()`



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
