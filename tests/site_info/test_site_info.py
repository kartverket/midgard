"""Tests for the site_info.site_info

Note: pytest can be started with commando:
    python -m pytest -s test_site_info.py

"""

import datetime
import pytest

from midgard.dev.exceptions import MissingDataError
from midgard.site_info import site_info


# Tests: SiteInfo.get("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_one_station(sinex_data):
    si = site_info.SiteInfo.get("snx", sinex_data, "zimm", datetime.datetime(2020, 1, 1), source_path="path/to/sinex")
    assert "zimm" in si
    assert len(si) == 1
    
    assert "antenna" in si["zimm"]
    assert "eccentricity" in si["zimm"]
    assert "identifier" in si["zimm"]
    assert "receiver" in si["zimm"]
    assert "site_coord" in si["zimm"]

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_two_station_string(sinex_data):
    si = site_info.SiteInfo.get("snx", sinex_data, "zimm,hrao", datetime.datetime(2020, 1, 1), source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    assert len(si) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_two_station_list(sinex_data):
    si = site_info.SiteInfo.get("snx", sinex_data, ["zimm","hrao"], datetime.datetime(2020, 1, 1), source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    assert len(si) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_one_station_error(sinex_data):
    # station xxxx does not exist
    with pytest.raises(MissingDataError):
        si = site_info.SiteInfo.get("snx", sinex_data, "xxxx", datetime.datetime(2020, 1, 1), source_path="path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_two_stations_string_error(sinex_data):
    # station xxxx does not exist
    #TODO: what is the desired behaviour
    with pytest.raises(MissingDataError):
        si = site_info.SiteInfo.get("snx", sinex_data, "xxxx, osls", datetime.datetime(2020, 1, 1), source_path="path/to/sinex")
        
@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_last_entry(sinex_data):
    si = site_info.SiteInfo.get("snx", sinex_data, "zimm", "last", source_path="/path/to/sinex")
    assert "zimm" in si
    assert si["zimm"]["antenna"].date_to == datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)

# Tests: SiteInfo.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_one_station(sinex_data):
    si = site_info.SiteInfo.get_history("snx", sinex_data, "zimm", source_path="path/to/sinex")
    assert "zimm" in si
    assert len(si) == 1

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_one_station_uppercase(sinex_data):
    si = site_info.SiteInfo.get_history("snx", sinex_data, "ZIMM", source_path="path/to/sinex")
    assert "zimm" in si
    assert len(si) == 1

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_two_station_string(sinex_data):
    si = site_info.SiteInfo.get_history("snx", sinex_data, "zimm,hrao", source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    assert len(si) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_two_station_list(sinex_data):
    si = site_info.SiteInfo.get_history("snx", sinex_data, ["zimm","hrao"], source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    assert len(si) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_one_station_error(sinex_data):
    # station xxxx does not exist
    with pytest.raises(MissingDataError):
        si = site_info.SiteInfo.get_history("snx", sinex_data, "xxxx", source_path="path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_two_stations_string_error(sinex_data):
    # station xxxx does not exist
    with pytest.raises(MissingDataError):
        si = site_info.SiteInfo.get_history("snx", sinex_data, "xxxx, osls", source_path="path/to/sinex")

# Tests: SiteInfo.get("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_one_station(ssc_data):
    si = site_info.SiteInfo.get("ssc", ssc_data, "gras", datetime.datetime(2020, 1, 1), source_path="path/to/ssc")
    assert "gras" in si
    assert len(si) == 1

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_two_station_string(ssc_data):
    si = site_info.SiteInfo.get("ssc", ssc_data, "gras,borr", datetime.datetime(2020, 1, 1), source_path="path/to/ssc")
    assert "gras" in si
    assert "borr" in si
    assert len(si) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_two_station_list(ssc_data):
    si = site_info.SiteInfo.get("ssc", ssc_data, ["gras","borr"], datetime.datetime(2020, 1, 1), source_path="path/to/ssc")
    assert "gras" in si
    assert "borr" in si
    assert len(si) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_one_station_error(ssc_data):
    # station xxxx does not exist
    with pytest.raises(MissingDataError):
        si = site_info.SiteInfo.get("ssc", ssc_data, "xxxx", datetime.datetime(2020, 1, 1), source_path="path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_two_stations_string_error(ssc_data):
    # station xxxx does not exist
    with pytest.raises(MissingDataError):
        si = site_info.SiteInfo.get("ssc", ssc_data, "xxxx, borr", datetime.datetime(2020, 1, 1), source_path="path/to/ssc")

# Tests: SiteInfo.get_history("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_scc_one_station(ssc_data):
    si = site_info.SiteInfo.get_history("ssc", ssc_data, "gras", source_path="path/to/ssc")
    assert "gras" in si
    assert len(si) == 1

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_ssc_two_station_string(ssc_data):
    si = site_info.SiteInfo.get_history("ssc", ssc_data, "gras,borr", source_path="path/to/ssc")
    assert "gras" in si
    assert "borr" in si
    assert len(si) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_ssc_two_station_list(ssc_data):
    si = site_info.SiteInfo.get_history("ssc", ssc_data, ["gras","borr"], source_path="path/to/ssc")
    assert "gras" in si
    assert "borr" in si
    assert len(si) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_ssc_one_station_error(ssc_data):
    # station xxxx does not exist
    with pytest.raises(MissingDataError):
        si = site_info.SiteInfo.get_history("ssc", ssc_data, "xxxx", source_path="path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_ssc_two_stations_string_error(ssc_data):
    # station xxxx does not exist
    with pytest.raises(MissingDataError):
        si = site_info.SiteInfo.get_history("ssc", ssc_data, "xxxx, borr", source_path="path/to/ssc")

