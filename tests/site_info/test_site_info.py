import datetime
import pytest

from midgard.site_info import site_info

# Tests: SiteInfo.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_one_station(sinex_data):
    si = site_info.SiteInfo.get_history("snx", "zimm", sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    assert len(si) == 1
    #TODO: Check content

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_two_station_string(sinex_data):
    si = site_info.SiteInfo.get_history("snx", "zimm,hrao", sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    assert len(si) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_two_station_list(sinex_data):
    si = site_info.SiteInfo.get_history("snx", ["zimm","hrao"], sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    assert len(si) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_one_station_error(sinex_data):
    # station xxxx does not exist
    with pytest.raises(ValueError):
        si = site_info.SiteInfo.get_history("snx", "xxxx", sinex_data, source_path="path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_info_history_sinex_two_stations_string_error(sinex_data):
    # station xxxx does not exist
    #TODO: what is the desired behaviour
    with pytest.raises(ValueError):
        si = site_info.SiteInfo.get_history("snx", "xxxx, osls", sinex_data, source_path="path/to/sinex")

# Tests: SiteInfo.get("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_one_station(sinex_data):
    si = site_info.SiteInfo.get("snx", "zimm", datetime.datetime(2020, 1, 1), sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    assert len(si) == 1
    #TODO: Check content

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_two_station_string(sinex_data):
    si = site_info.SiteInfo.get("snx", "zimm,hrao", datetime.datetime(2020, 1, 1), sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    assert len(si) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_two_station_list(sinex_data):
    si = site_info.SiteInfo.get("snx", ["zimm","hrao"], datetime.datetime(2020, 1, 1), sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    assert len(si) == 2

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_one_station_error(sinex_data):
    # station xxxx does not exist
    with pytest.raises(ValueError):
        si = site_info.SiteInfo.get("snx", "xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex_two_stations_string_error(sinex_data):
    # station xxxx does not exist
    #TODO: what is the desired behaviour
    with pytest.raises(ValueError):
        si = site_info.SiteInfo.get("snx", "xxxx, osls", datetime.datetime(2020, 1, 1), sinex_data, source_path="path/to/sinex")

# Tests: SiteInfo.get_history("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_scc_one_station(ssc_data):
    si = site_info.SiteInfo.get_history("ssc", "gras", ssc_data, source_path="path/to/ssc")
    assert "gras" in si
    assert len(si) == 1
    #TODO: Check content

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_sinex_two_station_string(ssc_data):
    si = site_info.SiteInfo.get_history("ssc", "gras,borr", ssc_data, source_path="path/to/ssc")
    assert "gras" in si
    assert "borr" in si
    assert len(si) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_sinex_two_station_list(ssc_data):
    si = site_info.SiteInfo.get_history("ssc", ["gras","borr"], ssc_data, source_path="path/to/ssc")
    assert "gras" in si
    assert "borr" in si
    assert len(si) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_sinex_one_station_error(ssc_data):
    # station xxxx does not exist
    with pytest.raises(ValueError):
        si = site_info.SiteInfo.get_history("ssc", "xxxx", ssc_data, source_path="path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_info_history_sinex_two_stations_string_error(ssc_data):
    # station xxxx does not exist
    #TODO: what is the desired behaviour
    with pytest.raises(ValueError):
        si = site_info.SiteInfo.get_history("ssc", "xxxx, borr", ssc_data, source_path="path/to/ssc")

# Tests: SiteInfo.get("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_one_station(ssc_data):
    si = site_info.SiteInfo.get("ssc", "gras", datetime.datetime(2020, 1, 1), ssc_data, source_path="path/to/ssc")
    assert "gras" in si
    assert len(si) == 1
    #TODO: Check content

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_two_station_string(ssc_data):
    si = site_info.SiteInfo.get("ssc", "gras,borr", datetime.datetime(2020, 1, 1), ssc_data, source_path="path/to/ssc")
    assert "gras" in si
    assert "borr" in si
    assert len(si) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_two_station_list(ssc_data):
    si = site_info.SiteInfo.get("ssc", ["gras","borr"], datetime.datetime(2020, 1, 1), ssc_data, source_path="path/to/ssc")
    assert "gras" in si
    assert "borr" in si
    assert len(si) == 2

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_one_station_error(ssc_data):
    # station xxxx does not exist
    with pytest.raises(ValueError):
        si = site_info.SiteInfo.get("ssc", "xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_info_ssc_two_stations_string_error(ssc_data):
    # station xxxx does not exist
    #TODO: what is the desired behaviour
    with pytest.raises(ValueError):
        si = site_info.SiteInfo.get("ssc", "xxxx, borr", datetime.datetime(2020, 1, 1), ssc_data, source_path="path/to/ssc")
