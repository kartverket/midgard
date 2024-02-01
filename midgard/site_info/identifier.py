"""Identifier information classes

Description:
------------
This module is divided into three different types of classes:

    1. Main class Identifier provides basic functionality to the user. See examples.
    2. Identifier source type classes:
        - There is one class for each source type
        - A class with all relevant site coordinate information for a point in time.

    If a source type does not contain information about the identifier the module will return 'None'.

Example:
--------
    
    from midgard import parsers
    from midgard.site_info.identifier import Identifier
    from datetime import datetime
    
    # Read SINEX data  
    p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
    source_data = p.as_dict()
    all_stations = source_data.keys()

    # Get station information
    Identifier.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
    Identifier.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)
    
"""


# Standard library imports
from copy import deepcopy
from typing import Any, Dict, Callable

# Midgard imports
from midgard.dev.exceptions import MissingDataError
from midgard.site_info.m3g.api import M3gApi
from midgard.site_info._site_info import SiteInfoBase, ModuleBase
from midgard.site_info import convert_to_utc

class Identifier(ModuleBase):
    """Main class for converting identifier information from various sources into unified classes"""
    
    sources: Dict[str, Callable] = dict()
    

@Identifier.register_source
class IdentifierSinex(SiteInfoBase):
    """ Identifier class handling SINEX file identifier station information
    """

    source: str = "snx"
    fields: Dict = dict()
    
    def __init__(self, station: str, source_data: Any = None, source_path: str = None) -> None:
        """Initialize history information object from input data

        Args:
            station:      Station name.
            source_data:  Source data with site information. Structure of data is specific to information type
                          and source type
            source_path:  Source path of site information. Only intended for information purposes.
        """
        self.station = station.lower()
        self.source_path = source_path
        self._info = self._process(source_data)

    def _process(
                self, 
                source_data: Dict,
    ) -> "IdentifierSinex":
        """Process identifier site from SINEX file

        Args:
            source_data:  Source data with site information.

        Returns:
            IdentifierSinex object
        """       
        if self.station in source_data:
            if "site_id" not in source_data[self.station]:
                raise MissingDataError(f"Station {self.station!r} is not given in SITE/ID SINEX block.")
            raw_info = source_data[self.station]["site_id"]
        elif self.station.upper() in source_data:
            if "site_id" not in source_data[self.station]:
                raise MissingDataError(f"Station {self.station.upper()!r} is not given in SITE/ID SINEX block.")
            raw_info = source_data[self.station.upper()]["site_id"]
        else:
            raise MissingDataError(f"Station '{self.station}' unknown in source '{self.source}:{self.source_path}'.")

        return raw_info

    @property
    def country(self) -> str:
        """ Get country of site

        Returns:
            Country name
        """
        description = self._info["description"].split(",")
        if description:
            if len(description) > 1:
                country = description[1].strip().capitalize()
                #country = None if len(country) < 3 else country  # Country with less than 3 characters are not excepted.
            else:
                country = None
        else:
            country = None
            
        return country
        
        
    @property
    def country_code(self) -> str:
        """ Get country code of site

        Returns:
            Country code
        """
        # Country not given in SINEX file.
        return None 
        
        
    @property
    def domes(self) -> str:
        """ Get DOMES number

        Returns:
            DOMES number
        """
        return self._info["domes"]+self._info["marker"]
    
    @property
    def name(self) -> str:
        """ Get site name

        Returns:
            Site name
        """
        description = self._info["description"].split(",") 
        name = description[0].strip().capitalize() if description else None
            
        return name
    
    @property
    def tectonic_plate(self) -> str:
        """ Get tectonic plate name

        Returns:
            Tectonic plate name
        """
        # Tectonic plate name is not available in SINEX file.
        return None 
    

@Identifier.register_source
class IdentifierSsc(SiteInfoBase):
    """ Identifier class handling SSC file identifier station information
    """

    source: str = "ssc"
    fields: Dict = dict()
    
    def __init__(self, station: str, source_data: Any = None, source_path: str = None) -> None:
        """Initialize history information object from input data

        Args:
            station:      Station name.
            source_data:  Source data with site information. Structure of data is specific to information type
                          and source type
            source_path:  Source path of site information. Only intended for information purposes.
        """
        self.station = station.lower()
        self.source_path = source_path
        self._info = self._process(deepcopy(source_data))

            
    def _process(
                self, 
                source_data: Dict,
    ) -> "IdentifierSsc":
        """Process identifier site from SINEX file

        Args:
            source_data:  Source data with site information.

        Returns:
            IdentifierSsc object
        """
        if self.station in source_data:
            raw_info = source_data[self.station]
        elif self.station.upper() in source_data:
            raw_info = source_data[self.station.upper()]
        else:
            raise MissingDataError(f"Station '{self.station}' unknown in source '{self.source_path}'.")

        return raw_info
    
    @property
    def country(self) -> str:
        """ Get country of site

        Returns:
            Country name
        """
        # Country not given in SSC file.
        return None
    
    @property
    def country_code(self) -> str:
        """ Get country code of site

        Returns:
            Country code
        """
        # Country not given in SSC file.
        return None 
    
    @property
    def domes(self) -> str:
        """ Get DOMES number

        Returns:
            DOMES number
        """
        return self._info["domes"]
    
    @property
    def name(self) -> str:
        """ Get site name

        Returns:
            Site name
        """    
        # Site name not given in SSC file
        return None
        
    @property
    def tectonic_plate(self) -> str:
        """ Get tectonic plate name

        Returns:
            Tectonic plate name
        """
        # Tectonic plate name is not available in SSC file.
        return None 

