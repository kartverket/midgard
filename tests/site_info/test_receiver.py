import datetime
import pytest

#from test_site_info import sinex_data

from midgard.site_info.receiver import Receiver

@pytest.mark.usefixtures("sinex_data")
def test_receiver_sinex(sinex_data):
    r = Receiver.get("snx", "zimm", datetime.datetime.now(), sinex_data, source_path="/path/to/sinex")