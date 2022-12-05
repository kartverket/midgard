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
from midgard.site_info._site_info import SiteInfoBase, ModuleBase

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
        self._info = self._process(deepcopy(source_data))
        

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
        return self._info["domes"]+self._info["marker"]
    
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
