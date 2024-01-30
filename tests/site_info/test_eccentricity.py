"""Tests for the site_info.eccentricity

Note: pytest can be started with commando:
    python -m pytest -s test_eccentricity.py

"""

import datetime
import pytest
import numpy as np

from midgard.dev.exceptions import MissingDataError
from midgard.site_info.eccentricity import Eccentricity

# Tests: Eccentricity.get("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_one_station(sinex_data):
    e = Eccentricity.get("snx", sinex_data, "zimm", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "zimm" in e
    assert len(e) == 1
    
    # Test eccentricity information
    assert e["zimm"].date_from == datetime.datetime(1993, 5, 1, 0, 0)
    assert e["zimm"].date_to == datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)
    assert e["zimm"].station == 'zimm'
    #np.testing.assert_allclose(e["zimm"].dpos.trs.val, np.array([0.01, 0.03, 0.02]), rtol=0, atol=1e-3)
    np.testing.assert_allclose(e["zimm"].dpos, np.array([0.03, 0.02, 0.01]), rtol=0, atol=1e-3)

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_one_station_uppercase(sinex_data):
    e = Eccentricity.get("snx", sinex_data, "ZIMM", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "zimm" in e
    assert len(e) == 1

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_two_stations_string(sinex_data):
    e = Eccentricity.get("snx", sinex_data, "zimm, hrao", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "zimm" in e
    assert "hrao" in e
    assert len(e) == 2

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_two_stations_list(sinex_data):
    e = Eccentricity.get("snx", sinex_data, ["zimm", "hrao"], datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
    assert "zimm" in e
    assert "hrao" in e
    assert len(e) == 2
    
@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        e = Eccentricity.get("snx", sinex_data, "xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        e = Eccentricity.get("snx", sinex_data, "zimm,xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/sinex")
        
@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_last_entry(sinex_data):
    e = Eccentricity.get("snx", sinex_data, "zimm", "last", source_path="/path/to/sinex")
    assert "zimm" in e
    assert e["zimm"].date_to == datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)

# Tests: Eccentricity.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_one_station(sinex_data):
    e = Eccentricity.get_history("snx", sinex_data, "zimm", source_path="/path/to/sinex")
    assert "zimm" in e
    assert len(e) == 1
    
    # Test eccentricity history information
    assert len(e["zimm"].history) == 1
    assert len(e["zimm"].date_from) == 1
    assert len(e["zimm"].date_to) == 1

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_two_stations_string(sinex_data):
    e = Eccentricity.get_history("snx", sinex_data, "zimm, hrao", source_path="/path/to/sinex")
    assert "zimm" in e
    assert "hrao" in e
    assert len(e) == 2

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_two_stations_list(sinex_data):
    e = Eccentricity.get_history("snx", sinex_data, ["zimm", "hrao"], source_path="/path/to/sinex")
    assert "zimm" in e
    assert "hrao" in e
    assert len(e) == 2
    
@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        e = Eccentricity.get_history("snx", sinex_data, "xxxx", source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        e = Eccentricity.get_history("snx", sinex_data, "zimm,xxxx", source_path="/path/to/sinex")

# Tests: Eccentricity.get("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_one_station(ssc_data):
    e = Eccentricity.get("ssc", ssc_data, "gras", datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")
    assert "gras" in e
    assert len(e) == 1
    
    # Test eccentricity information
    assert e["gras"] is None

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_two_stations_string(ssc_data):
    e = Eccentricity.get("ssc", ssc_data, "gras, borr", datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")
    assert "gras" in e
    assert "borr" in e
    assert len(e) == 2

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_two_stations_list(ssc_data):
    e = Eccentricity.get("ssc", ssc_data, ["gras", "borr"], datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")
    assert "gras" in e
    assert "borr" in e
    assert len(e) == 2

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        e = Eccentricity.get("ssc", ssc_data, "xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        e = Eccentricity.get("ssc", ssc_data, "zimm,xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/ssc")

# Tests: Eccentricity.get_history("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_one_station(ssc_data):
    e = Eccentricity.get_history("ssc", ssc_data, "gras", source_path="/path/to/ssc")
    assert "gras" in e
    assert len(e) == 1
    
    # Test eccentricity history information
    assert e["gras"].history is None
    assert e["gras"].date_from is None
    assert e["gras"].date_to is None

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_two_stations_string(ssc_data):
    e = Eccentricity.get_history("ssc", ssc_data, "gras, borr", source_path="/path/to/ssc")
    assert "gras" in e
    assert "borr" in e
    assert len(e) == 2

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_two_stations_list(ssc_data):
    e = Eccentricity.get_history("ssc", ssc_data, ["gras", "borr"], source_path="/path/to/ssc")
    assert "gras" in e
    assert "borr" in e
    assert len(e) == 2

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        e = Eccentricity.get_history("ssc", ssc_data, "xxxx", source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        e = Eccentricity.get_history("ssc", ssc_data, "zimm,xxxx", source_path="/path/to/ssc")

# Tests: Eccentricity.get("m3g",...)

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_m3g_one_station(m3g_api):
    a = Eccentricity.get("m3g", m3g_api, "osls", datetime.datetime(2020, 1, 1), source_path="/path/to/api")
    assert "osls" in a
    assert len(a) == 1

    # Test eccentricity information
    assert a["osls"].date_from.date() == datetime.date(2007, 4, 23)
    assert a["osls"].date_to.date() == datetime.date(9999, 12, 31)
    assert a["osls"].station == 'osls'
    #np.testing.assert_allclose(a["osls"].dpos.trs.val, np.array([5.496, 0.013, 0.017]), rtol=0, atol=1e-3)
    np.testing.assert_allclose(a["osls"].dpos, np.array([0.013, 0.017, 5.496]), rtol=0, atol=1e-3)

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_m3g_two_stations_string(m3g_api):
    a = Eccentricity.get("m3g", m3g_api, "osls, trds", datetime.datetime(2020, 1, 1), source_path="/path/to/api")
    assert "osls" in a
    assert "trds" in a
    assert len(a) == 2

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_m3g_two_stations_list(m3g_api):
    a = Eccentricity.get("m3g", m3g_api, ["osls", "trds"], datetime.datetime(2020, 1, 1), source_path="/path/to/api")
    assert "osls" in a
    assert "trds" in a
    assert len(a) == 2

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_m3g_one_station_error(m3g_api):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get("m3g", m3g_api, "xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/api")

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_m3g_two_stations_error(m3g_api):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get("m3g", m3g_api, "osls, xxxx", datetime.datetime(2020, 1, 1), source_path="/path/to/api")

# Tests: Eccentricity.get_history("m3g",...)

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_history_m3g_one_station(m3g_api):
    a = Eccentricity.get_history("m3g", m3g_api, "osls", source_path="/path/to/api")
    assert "osls" in a
    assert len(a) == 1

    # Test eccentricity history information
    assert len(a["osls"].history) >= 2
    assert len(a["osls"].date_from) >= 2
    assert len(a["osls"].date_to) >= 2

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_history_m3g_two_stations_string(m3g_api):
    a = Eccentricity.get_history("m3g", m3g_api, "osls, trds", source_path="/path/to/api")
    assert "osls" in a
    assert "trds" in a
    assert len(a) == 2

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_history_m3g_two_stations_list(m3g_api):
    a = Eccentricity.get_history("m3g", m3g_api, ["osls", "trds"], source_path="/path/to/api")
    assert "osls" in a
    assert "trds" in a
    assert len(a) == 2

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_history_m3g_one_station_error(m3g_api):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get_history("m3g", m3g_api, "xxxx", source_path="/path/to/api")

@pytest.mark.usefixtures("m3g_api")
def test_eccentricity_history_m3g_two_stations_error(m3g_api):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get_history("m3g", m3g_api, "osls, xxxx", source_path="/path/to/api")
