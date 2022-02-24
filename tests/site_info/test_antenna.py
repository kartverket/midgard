import datetime
import pytest

#from test_site_info import sinex_data

from midgard.site_info.antenna import Antenna

@pytest.mark.usefixtures("sinex_data")
def test_antenna_sinex(sinex_data):
    a = Antenna.get("snx", "zimm", datetime.datetime.now(), sinex_data, source_path="/path/to/sinex")