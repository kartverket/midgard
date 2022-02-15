"""Tests for the gnss.antenna_calibration-module

Example:
--------
    python -m pytest test_antenna_calibration.py -s

Note: If '-s' option is used by calling pytest, then also debug messages are printed.
"""
# Standard library imports
from datetime import datetime

# Third party imports
import pytest
import numpy as np

# Midgard imports
from midgard.gnss.antenna_calibration import AntennaCalibration


#
# TEST DATA
#
@pytest.fixture
def ant():
    """Generate AntennaCalibration object by reading example ANTEX file"""
    return AntennaCalibration(file_path="../parsers/example_files/antex")

    
#
# TEST CLASS METHODS
#
@pytest.mark.parametrize("system, frequency, antenna, radome, expected_pco", [
                ("G", "L1", "AERAT1675_120", "SPKE", np.array([-0.00001 , 0.00057, 0.08051])), 
])
def test_get_pco_rcv(ant, system, frequency, antenna, radome, expected_pco):
    """Test of get_pco_rcv() function
    """
    pco = ant.get_pco_rcv(system, frequency, antenna, radome)
        
    np.testing.assert_allclose(pco, expected_pco, rtol=0, atol=1e-5)
    
    
@pytest.mark.parametrize("date, system, frequency, satellite, expected_pco", [
                (datetime(1993, 2, 1), "G", "L1", "G01", np.array([0.279 , 0.0, 2.3195])), 
                (datetime(1993, 2, 1), "G", ["L1", "L2"], "G01", np.array([0.279 , 0.0, 2.3195])),
])
def test_get_pco_sat(ant, date, system, frequency, satellite, expected_pco):
    """Test of get_pco_sat() function
    """
    pco = ant.get_pco_sat(date, system, frequency, satellite)     
    np.testing.assert_allclose(pco, expected_pco, rtol=0, atol=1e-5)
    
    
@pytest.mark.parametrize("date, satellite", [(datetime(1993, 2, 1), "G01")])
def test_get_satellite_info(ant, date, satellite):
    """Test of get_satellite_info() function
    """
    info = ant.get_satellite_info(date, satellite)
    assert info["sat_type"] == "BLOCK IIA"
    assert info["sat_code"] == "G032"
    assert info["cospar_id"] == "1992-079A"
     
    
@pytest.mark.parametrize("date, satellite", [
                    (datetime(1993, 2, 1), "G01"),
                    (datetime(1993, 2, 1), ["G01"]),
                    (datetime(1993, 2, 1), np.array(["G01"])),
])
def test_get_satellite_type(ant, date, satellite):
    """Test of get_satellite_type() function
    """
    type_ = ant.get_satellite_type(date, satellite)
    assert type_[0] == "BLOCK IIA" 


#
# TEST AUXILIARY FUNCTIONS
#
@pytest.mark.parametrize("system, freq_num, expected_freq_name", [
                    ("C", "2", "B1"),
                    ("G", "1", "L1"),
                    ("R", "1", "G1"),
                    ("E", "1", "E1"),
                    ("I", "5", "L5"),
                    ("J", "1", "L1"),
                    ("S", "1", "L1"),
])
def test__freq_num_to_freq_name(ant, system, freq_num, expected_freq_name):
    """Test of _freq_num_to_freq_name() function
    """
    freq_name = ant._freq_num_to_freq_name(system, freq_num)
    assert freq_name == expected_freq_name
    
    
@pytest.mark.parametrize("system, frequency, expected_antex_freq", [
                    ("C", "B1", "C02"),
                    ("G", "L1", "G01"),
                    ("E", "E1", "E01"),
                    ("I", "L5", "I05"),
                    ("J", "L1", "J01"),
                    ("S", "L1", "S01"),
])
def test__gnss_to_antex_freq(ant, system, frequency, expected_antex_freq):
    """Test of _gnss_to_antex_freq() function
    """
    antex_freq = ant._gnss_to_antex_freq(system, frequency)
    assert antex_freq == expected_antex_freq
    
    
@pytest.mark.parametrize("date, satellite, expected_used_date", [
                    (datetime(1993, 2, 1), "G01", datetime(1992, 11, 22)),
])
def test__used_date(ant, date, satellite, expected_used_date):
    """Test of _used_date() function
    """
    used_date = ant._used_date(date, satellite)
    assert used_date == expected_used_date
