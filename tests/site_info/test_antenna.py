import datetime
import pytest

from midgard.dev.exceptions import MissingDataError
from midgard.site_info.antenna import Antenna

# Tests: Antenna.get("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_antenna_sinex_one_station(sinex_data):
    a = Antenna.get("snx", "zimm", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert len(a) == 1
    
    # Test antenna information
    assert a["zimm"].date_from == datetime.datetime(1998, 11, 6, 0, 0)
    assert a["zimm"].date_to == datetime.datetime(9998, 12, 29, 23, 59, 59, 999999)
    assert a["zimm"].station == 'zimm'
    assert a["zimm"].radome_serial_number == 'NONE'
    assert a["zimm"].radome_type == 'NONE'
    assert a["zimm"].serial_number == '99390'
    assert a["zimm"].type == 'TRM29659.00'


@pytest.mark.usefixtures("sinex_data")
def test_antenna_sinex_two_stations_string(sinex_data):
    a = Antenna.get("snx", "zimm, hrao", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2

@pytest.mark.usefixtures("sinex_data")
def test_antenna_sinex_two_stations_list(sinex_data):
    a = Antenna.get("snx", ["zimm", "hrao"], datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2
    
@pytest.mark.usefixtures("sinex_data")
def test_antenna_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Antenna.get("snx", "xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_antenna_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Antenna.get("snx", "zimm,xxxx", datetime.datetime(2020, 1, 1), sinex_data, source_path="/path/to/sinex")

# Tests: Antenna.get_history("snx",...)

@pytest.mark.usefixtures("sinex_data")
def test_antenna_history_sinex_one_station(sinex_data):
    a = Antenna.get_history("snx", "zimm", sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert len(a) == 1
    
    # Test antenna history information
    assert len(a["zimm"].history) == 2
    assert len(a["zimm"].date_from) == 2
    assert len(a["zimm"].date_to) == 2

@pytest.mark.usefixtures("sinex_data")
def test_antenna_history_sinex_two_stations_string(sinex_data):
    a = Antenna.get_history("snx", "zimm, hrao", sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2

@pytest.mark.usefixtures("sinex_data")
def test_antenna_history_sinex_two_stations_list(sinex_data):
    a = Antenna.get_history("snx", ["zimm", "hrao"], sinex_data, source_path="/path/to/sinex")
    assert "zimm" in a
    assert "hrao" in a
    assert len(a) == 2
    
@pytest.mark.usefixtures("sinex_data")
def test_antenna_history_sinex_one_station_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Antenna.get_history("snx", "xxxx", sinex_data, source_path="/path/to/sinex")

@pytest.mark.usefixtures("sinex_data")
def test_antenna_history_sinex_two_stations_error(sinex_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Antenna.get_history("snx", "zimm,xxxx", sinex_data, source_path="/path/to/sinex")

# Tests: Antenna.get("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_antenna_ssc_one_station(ssc_data):
    a = Antenna.get("ssc", "gras", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert len(a) == 1
    
    # Test antenna information
    assert a["gras"] is None

@pytest.mark.usefixtures("ssc_data")
def test_antenna_ssc_two_stations_string(ssc_data):
    a = Antenna.get("ssc", "gras, borr", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_antenna_ssc_two_stations_list(ssc_data):
    a = Antenna.get("ssc", ["gras", "borr"], datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_antenna_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Antenna.get("ssc", "xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_antenna_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Antenna.get("ssc", "zimm,xxxx", datetime.datetime(2020, 1, 1), ssc_data, source_path="/path/to/ssc")

# Tests: Antenna.get_history("ssc",...)

@pytest.mark.usefixtures("ssc_data")
def test_antenna_history_ssc_one_station(ssc_data):
    a = Antenna.get_history("ssc", "gras", ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert len(a) == 1
    
    # Test antenna history information
    assert a["gras"].history is None
    assert a["gras"].date_from is None
    assert a["gras"].date_to is None

@pytest.mark.usefixtures("ssc_data")
def test_antenna_history_ssc_two_stations_string(ssc_data):
    a = Antenna.get_history("ssc", "gras, borr", ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_antenna_history_ssc_two_stations_list(ssc_data):
    a = Antenna.get_history("ssc", ["gras", "borr"], ssc_data, source_path="/path/to/ssc")
    assert "gras" in a
    assert "borr" in a
    assert len(a) == 2

@pytest.mark.usefixtures("ssc_data")
def test_antenna_history_ssc_one_station_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Antenna.get_history("ssc", "xxxx", ssc_data, source_path="/path/to/ssc")

@pytest.mark.usefixtures("ssc_data")
def test_antenna_history_ssc_two_stations_error(ssc_data):
    # Station xxxx does not exist
    with pytest.raises(MissingDataError):
        a = Antenna.get_history("ssc", "zimm,xxxx", ssc_data, source_path="/path/to/ssc")
