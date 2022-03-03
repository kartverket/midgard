import datetime
import pytest

import numpy as np

from midgard.dev.exceptions import MissingDataError
from midgard.site_info.site_coord import SiteCoord

# Tests: SiteCoord.get("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_one_station(sinex_data):
    c = SiteCoord.get("snx", "zimm", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in c
    assert len(c) == 1
    
    # Test site coord information
    assert c["zimm"] is None

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_one_station_uppercase(sinex_data):
    c = SiteCoord.get("snx", "ZIMM", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in c
    assert len(c) == 1

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_two_stations_string(sinex_data):
    c = SiteCoord.get("snx", "zimm, hrao", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in c
    assert "hrao" in c
    assert len(c) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_two_stations_list(sinex_data):
    c = SiteCoord.get("snx", ["zimm", "hrao"], datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in c
    assert "hrao" in c
    assert len(c) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get("snx", "xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get("snx", "zimm,xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")

# Tests: SiteCoord.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_one_station(sinex_data):
    c = SiteCoord.get_history("snx", "zimm", sinex_data, source_path="/path/to/sinex")
    assert "zimm" in c
    assert len(c) == 1

    # Test site coord history information
    assert c["zimm"].history is None
    assert c["zimm"].date_from is None
    assert c["zimm"].date_to is None

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_two_stations_string(sinex_data):
    c = SiteCoord.get_history("snx", "zimm, hrao", sinex_data, source_path="/path/to/sinex")
    assert "zimm" in c
    assert "hrao" in c
    assert len(c) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_two_stations_list(sinex_data):
    c = SiteCoord.get_history("snx", ["zimm", "hrao"], sinex_data, source_path="/path/to/sinex")
    assert "zimm" in c
    assert "hrao" in c
    assert len(c) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get_history("snx", "xxxx", sinex_data, source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get_history("snx", "zimm,xxxx", sinex_data, source_path="/path/to/sinex")

# Tests: SiteCoord.get("ssc",...)
        
@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_one_station(ssc_data):
    c = SiteCoord.get("ssc", "gras", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in c
    assert len(c) == 1
    
    # Test site coord information
    assert c["gras"].station == 'gras'
    assert all(c["gras"].pos == np.array([4581690.831,  556114.93 , 4389360.851]))
    assert all(c["gras"].pos_sigma == np.array([0.001, 0.001, 0.001]))
    assert all(c["gras"].vel == np.array([-0.0137,  0.0189,  0.0115]))
    assert all(c["gras"].vel_sigma == np.array([0.0001, 0.0001, 0.0001]))
    assert c["gras"].system is None
    assert c["gras"].ref_epoch.datetime == datetime.datetime(2010, 1, 1, 0, 0)
    assert c["gras"].date_from == datetime.datetime(2004, 10, 22, 0, 0)
    assert c["gras"].date_to == datetime.datetime(2021, 2, 20, 23, 59, 30)


@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_two_stations_string(ssc_data):
    c = SiteCoord.get("ssc", "gras, borr", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in c
    assert "borr" in c
    assert len(c) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_two_stations_list(ssc_data):
    c = SiteCoord.get("ssc", ["gras", "borr"], datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in c
    assert "borr" in c
    assert len(c) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get("ssc", "xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get("ssc", "gras, xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")

# Tests: SiteCoord.get_history("ssc",...)
        
@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_one_station(ssc_data):
    c = SiteCoord.get_history("ssc", "gras", ssc_data, source_path="/path/to/ssc")
    assert "gras" in c
    assert len(c) == 1
    
    # Test site coord history information
    assert len(c["gras"].history) == 4
    assert len(c["gras"].date_from) == 4
    assert len(c["gras"].date_to) == 4

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_two_stations_string(ssc_data):
    c = SiteCoord.get_history("ssc", "gras, borr", ssc_data, source_path="/path/to/ssc")
    assert "gras" in c
    assert "borr" in c
    assert len(c) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_two_stations_list(ssc_data):
    c = SiteCoord.get_history("ssc", ["gras", "borr"], ssc_data, source_path="/path/to/ssc")
    assert "gras" in c
    assert "borr" in c
    assert len(c) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get_history("ssc", "xxxx", ssc_data, source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        c = SiteCoord.get_history("ssc", "gras, xxxx", ssc_data, source_path="/path/to/ssc")
