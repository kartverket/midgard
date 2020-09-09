#!/usr/bin/env python3
# -*- encoding=utf8 -*-
# ===========================================
# Author        :  Mohammed Ouassou
# Date          :  January 09, 2019
# Organization  :  NMA, Geodetic Institute
# ===========================================
prolog = """
**PROGRAM**
    rec_velocity_est.py
      
**PURPOSE**
   "GNSS Receiver velocity estimation by Doppler measurements
    
    Doppler shift, affecting  the frequency of the signal received from  a GNSS satellite, is related to the user-satellite relative motion 
    and is useful to study  the receiver  motion.  Using measurements from at least four simultaneous Doppler measurements, Least Square (LS) 
    or Kalman filter (KF) estimation techniques can be employed to obtain an estimate of the four unknown dx=(Vx, Vy, Vz, rate(cdt) ).
    
    FACTS:
        F.1 The design matrix  H of the Doppler based velocity model is the same as the pseudorange  case. Constellation geometry influences the 
            velocity accuracy according to DOP.
        F.2 The measurement errors is composed of systematic errors (orbital errors, atmosphere, and so forth) and the measurement noise. 
            Noting that the Doppler is the time derivative of the carrier phase, the systematic Doppler errors are the time derivative of the 
            carrier phase errors and changing slowly with time. The magnitude is at the level of millimeters per seconds. 
        F.3 Geometry factors influences the estimation process.    
        F.4 The implementation is based on the paper of Mark Petovello (GNSS solutions).
    
    VALIDATION:
        V.1 CNES software package SPRING is used to validate the implemented SPV.
        V.2 Solution validation is based on Chi-square test and GDOP values on epoch-by-epoch basis
   
**USAGE**
"""
epilog = """
**EXAMPLE**
    rec_velocity_est.py 
    args:
    NONE
               
**COPYRIGHT**
    | Copyright 2019, by the Geodetic Institute, NMA
    | All rights reserved

**AUTHORS**
    | Mohammed Ouassou 
    | Geodetic Institute, NMA
    | Kartverksveien 21, N-3511
    | Hønefoss, Norway
  
"""
# Standard library imports
import time
import math

# External imports
import scipy.constants as scp
from scipy import stats
from scipy.optimize import lsq_linear
import numpy as np

#  Midgard imports
from midgard.data.position import Position  # Import Position class
from midgard.collections import enums
from midgard.math.constant import constant

# define constants
# wavelength for E1 (D1X) - lambda_E1
lambda_E1 = constant.c / enums.gnss_freq_E.E1  # eller constant.c /enums.gnss_freq_E.E1.value
E_OMGA = constant.get("omega", source="wgs84")  # Earth Angular Velocity (IS-GPS) (rad/s)
logger = print


