"""Tests for the Midgard.api.transformation_api-module

Example:
--------
    python -m pytest test_transformation_api.py -s

    Note: If '-s' option is used by calling pytest, then also debug messages are printed.
"""


# Third party imports
import numpy as np
import pytest

# Midgard imports
from midgard.api import transformation_api
from midgard.dev.exceptions import PositionOutsideTranformationRegion


@pytest.fixture
def trans_api():
    """Generate transformation API object by accessing transformation API
    """
    url = "https://ws.geonorge.no/transformering/v1"
    return transformation_api.TransformationApi(url=url)
    
    
@pytest.fixture
def trans_api_proxy():
    """Generate transformation API object by accessing transformation API via a proxy server
    """
    url = "https://ws.geonorge.no/transformering/v1"
    proxy = "http://159.162.38.244:3128"
    return transformation_api.TransformationApi(url=url, proxy=proxy)


@pytest.mark.parametrize("epsg, expected_name", [
                (4936, "ETRS89 Geosentrisk"),
                (4937, "ETRS89 Geografisk 3D"),
                (7789, "ITRF2014 Geosentrisk"),
                (7912, "ITRF2014 Geografisk 3D"),
])    
def test_get_name(trans_api, epsg, expected_name):
    """Test of get_name() function 
    """
    name = trans_api.get_name(epsg)
    assert name == expected_name
    
    
def test_projections(trans_api):
    """Test of projections property
    """
    projections = trans_api.projections
    assert 4936 in projections.keys()
    assert "name" in projections[4936].keys()
    assert "ETRS89 Geosentrisk" == projections[4936]["name"]
    
   
def test_projections_proxy(trans_api_proxy):
    """Test of projections property via proxy server
    """
    projections = trans_api_proxy.projections
    assert 4936 in projections.keys()
    assert "name" in projections[4936].keys()
    assert "ETRS89 Geosentrisk" == projections[4936]["name"]


@pytest.mark.parametrize("x, y, z, t, epsg_etrs89, epsg_itrf2014", [
                (2169481.8222,  627616.5130, 5944951.8549, 2021.0, 4936, 7789), # 4936: ETRS89 Geosentrisk, 7789: ITRF2014 Geosentrisk
                (16.13481177249419,  69.3260547223623, 44.2240, 2021.0, 4937, 7789), # 4937: ETRS89 Geografisk 3D, 7789: ITRF2014 Geosentrisk
])
def test_transform(trans_api, x, y, z, t, epsg_etrs89, epsg_itrf2014):
    """Test of transform() function 
    """
    pos_itrf2014 = trans_api.transform(x, y, z, t, epsg_etrs89, epsg_itrf2014)
    pos_etrs89 = trans_api.transform(pos_itrf2014[0], pos_itrf2014[1], pos_itrf2014[2], t, epsg_itrf2014, epsg_etrs89)
   
    np.testing.assert_allclose(np.array([x,y,z]), np.array(pos_etrs89), rtol=0, atol=1e-6)

     
@pytest.mark.parametrize("x, y, z, t, from_epsg, to_epsg", [
                (-52.6,  5.1, 100.0, 2021.0, 4937, 7789),
])
def test_transform_outside_region(trans_api, x, y, z, t, from_epsg, to_epsg):
    """Test failure raising if station coordinate is outside of EUREF89 transformation region
    """
    with pytest.raises(PositionOutsideTranformationRegion):
        pos = trans_api.transform(x, y, z, t, from_epsg, to_epsg)
   
