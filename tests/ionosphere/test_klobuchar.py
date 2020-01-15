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
        0.143e06,
        0.0,
        -0.328e06,
        0.113e06,  # beta coefficients
    ]
    rec_pos = [0.698131701, 4.53785606, 0.0]
    az = 3.66519143
    el = 0.34906585
    freq_l1 = 1575420000.0
    freq = 1575420000.0

    # +gLAB validation test
    # PRN15, epoch
    # -input:obs /home/dahmic/where/data/gnss/obs/2018/032/stas0320.18o
    # -input:nav /home/dahmic/where/data/gnss/orb/brdc/2018/032/brdm0320.18p  (added ionosphere parameters)
    # -input:dcb /home/dahmic/where/data/gnss/orb/brdc/2018/032/brdm0320.18p
    # t = 432000.0
    # ion_coeffs = [8.381900e-09, -7.450600e-09, -5.960500e-08, 5.960500e-08, 8.806400e+04, -3.276800e+04, -1.966100e+05, 1.966100e+05]
    # rec_pos = [3275753.912000, 321110.865100, 5445041.882900]
    # az = 0.159409
    # el = 1.171217
    # freq_l1 = 1575420000.0
    # freq = 1575420000.0
    # -gLAB validation test

    delay, _ = klobuchar.klobuchar(t, ion_coeffs, rec_pos, az, el, freq_l1, freq)
    # expected: delay = 23.784 m
    expected = 23.784

    assert abs(delay - expected) < 1e-3
