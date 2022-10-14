"""Tests for the site_info.identifier

Note: pytest can be started with commando:
    python -m pytest -s test_identifier.py

"""

import pytest

from midgard.dev.exceptions import MissingDataError
from midgard.site_info.identifier import Identifier

# Tests: Identifier.get("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_identifier_sinex_one_station(sinex_data):
    a = Identifier.get("snx", sinex_data, "zimm", source_path="/path/to/sinex")
    assert "zimm" in a
    assert len(a) == 1
        
    # Test identifier information
    assert a["zimm"].county == 'Switzerlan'
    assert a["zimm"].domes == '14001M004'
    assert a["zimm"].name == 'Zimmerwald'

@pytest.mark.usefixtures("sinex_data")
def test_identifier_sinex_one_station_uppercase(sinex_data):
    a = Identifier.get("snx", sinex_data, "ZIMM", source_path="/path/to/sinex")
    assert "zimm" in a
    assert len(a) == 1

@pytest.mark.usefixtures("sinex_data")
def test_identifier_sinex_two_stations_string(sinex_data):
    a = Identifier.get("snx", sinex_data, "zimm, hrao", source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2

@pytest.mark.usefixtures("sinex_data")
def test_identifier_sinex_two_stations_list(sinex_data):
    a = Identifier.get("snx", sinex_data, ["zimm", "hrao"], source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2
    
@pytest.mark.usefixtures("sinex_data")
def test_identifier_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Identifier.get("snx", sinex_data, "xxxx", source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_identifier_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Identifier.get("snx", sinex_data, "zimm,xxxx", source_path="/path/to/sinex")

# Tests: Identifier.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_identifier_history_sinex_one_station(sinex_data):
    a = Identifier.get_history("snx", sinex_data, "zimm", source_path="/path/to/sinex")
    assert "zimm" in a
    assert len(a) == 1
   
@pytest.mark.usefixtures("sinex_data")
def test_identifier_history_sinex_two_stations_string(sinex_data):
    a = Identifier.get_history("snx", sinex_data, "zimm, hrao", source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2

@pytest.mark.usefixtures("sinex_data")
def test_identifier_history_sinex_two_stations_list(sinex_data):
    a = Identifier.get_history("snx", sinex_data, ["zimm", "hrao"], source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2
    
@pytest.mark.usefixtures("sinex_data")
def test_identifier_history_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Identifier.get_history("snx", sinex_data, "xxxx", source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_identifier_history_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Identifier.get_history("snx", sinex_data, "zimm,xxxx", source_path="/path/to/sinex")

# Tests: Identifier.get("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_identifier_ssc_one_station(ssc_data):
    a = Identifier.get("ssc", ssc_data, "gras", source_path="/path/to/ssc")
    assert "gras" in a
    assert len(a) == 1
    
    # Test identifier information
    assert a["gras"].county is None
    assert a["gras"].domes == '10002M006'
    assert a["gras"].name is None
    
@pytest.mark.usefixtures("ssc_data")
def test_identifier_ssc_two_stations_string(ssc_data):
    a = Identifier.get("ssc", ssc_data, "gras, borr", source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_identifier_ssc_two_stations_list(ssc_data):
    a = Identifier.get("ssc", ssc_data, ["gras", "borr"], source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_identifier_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Identifier.get("ssc", ssc_data, "xxxx", source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_identifier_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Identifier.get("ssc", ssc_data, "zimm,xxxx", source_path="/path/to/ssc")

# Tests: Identifier.get_history("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_identifier_history_ssc_one_station(ssc_data):
    a = Identifier.get_history("ssc", ssc_data, "gras", source_path="/path/to/ssc")
    assert "gras" in a
    assert len(a) == 1
    
@pytest.mark.usefixtures("ssc_data")
def test_identifier_history_ssc_two_stations_string(ssc_data):
    a = Identifier.get_history("ssc", ssc_data, "gras, borr", source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_identifier_history_ssc_two_stations_list(ssc_data):
    a = Identifier.get_history("ssc", ssc_data, ["gras", "borr"], source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_identifier_history_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Identifier.get_history("ssc", ssc_data, "xxxx", source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_identifier_history_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Identifier.get_history("ssc", ssc_data, "zimm,xxxx", source_path="/path/to/ssc")
