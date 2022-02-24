import datetime
import pytest

from midgard.site_info import site_info
from curses.ascii import SI


@pytest.mark.usefixtures("sinex_data")
def test_site_info_sinex(sinex_data):
    si = site_info.SiteInfo.get_history("snx", "zimm", sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    si = site_info.SiteInfo.get_history("snx", "zimm,hrao", sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    si = site_info.SiteInfo.get_history("snx", ["zimm","hrao"], sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    assert "hrao" in si
    si = site_info.SiteInfo.get("snx", "zimm", datetime.datetime.now(), sinex_data, source_path="path/to/sinex")
    assert "zimm" in si
    