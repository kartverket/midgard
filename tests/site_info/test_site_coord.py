import datetime
import pytest

from midgard.site_info.site_coord import SiteCoord

# Tests: SiteCoord.get("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_one_station(sinex_data):
    c = SiteCoord.get("snx", "zimm", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
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
    with pytest.raises(ValueError):
        c = SiteCoord.get("snx", "xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(ValueError):
        c = SiteCoord.get("snx", "zimm,xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")

# Tests: SiteCoord.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_one_station(sinex_data):
    c = SiteCoord.get_history("snx", "zimm", sinex_data, source_path="/path/to/sinex")
    assert "zimm" in c
    assert len(c) == 1

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
    with pytest.raises(ValueError):
        c = SiteCoord.get_history("snx", "xxxx", sinex_data, source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_history_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(ValueError):
        c = SiteCoord.get_history("snx", "zimm,xxxx", sinex_data, source_path="/path/to/sinex")

# Tests: SiteCoord.get("ssc",...)
        
@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_one_station(ssc_data):
    c = SiteCoord.get("ssc", "gras", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in c
    assert len(c) == 1

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
    with pytest.raises(ValueError):
        c = SiteCoord.get("ssc", "xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(ValueError):
        c = SiteCoord.get("ssc", "gras, xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")

# Tests: SiteCoord.get_history("ssc",...)
        
@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_one_station(ssc_data):
    c = SiteCoord.get_history("ssc", "gras", ssc_data, source_path="/path/to/ssc")
    assert "gras" in c
    assert len(c) == 1

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
    with pytest.raises(ValueError):
        c = SiteCoord.get_history("ssc", "xxxx", ssc_data, source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_site_coord_history_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(ValueError):
        c = SiteCoord.get_history("ssc", "gras, xxxx", ssc_data, source_path="/path/to/ssc")
