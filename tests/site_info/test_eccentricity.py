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
    a = Eccentricity.get("snx", "zimm", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert len(a) == 1
    
    # Test eccentricity information
    assert a["zimm"].date_from == datetime.datetime(1993, 5, 1, 0, 0)
    assert a["zimm"].date_to == datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)
    assert a["zimm"].station == 'zimm'
    np.testing.assert_allclose(a["zimm"].dpos.trs.val, np.array([0.01, 0.03, 0.02]), rtol=0, atol=1e-3)
    np.testing.assert_allclose(a["zimm"].dpos.enu.val, np.array([0.03, 0.02, 0.01]), rtol=0, atol=1e-3)

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_one_station_uppercase(sinex_data):
    a = Eccentricity.get("snx", "ZIMM", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert len(a) == 1

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_two_stations_string(sinex_data):
    a = Eccentricity.get("snx", "zimm, hrao", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_two_stations_list(sinex_data):
    a = Eccentricity.get("snx", ["zimm", "hrao"], datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2
    
@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get("snx", "xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get("snx", "zimm,xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")

# Tests: Eccentricity.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_one_station(sinex_data):
    a = Eccentricity.get_history("snx", "zimm", sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert len(a) == 1
    
    # Test eccentricity history information
    assert len(a["zimm"].history) == 1
    assert len(a["zimm"].date_from) == 1
    assert len(a["zimm"].date_to) == 1

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_two_stations_string(sinex_data):
    a = Eccentricity.get_history("snx", "zimm, hrao", sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_two_stations_list(sinex_data):
    a = Eccentricity.get_history("snx", ["zimm", "hrao"], sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2
    
@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get_history("snx", "xxxx", sinex_data, source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_eccentricity_history_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get_history("snx", "zimm,xxxx", sinex_data, source_path="/path/to/sinex")

# Tests: Eccentricity.get("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_one_station(ssc_data):
    a = Eccentricity.get("ssc", "gras", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert len(a) == 1
    
    # Test eccentricity information
    assert a["gras"] is None

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_two_stations_string(ssc_data):
    a = Eccentricity.get("ssc", "gras, borr", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_two_stations_list(ssc_data):
    a = Eccentricity.get("ssc", ["gras", "borr"], datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get("ssc", "xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get("ssc", "zimm,xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")

# Tests: Eccentricity.get_history("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_one_station(ssc_data):
    a = Eccentricity.get_history("ssc", "gras", ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert len(a) == 1
    
    # Test eccentricity history information
    assert a["gras"].history is None
    assert a["gras"].date_from is None
    assert a["gras"].date_to is None

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_two_stations_string(ssc_data):
    a = Eccentricity.get_history("ssc", "gras, borr", ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_two_stations_list(ssc_data):
    a = Eccentricity.get_history("ssc", ["gras", "borr"], ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get_history("ssc", "xxxx", ssc_data, source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_eccentricity_history_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Eccentricity.get_history("ssc", "zimm,xxxx", ssc_data, source_path="/path/to/ssc")