# =================================================
#  class definition of Single Point Velocity (SPV)
# =================================================
class spvDoppler(object):

    # =========================================
    #    METHOD 1: Constructor/Initializer
    # =========================================
    def __init__(self, z, H, x, dx, Qx):
        """Initialize the single point velocity estimation by Doppler

        Args:
            z  (vector):  Doppler observations              (num_obs)
            H  (matrix):  Design matrix                     (n_obs x n_params)
            x  (vector):  Receiver velocity final result    (4 elements)
            dx (vector):  state vector (Vx, Vy, Vz,c*dt)    (4  elements)
            Qx (matrix):  variance-covariance               (16 elements)
        """
        self.sol_val = False
        self.z = z
        self.H = H
        self.num_obs, self.num_params = self.H.shape
        self.x = x
        self.dx = dx
        self.Qx = Qx
        self.v = np.zeros(self.num_obs)
        self.rot_mat_T = np.zeros(shape=(3, 3))

    # =============================================
    # METHOD 2: Display the content of attributes
    # =============================================
    def display_attrb(self):

        logger(f" ================================================ ")
        logger(f" \t [1] display_attrb():: Doppler observations \n {self.z} \n")
        logger(f" \t [2] display_attrb():: Design matrix  \n{self.H} \n")
        logger(f" \t [3] display_attrb():: Number of parameters and observations={self.H.shape} ")
        logger(f" \t [4] display_attrb():: Receiver velocity components={self.x} ")
        logger(f" \t [5] display_attrb():: state vector={self.dx} ")
        logger(f" \t [6] display_attrb():: Solution covariance matrix \n {self.Qx} ")
        logger(f" \t [7] display_attrb():: Residuals vector {self.v} ")

    # ===================================================================
    #   METHOD 3 : ECEF to local ENU coordinate transfromation matrix
    # ===================================================================
    def xyz2enu_transf_mat(self, pos_llh, logger):
        """ Compute the transformation matrix to transform a vector in XYZ coordinates to ENU coordinate.
        
            It is appropriate to use WGS-84 topocentric cordinates to describe relative position,
            change in position, velocities, object orientation, differences in heught, etc. because
            WGS-84 is compatible with all national systems at such a local scale.
                  
        Args:
            pos_llh   (I)       (vector): geodetic position {lat,lon} (rad) 
            logger    (I)       (device): handle error messages 
            rot_mat_T (O)       (matrix): computed rotational matrix  (3x3)
        """
        sin_lat = np.sin(pos_llh[0])
        cos_lat = np.cos(pos_llh[0])
        sin_lon = np.sin(pos_llh[1])
        cos_lon = np.cos(pos_llh[1])
        rot_mat_T = np.array(
            [
                [-sin_lon, -sin_lat * cos_lon, cos_lat * cos_lon],  # 1st row
                [cos_lon, -sin_lat * sin_lon, cos_lat * sin_lon],  # 2nd row
                [0.0, cos_lat, sin_lat],
            ]
        )  # 3rd row

        self.rot_mat_T = rot_mat_T

        return rot_mat_T

    # =====================================================
    #       METHOD x: SPV Solution validation
    # =====================================================
    # def spv_sol_validation(self, dop_residuals: np.ndarray, alpha_sig_level: float, n_params: int = 4, Az: np.ndarray, El: np.ndarray, logger)  -> bool:
    def spv_sol_val(self, dop_residuals, alpha_sig_level, n_params, logger):

        """ Validating the estimated receiver velocity by Doppler measurements by DOPs values and residuals test
        Args:
            residuals:          Postfit residuals for all satellites in each epoch 
            alpha_sig_level:    Alpha significance level
            n_params:           Number of parameters (states), normally 4 parameters for station velocity and receiver clock rate
            Az  (vector):       azimuth angle (rad) 
            El  (vector):       elevation angle (rad)    
            logger:             define device to write the information to
        """

        # Regular checks
        num_obs = len(dop_residuals)
        # df = num_obs - n_params - 1
        df = num_obs - n_params
        if df < 0:
            logger(f"spv_sol_validation():: degree of freedom < 0 (df = {df}) --> TEST NOT PASSED")
            return False

        # Chi-square validation of residuals
        vv = np.dot(dop_residuals, dop_residuals)  # sum (v(i) * v(i))
        chi_sqr = stats.chi2.ppf(1 - alpha_sig_level, df=df)
        if math.isnan(chi_sqr):
            logger(
                f"spv_sol_validation():: number of valid obs={num_obs:03} vv={vv:.5f} degree of freedom={df}) chi-square value={chi_sqr:.5f}--> NOT A NUMBER"
            )
            print(dop_residuals)
            time.sleep(2)

        if vv > chi_sqr:
            logger(
                f"spv_sol_validation():: number of valid obs={num_obs:03} vv={vv:.5f} chi-square value={chi_sqr:.5f} max-res-value ={np.max(np.abs(dop_residuals))}--> TEST NOT PASSED"
            )
            print(dop_residuals)
            time.sleep(2)
            return False
        else:
            logger(
                f"spv_sol_validation():: number of valid obs={num_obs:02} vv={vv:.5f} < chi-square value={chi_sqr:.5f} --> TEST PASSED for alpha significance level= {(1.0-alpha_sig_level)*100:.2f} %"
            )
            return True

    # =========================================
    #    METHOD 4: compute Doppler residuals
    # =========================================
    def compute_doppler_res(self, dop_obs, sat_pos, sat_vel, sat_dt, rcv_pos, x, az, el, valid_sats):
        """Doppler residuals computation 
            
        Args:
            n is the number of satellites observed in this particular epoch
            dop_obs     (vector (nx1)): Doppler D1C observation data                                                              
            sat_pos     (matrix (nx3)): Satellite position in ECEF
            sat_vel     (matrix (nx3)): satellite velocity                            
            sat_dt      (matrix (nx2)): Clock offset and drift                          
            rcv_pos     (vector (3x1)): Receiver position in ECEF                              
            az          (vector (nx1)): azimuth angle (rad) 
            el          (vector (nx1)): elevation angle (rad) 
            valid_sats  (vector (nx1)): valid satellites ID  
            x           (vector (4x1)): state/parameter vector        
        Output:
            v : Doppler residuals                                       
            H : Design matrix 
            nv: number of valid satellite in solution
        """

        # local variables definition and initialization
        i = j = nv = 0
        e = np.zeros(3)
        a = svel_rel2rvel = e
        v = np.zeros(dop_obs.size)  # Doppler residuals
        T = np.zeros(shape=(3, 3))  # transformation matrix

        # =========================================================================
        #  Convert the receiver coordinates from ECEF to ENU, then compute the
        #  transformation matrix  T
        # =========================================================================
        rcv_llh = Position(val=rcv_pos, system="trs").llh

        # T= np.transpose(self.xyz2enu_transf_mat(rcv_llh, logger))
        E = self.xyz2enu_transf_mat(rcv_llh, logger)

        # sleep for a while
        time.sleep(0.1)

        # ===============================================
        #   Main loop: loop over all valid satellites
        # ===============================================
        n_obs = dop_obs.size
        if n_obs < 4:
            logger(f"compute_doppler_res():: Missing data for sat-ID:{valid_sats[i]} doppler data:{dop_obs[i]:.2f}  ")
            return 0

        for i in range(n_obs):

            # Check for valid Doppler measurement, satellite velocity and satellite IDs
            # if ( dop_obs[i] == 0.0 #or not valid_sats[i] #or np.linalg.norm(sat_vel[i]) <= 0.0):
            if dop_obs[i] == 0.0:

                logger(
                    f"compute_doppler_res():: index={i} -->  Missing data for sat-ID:{valid_sats[i]} doppler data:{dop_obs[i]:.2f}  "
                )
                continue

            # else:

            # A. compute line-of-sight vector in ECEF
            a = [np.sin(az[i]) * np.cos(el[i]), np.cos(az[i]) * np.cos(el[i]), np.sin(el[i])]
            LOS = [np.sin(az[i]) * np.cos(el[i]), np.cos(az[i]) * np.cos(el[i]), np.sin(el[i])]

            # compute the directional vector (LOS)= e (3x1)
            # e = T.transpose() @ a
            e = LOS @ E.T

            # B. satellite velocity relative to receiver in ECEF
            for j in range(3):
                svel_rel2rvel[j] = sat_vel[i, j] - x[j]

            # =========================================================== #
            #   C. range rate with Earth rotation correction              #
            # =========================================================== #
            #           Notez-Bien
            #
            # Satellite(S)/Receiver(R) relative motion is defined as:
            #
            #               R(Vx)*Sy - R(Vy)*Sx + S(Vy)*Rx - S(Vx)*Ry
            # Rearraging =  S(Vy)*Rx + Sy*R(Vx) - S(Vx)*Ry - Sx*R(Vy)
            # ==============================================================
            sat_rec_rel_motion = (
                sat_vel[i, 1] * rcv_pos[0] + sat_pos[i, 1] * x[0] - sat_vel[i, 0] * rcv_pos[1] - sat_pos[i, 0] * x[1]
            )
            d_rate_erc = np.float(np.dot(svel_rel2rvel, e) + E_OMGA / scp.speed_of_light * sat_rec_rel_motion)

            aa_dot = svel_rel2rvel.transpose() @ e

            # D. doppler residuals
            v[nv] = -lambda_E1 * dop_obs[i] - (d_rate_erc + x[3] - scp.speed_of_light * sat_dt[i])

            # E. design matrix
            for j in range(4):
                self.H[i, j] = -e[j] if j < 3 else 1.0

            # ====================================
            #          Debugging info
            # ====================================
            b_debug = False
            if b_debug:
                logger(f"\n\n compute_doppler_res():: E")
                print(T)
                logger(f"\n\n compute_doppler_res():: a")
                print(a)
                logger(f"\n\n compute_doppler_res():: e")
                print(e)
                logger(f"\n\n compute_doppler_res():: vs")
                print(svel_rel2rvel)
                logger(f"\n\n compute_doppler_res():: srrm")
                print(sat_rec_rel_motion)

                logger(f"\n\n compute_doppler_res():: dotproduct")
                print(np.float(np.dot(svel_rel2rvel, e)))
                print(np.double(np.dot(svel_rel2rvel, e)))
                print(aa_dot)
                logger(f"\n\n compute_doppler_res():: d_rate_erc")
                print(d_rate_erc)
                logger(f"compute_doppler_res():  svel_rel2rvel sat-ID:{valid_sats[i]} ")
                print(svel_rel2rvel)
                logger(f"compute_doppler_res():  sat_rec_rel_motion sat-ID:{valid_sats[i]} ")
                print(sat_rec_rel_motion)
                logger(f"compute_doppler_res():  d_rate_erc sat-ID:{valid_sats[i]} ")
                print(d_rate_erc)

            #  One more valid satellite
            nv += 1

        v = v[v != 0.0]

        # time.sleep(2)
        self.v = v
        return nv

    # ============================================================================ #
    #    METHOD 5: Estimate the receiver (user) velocity by Doppler measurement    #
    # ============================================================================ #
    def est_spv_by_doppler(self, dop_obs, sat_pos, sat_vel, sat_dts, rcv_pos, Az, El, valid_sats, logger):
        """
        Args:
            dop_obs (vector)    : observation data   
            sat_pos (matrix)    : Satellite position  
            sat_vel (matrix)    : Satellite position  
            sat_dts (vector)    : Satellite drift                  
            rcv_pos (vector)    : Receiver true coordinates in ECEF
            x                   : estimated receiver position                                         
            Az  (vector)        : azimuth angle (rad) 
            El  (vector)        : elevation angle (rad)    
            valid_sats (vector) : satellite ID (string) 
            logger              : define device to write the information to
        """

        # =========================
        # Step 1: Initialization
        # ==========================
        i = j = nv = 0
        n_parms = 4
        self.dop_obs = dop_obs
        n = dop_obs.size
        v = np.zeros(shape=(n, 1))
        H = np.zeros(shape=(4, n))
        x = dx = np.zeros(4)

        ## ==================================================
        ##  remove observations with values equal to .0
        ## ==================================================
        # indx_entry = np.where(dop_obs==0.0)
        # indx       = sum(indx_entry).size
        # if indx > 0:

        # print(dop_obs)
        # sat = valid_sats[indx]
        # logger(f"est_spv_by_doppler():: removing item={indx} with zero values from Doppler observation for sat={sat}")
        ##logger(f"est_spv_by_doppler():: removing item={indx} with zero values from Doppler observation for sat={valid_sats[indx]}")
        # dop_obs = np.delete(dop_obs, indx, None)
        # valid_sats= np.delete(valid_sats,indx, None)

        # loop until convergence
        i_max_iter = 10
        for i in range(i_max_iter):

            #  Step 2: compute the Doppler residuals
            nv = self.compute_doppler_res(dop_obs, sat_pos, sat_vel, sat_dts, rcv_pos, x, Az, El, valid_sats)
            if nv < 4:
                logger(f"est_spv_by_doppler():: number of valid satellites={nv:2d} is less that {n_parms}")
                break

            # ==============================================================
            # Step 3:   Least Square Estimation (LSE)
            #           v, H  are update by method compute_doppler_res()
            # ===============================================================
            v = self.v
            H = self.H
            H = H[0:nv, 0:n_parms]  # remove unwanted entries from design matrix H

            # logger(f"est_spv_by_doppler(): Lest square info ....")
            # print(np.shape(H))
            # print(np.shape(v))

            H_m, H_n = H.shape
            v_b = np.atleast_1d(v)

            if v_b.size != H_m:
                logger(
                    f"est_spv_by_doppler():: lsq_linear() Inconsistent shapes between design matrix H and residual vector v"
                )
            else:
                res = lsq_linear(H, v, lsmr_tol="auto", verbose=0)
                if res.success:

                    # update velocity and check for convergence
                    dx = res.x
                    Qx = np.linalg.inv(H.T @ H)
                    x += dx

                    # ========================================
                    #   User output
                    # ========================================
                    b_debug = False
                    if b_debug:
                        logger(f"\n\ncompute_doppler_res():  Design matrix H:")
                        print(H)
                        logger(f"\n\ncompute_doppler_res():  Residual vector v:")
                        print(v)
                        logger(f"\n\n compute_doppler_res(): estimated velocity vector x:")
                        print(x)
                        logger(f"\n\ncompute_doppler_res():  covariance Qx :")
                        print(Qx)

                    # Check for convergence ?
                    if np.linalg.norm(dx) < 1e-7:

                        est_vel = np.linalg.norm(x[0:3])
                        val_sat_cnt = valid_sats.size
                        logger(
                            f"est_spv_by_doppler():: CONVERGENCE  at iteration={i}, valid satellites={val_sat_cnt}. Estimated velocity::{est_vel} [m/s] "
                        )

                        # validate the solution
                        alpha_sig_level = 0.001
                        n_params = 4
                        sol_indicator = self.spv_sol_val(v * 100, alpha_sig_level, n_params, logger)
                        # if(sol_indicator):

                        time.sleep(0.1)
                        self.sol_val = sol_indicator
                        self.x = x
                        self.dx = dx
                        self.Qx = Qx
                        return

                else:
                    logger(f"est_spv_by_doppler():: lsq_linear() failed to compute the velocity solution ")
                    continue

        if i == (i_max_iter - 1):
            logger(f"est_spv_by_doppler():: NO CONVERGENCE .......")
            print(x)
            print(dx)
            self.x = x


# ==========================================================================
# E_1 = E
# rcv_pos_obj=Position(rcv_pos[None, :], system="trs")
# rcv_llh_1= np.squeeze(np.array(rcv_pos_obj.llh))
# E_1 = self.xyz2enu_transf_mat(rcv_llh_1, logger)

# ====================================================================================
# return lat, lon, and alt of a rfeceiver  located on Earth giventhe ECEF coordinates
# ====================================================================================
