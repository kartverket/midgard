# midgard.ionosphere


## midgard.ionosphere.klobuchar
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

Full name: `midgard.ionosphere.klobuchar.klobuchar`

Signature: `(time, ion_coeffs, rec_pos, az, el, freq_l1, freq=None, logger=functools.partial(<function log at 0x7fa9957b3dc0>, level='debug'))`

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

Full name: `midgard.ionosphere.klobuchar.main`

Signature: `()`

