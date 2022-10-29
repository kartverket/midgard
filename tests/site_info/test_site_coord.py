"""Tests for the site_info.site_coord

Note: pytest can be started with commando:
    python -m pytest -s test_site_coord.py

"""

import datetime
import pytest

import numpy as np

from midgard.dev.exceptions import MissingDataError
from midgard.site_info.site_coord import SiteCoord, SiteCoordHistorySinex, SiteCoordHistorySsc

# Tests: SiteCoord.get("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_one_station(sinex_data):
    c = SiteCoord.get("snx", sinex_data, "zimm", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "zimm" in c
    assert len(c) == 1
    
    # Test site coord information
    assert c["zimm"] is None

@pytest.mark.usefixtures("sinex_data_site_coord")
def test_site_coord_sinex_one_station_with_data(sinex_data_site_coord):
    c = SiteCoord.get("snx", sinex_data_site_coord, "kiri", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "kiri" in c
    assert len(c) == 1
    
    # Test site coord information
    assert c["kiri"].station == 'kiri'
    assert c["kiri"].date_from == datetime.datetime(2015, 4, 28, 0, 0)
    assert c["kiri"].date_to == datetime.datetime(2020, 4, 12, 12, 0)
    assert np.allclose(c["kiri"].pos.val, np.array([-6327822.40890791,   785604.50573119,   149769.23973976]))
    assert np.allclose(c["kiri"].pos_sigma, np.array([0.00042754, 0.00012964, 0.00010695]))
    assert np.allclose(c["kiri"].vel, np.array([0.00915987, 0.06720133, 0.03124394]))
    assert np.allclose(c["kiri"].vel_sigma, np.array([5.0865e-05, 1.5316e-05, 1.2724e-05]))
    assert c["kiri"].ref_epoch.datetime, datetime.datetime(2010, 1, 1, 0, 0)
    assert c["kiri"].system is None

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_one_station_uppercase(sinex_data):
    c = SiteCoord.get("snx", sinex_data, "ZIMM", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "zimm" in c
    assert len(c) == 1

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_two_stations_string(sinex_data):
    c = SiteCoord.get("snx", sinex_data, "zimm, hrao", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "zimm" in c
    assert "hrao" in c
    assert len(c) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_two_stations_list(sinex_data):
    c = SiteCoord.get("snx", sinex_data, ["zimm", "hrao"], datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "zimm" in c
    assert "hrao" in c
    assert len(c) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get("snx", sinex_data, "xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get("snx", sinex_data, "zimm,xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")

# Tests: SiteCoord.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_one_station(sinex_data):
    c = SiteCoord.get_history("snx", sinex_data, "zimm", source_path="/path/to/sinex")
    assert "zimm" in c
    assert len(c) == 1

    # Test site coord history information
    assert c["zimm"].history is None
    assert c["zimm"].date_from is None
    assert c["zimm"].date_to is None

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_two_stations_string(sinex_data):
    c = SiteCoord.get_history("snx", sinex_data, "zimm, hrao", source_path="/path/to/sinex")
    assert "zimm" in c
    assert "hrao" in c
    assert len(c) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_two_stations_list(sinex_data):
    c = SiteCoord.get_history("snx", sinex_data, ["zimm", "hrao"], source_path="/path/to/sinex")
    assert "zimm" in c
    assert "hrao" in c
    assert len(c) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get_history("snx", sinex_data, "xxxx", source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get_history("snx", sinex_data, "zimm,xxxx", source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data_site_coord")
def test_site_coord_history_sinex_set_history(sinex_data_site_coord):
    
    # Get history data and set history
    c = SiteCoordHistorySinex("kiri")   
    raw_info = c._combine_sinex_block_data(sinex_data_site_coord["kiri"])
    c.set_history(raw_info)
    
    # Check history
    period = (datetime.datetime(2002, 8, 3, 0, 0), datetime.datetime(2011, 11, 20, 23, 59, 30))
    assert period in c.history
    assert "snx" == c.history[period].source
    assert -6327822.41344055 == c.history[period].pos.x

#
# Tests: SiteCoord.get("ssc",...)
#
        
@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_one_station(ssc_data):
    c = SiteCoord.get("ssc", ssc_data, "gras", datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")
    assert "gras" in c
    assert len(c) == 1
    
    # Test site coord information
    assert c["gras"].station == 'gras'
    assert np.allclose(c["gras"].pos.val, np.array([4581690.831,  556114.93 , 4389360.851]))
    assert np.allclose(c["gras"].pos_sigma, np.array([0.001, 0.001, 0.001]))
    assert np.allclose(c["gras"].vel, np.array([-0.0137,  0.0189,  0.0115]))
    assert np.allclose(c["gras"].vel_sigma, np.array([0.0001, 0.0001, 0.0001]))
    assert c["gras"].system is None
    assert c["gras"].ref_epoch.datetime == datetime.datetime(2010, 1, 1, 0, 0)
    assert c["gras"].date_from == datetime.datetime(2004, 10, 22, 0, 0)
    assert c["gras"].date_to == datetime.datetime(2021, 2, 20, 23, 59, 30)


@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_two_stations_string(ssc_data):
    c = SiteCoord.get("ssc", ssc_data, "gras, borr", datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")
    assert "gras" in c
    assert "borr" in c
    assert len(c) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_two_stations_list(ssc_data):
    c = SiteCoord.get("ssc", ssc_data, ["gras", "borr"], datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")
    assert "gras" in c
    assert "borr" in c
    assert len(c) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get("ssc", ssc_data, "xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get("ssc", ssc_data, "gras, xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")
        
@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_last_entry(sinex_data):
    c = SiteCoord.get("snx", sinex_data, "zimm", "last", source_path="/path/to/sinex")
    assert "zimm" in c
    #TODO assert c["zimm"].date_to == datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)

# Tests: SiteCoord.get_history("ssc",...)
        
@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_one_station(ssc_data):
    c = SiteCoord.get_history("ssc", ssc_data, "gras", source_path="/path/to/ssc")
    assert "gras" in c
    assert len(c) == 1
    
    # Test site coord history information
    assert len(c["gras"].history) == 4
    assert len(c["gras"].date_from) == 4
    assert len(c["gras"].date_to) == 4

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_two_stations_string(ssc_data):
    c = SiteCoord.get_history("ssc", ssc_data, "gras, borr", source_path="/path/to/ssc")
    assert "gras" in c
    assert "borr" in c
    assert len(c) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_two_stations_list(ssc_data):
    c = SiteCoord.get_history("ssc", ssc_data, ["gras", "borr"], source_path="/path/to/ssc")
    assert "gras" in c
    assert "borr" in c
    assert len(c) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get_history("ssc", ssc_data, "xxxx", source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get_history("ssc", ssc_data, "gras, xxxx", source_path="/path/to/ssc")
        
@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_set_history(ssc_data):
    
    # Get history data and set history
    c = SiteCoordHistorySsc("gras")  
    c.set_history(ssc_data["GRAS"])
 
    # Check history
    period = (datetime.datetime(1996, 1, 1, 0, 0), datetime.datetime(1996, 5, 6, 23, 59, 30))
    assert period in c.history
    assert "ssc" == c.history[period].source
    assert 4581690.826 == c.history[period].pos.x

