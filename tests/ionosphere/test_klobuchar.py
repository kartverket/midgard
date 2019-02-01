"""Tests for the math.klobuchar-module

"""
from midgard.ionosphere import klobuchar


def test_klobuchar():
    # Comparison are done against GPS-Toolbox Klobuchar programs from Ola Ovstedal
    # https://www.ngs.noaa.gov/gps-toolbox/ovstedal.htm
    t = 593100
    ion_coeffs = [
        0.382e-07,
        0.149e-07,
        -0.179e-06,
        0.0,  # alpha coefficients
        0.143e+06,
        0.0,
        -0.328e+06,
        0.113e+06,  # beta coefficients
    ]
    rec_pos = [0.698131701, 4.53785606, 0.0]
    az = 3.66519143
    el = 0.34906585
    freq_l1 = 1575420000.0
    freq = 1575420000.0

    delay, _ = klobuchar.klobuchar(t, ion_coeffs, rec_pos, az, el, freq_l1, freq)
    # expected: delay = 23.784 m
    expected = 23.784

    assert abs(delay - expected) < 1e-3
