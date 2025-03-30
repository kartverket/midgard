"""Python wrapper around the Transformation API

Description:
------------

Transformation of coordinates can be done by using Transformation API from/to different reference systems and 
projection. Available Transformation API projections can be shown by using function 'projections'.

Example:
--------
from midgard.api import transformation_api

# Get instance of TransformationApi class on default URL
api = transformation_api.TransformationApi()

# Get instance of TransformationApi class based on defined URL
api = transformation_api.TransformationApi(url="https://ws.geonorge.no/transformering/v1")

# Transform from ITRF2014 to ETRS89
pos = api.transform(2169481.21111251,  627616.7736756 , 5944952.10084486, 2021.0, 4936, 7789)

"""

# Standard library imports
from collections import OrderedDict
from json import JSONDecodeError
from typing import Any, Dict, List, Union

# Third party imports
import requests

# Midgard imports
from midgard.dev.exceptions import PositionOutsideTranformationRegion


class TransformationApi(object):
    """A wrapper around the transformation API
    
    https://ws.geonorge.no/transformering/v1/transformer?x=1&y=60&z=0&t=2018&fra=4258&til=4258
    """

    def __init__(
            self, 
            url: str="https://ws.geonorge.no/transformering/v1", 
            proxy: Union[str, None] = None,
    ) -> None:
        """Initialize transformation API object

        Args:
            url:     URL of transformation API
            proxy:   URL of proxy server
        """
        self.url = url.replace("#/", "")
        self.proxy = proxy
        self.epsg = self._get_available_epsg()
        

    def get_name(self, epsg: Union[int, str]) -> str:
        """Get name of projection based on given EPSG code
        
        Args:
            epsg: EPSG code
            
        Returns:
            Name of projection based on given EPSG code
        """
        return self.projections[self._exists_epsg(int(epsg))]["name"]
    
    
    @property
    def projections(self) -> Dict[str, Any]:
        """Get available projections of transformation API
        
        Returns:
        """
        projections = OrderedDict()
        url = f"{self.url}/projeksjoner"
          
        for proj in self._get_url(url).json():
            projections[proj["epsg"]] = dict(name = proj["name"], info = proj["info"]) if "info" in proj else dict(name = proj["name"])

        return projections


    def transform(self, x: float, y: float, z: float, t: float, from_epsg: float, to_epsg: float) -> List[float]:
        """Transform coordinates via transformation API
        
        Args:
            x:         X-coordinate in [m] or longitude in [deg] given in 'from_sys' reference system 
            y:         Y-coordinate in [m] or latitude in [deg] given in 'from_sys' reference system
            z:         Z-coordinate in [m] or height in [m] given in 'from_sys' reference system
            t:         Reference epoch of X, Y, Z coordinates in decimalyear
            from_epsg: EPSG code for input coordinates
            to_epsg:   EPSG code for output coordinates 
            
        Returns:
            Tuple with X, Y and Z coordinates in reference system 'to_sys'
        """
        url = (f"{self.url}/transformer?x={x}&y={y}&z={z}&t={t}&fra={self._exists_epsg(from_epsg)}&"
              f"til={self._exists_epsg(to_epsg)}")
        pos = self._get_url(url).json()
        return [pos["x"], pos["y"], pos["z"]]
    
    
    #
    # AUXILIARY FUNCTIONS
    #
    @staticmethod            
    def _error_message(url: str, response: "Response"):
        """Generate error message based on request response
        
        Args:
            url:      Requested URL
            response: Response of request
        
        Returns:
            Error message
        """
        
        error_msg = ""
        #+ Workaround due to official transformation API does not provide error messages as JSON files
        try: 
            response.json()
        except JSONDecodeError:
            raise ConnectionError(f"Failure by URL {url} call\nStatus {response.status_code}: {response.text}")
        #- Workaround due to official transformation API does not provide error messages as JSON files

        #TODO: Use status code instead of text to check failure.
        json = response.json()
        if "detail" in json:
            error_msg = f"{error_msg}\nDetails: {json['detail']}"
            
            if "Responsen inneholder uendelige verdier" in json["detail"]:
                raise PositionOutsideTranformationRegion(f"Failure by URL {url} call. Station position is located outside transformation region.")
    
        raise ConnectionError(f"Failure by URL {url} call\n{error_msg}")
    

    def _exists_epsg(self, epsg: Union[int, str]) -> Union[int, str]: 
        """Check if EPSG code exists 
        
        Args: 
            epsg: EPSG code
            
        Returns:
            EPSG code, if EPSG code exists in transformation API
        """
        if not int(epsg) in self.epsg:
            raise ValueError(f"EPSG code {epsg!r} is not available in transformation API. Choose one of following EPSG "
                             f"codes: {','.join([str(v) for v in self.epsg])}")
        return epsg
    
    
    def _get_available_epsg(self) -> List[int]: 
        """Get available transformation API EPSG codes
        
        Returns:
            List with available EPSG codes
        """
        return list(self.projections.keys())


    def _get_url(self, url: str) -> requests.models.Response:
        """Check availability of URL and return request response object

        Args:
            url: URL path

        Returns:
            Request response object
        """
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else self.proxy 
        try:
            response = requests.get(url, proxies=proxies)
            response.raise_for_status()  # If the response was successful (status_code = 200), no exception will be raised.

        except requests.exceptions.ProxyError as err:
            raise ConnectionError(f"Failure by URL {url} call via proxy server {self.proxy}.\nError message: {err}")

        except requests.exceptions.RequestException: # all requests exceptions inherit from RequestException
            self._error_message(url, response)
   
        return response


