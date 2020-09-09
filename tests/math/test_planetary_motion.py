""" Tests for the midgard.math.planetary_motion module"""

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import time
from midgard.math import planetary_motion


def t_jd_gps():
    """Time, format julian date, scale gps"""
    return time.Time(2457448.5, scale="gps", fmt="jd")


def test_findsun():
    sun_pos = planetary_motion.findsun(t_jd_gps())
    expected_sun_pos = np.array([-148102175.801620, -7980320.884334, -19534142.160482])
    np.testing.assert_allclose(sun_pos, expected_sun_pos, rtol=0, atol=1e-6)
    # print('OUTPUT:\n findsun = {:f} {:f} {:f} \n'.format(sun_pos[0], sun_pos[1], sun_pos[2]))


def test_gsdtime_sun():

    gstr, slong, sra, sdec = planetary_motion.gsdtime_sun(t_jd_gps())
    expected_gstr = np.array([159.228953])
    expected_slong = np.array([340.840280])
    expected_sra = np.array([342.313290])
    expected_sdec = np.array([-7.502975])

    np.testing.assert_allclose(gstr, expected_gstr, rtol=0, atol=1e-6)
    np.testing.assert_allclose(slong, expected_slong, rtol=0, atol=1e-6)
    np.testing.assert_allclose(sra, expected_sra, rtol=0, atol=1e-6)
    np.testing.assert_allclose(sdec, expected_sdec, rtol=0, atol=1e-6)
    # print(f"OUTPUT:\n gsdtime_sun = {gstr} {slong} {sra} {sdec} \n")
