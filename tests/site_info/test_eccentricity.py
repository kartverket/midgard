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
    np.testing.assert_allclose(e["zimm"].dpos.trs.val, np.array([0.01, 0.03, 0.02]), rtol=0, atol=1e-3)
    np.testing.assert_allclose(e["zimm"].dpos.enu.val, np.array([0.03, 0.02, 0.01]), rtol=0, atol=1e-3)

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
