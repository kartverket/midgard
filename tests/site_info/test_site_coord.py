import datetime
import pytest

#from test_site_info import sinex_data

from midgard.site_info.site_coord import SiteCoord

@pytest.mark.usefixtures("sinex_data")
def test_site_coord_sinex(sinex_data):
    a = SiteCoord.get("snx", "zimm", datetime.datetime.now(), sinex_data, source_path="/path/to/sinex")