@Identifier.register_source
class IdentifierM3g(SiteInfoBase):
    """ Identifier class handling gnssEu API identifier station information
    """

    source = "m3g"
    fields = dict()


    def __init__(self, station: str, source_data: Any = None, source_path: str = None) -> None:
        """Initialize history information object from input data

        Args:
            station:      Station name.
            source_data:  Source data with site information. Structure of data is specific to information type
                          and source type
            source_path:  Source path of site information. Only intended for information purposes.
        """
        self.station = station.lower()
        self.source_path = source_path
        self._info = self._process(source_data)

    def _process(
                self,
                source_data: Dict,
    ) -> "IdentifierM3g":
        """Read identifier information from gnssEu API

        Args:
            source_data:  api object for m3g

        Returns:
            IdentifierSestation object
        """
        raw_info = dict()

        # Get identifier information
        if isinstance(source_data, M3gApi):
            # source_data is an Api object. Use api function to query database
            try:
                raw_info = source_data.get_sitelog(filter={"id": {"like": self.station}})
                if not raw_info:
                    raise MissingDataError(f"Station {self.station.upper()!r} unknown in source {self.source!r}.")
                if len(raw_info) > 1:
                    raise ValueError(f"Station {self.station.upper()!r} is not unique in source {self.source!r}. Use full station name.")
                station_data = raw_info[0]
            except ConnectionError as err:
                raise MissingDataError(f"Station {self.station.upper()!r} unknown in source {self.source!r}. Error: {err}")
        elif isinstance(source_data, dict):
            # source data is a dictionary. Use the keys to look up station data
            # This is a more efficient way to look up information when all data already has been queried from
            # the database through the api.get_sitelog_all function.
            sta = self.station.upper()
            try:
                raw_info = source_data[sta[0:4]]
                if len(raw_info) > 1:
                    if len(sta) == 9:
                        station_data = raw_info[sta]
                    else:
                        raise ValueError(f"Station {self.station.upper()!r} is not unique in source {self.source!r}. Use full station name.")
                else:
                    # Only one key in dictionary
                    station_data = raw_info[list(raw_info.keys())[0]]
            except KeyError:
                raise MissingDataError(f"Station {self.station.upper()!r} unknown in source {self.source!r}. Error: {err}")

        if not "sitelog" in station_data:
            raise MissingDataError(f"No sitelog information is available for station {self.station.upper()!r} in source {self.source!r}.")

        try:
            agency = station_data["sitelog"]["siteOwner"]["agency"]["agencyName"]
        except TypeError:
            # siteOwner is often None
            agency = None

        # Get site information
        raw_info = {
            "agency": agency,
            "domes": station_data["sitelog"]["siteForm"]["domes"],
            "city": station_data["sitelog"]["location"]["location"],
            "country": station_data["sitelog"]["location"]["country"],
            "country_code": station_data["sitelog"]["location"]["countryCode"],
            "monument_depth": station_data["sitelog"]["siteForm"]["foundationDepthVal"],
            "monument_foundation": station_data["sitelog"]["siteForm"]["foundation"],
            "monument_type": station_data["sitelog"]["siteForm"]["monumentDesc"],
            "name": station_data["sitelog"]["siteForm"]["siteName"],
            "date_installed": station_data["sitelog"]["siteForm"]["dateInstalled"],
            "date_removed": station_data["sitelog"]["siteForm"]["dateRemoved"],
            "tectonic_plate": station_data["sitelog"]["location"]["tectonicPlate"],
        }

        return raw_info


    @property
    def agency(self) -> str:
        """ Get agency name

        Returns:
            Agency name
        """
        return self._info["agency"]

    @property
    def country(self) -> str:
        """ Get country of site

        Returns:
            Country name
        """
        return self._info["country"]

    @property
    def country_code(self) -> str:
        """ Get country code of site

        Returns:
            Country code
        """
        return self._info["country_code"]

    @property
    def city(self) -> str:
        """ Get city name

        Returns:
            City name
        """
        return None

    @property
    def domes(self) -> str:
        """ Get DOMES number

        Returns:
            DOMES number
        """
        return self._info["domes"]

    @property
    def monument_depth(self) -> float:
        """ Get monument depth

        Returns:
            Monument depth
        """
        return float(self._info["monument_depth"])

    @property
    def monument_foundation(self) -> str:
        """ Get monument foundation

        Returns:
            Monument foundation
        """
        return self._info["monument_foundation"].lower()

    @property
    def monument_type(self) -> str:
        """ Get monument type

        Returns:
            Monument type
        """
        return self._info["monument_type"].lower()

    @property
    def name(self) -> str:
        """ Get site name

        Returns:
            Site name
        """
        return self._info["name"]

    @property
    def status(self) -> str:
        """ Get site status

        Returns:
            Site status
        """
        if self._info["date_installed"] is not None and self._info["date_removed"] is None:
            return "operational"
        if self._info["date_installed"] is not None and self._info["date_removed"] is not None:
            return "closed"
        if self._info["date_installed"] is None:
            return "temporary"
        return

    @property
    def tectonic_plate(self) -> str:
        """ Get tectonic plate name

        Returns:
            Tectonic plate name
        """
        return self._info["tectonic_plate"]
