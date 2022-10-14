"""Eccentricity information classes

Description:
------------
This module is divided into three different types of classes:

    1. Main class Eccentricity provides basic functionality to the user. See examples.
    2. Eccentricity source type classes:
        - There is one class for each source type
        - A class with all relevant site coordinate information for a point in time.
    3. Eccentricity history source type classes:
        - There is one class for each source type
        - Converts input from source_data to a object of type EccentricityHistorySinex, etc and provides functions
          for accessing the history and relevant dates. 
        - The history consist of a time interval for which the entry is valid and an instance of an eccentricity 
          source type class for each defined time interval.

    If a source type does not contain information about the eccentricity the module will return 'None'.

Example:
--------
    
    from midgard import parsers
    from midgard.site_info.eccentricity import Eccentricity
    from datetime import datetime
    
    # Read SINEX data  
    p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
    source_data = p.as_dict()
    all_stations = source_data.keys()

    # Get station information
    Eccentricity.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
    Eccentricity.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)
    
    Eccentricity.get_history("snx", "osls", source_data, source_path=p.file_path)
    Eccentricity.get_history("snx", all_stations, source_data, source_path=p.file_path)

"""


# Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union, Callable

# Midgard imports
from midgard.data.position import Position, PositionDelta
from midgard.dev.exceptions import MissingDataError
from midgard.site_info._site_info import SiteInfoBase, SiteInfoHistoryBase, ModuleBase

class Eccentricity(ModuleBase):
    """Main class for converting eccentricity information from various sources into unified classes"""
    
    sources: Dict[str, Callable] = dict()


@Eccentricity.register_source
class EccentricityHistorySinex(SiteInfoHistoryBase):

    source: str = "snx"

    def _process_history(
                self, 
                source_data: Dict,
    ) -> Dict[Tuple[datetime, datetime], "EccentricitySinex"]:
        """Process eccentricity site history from SINEX file

        Args:
            source_data:  Source data with site information.

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are EccentricitySinex objects.
        """
                
        if self.station in source_data:
            if "site_eccentricity" not in source_data[self.station]:
                raise MissingDataError(f"Station {self.station!r} is not given in SITE/ECCENTRICITY SINEX block.")
            raw_info = source_data[self.station]["site_eccentricity"]
        elif self.station.upper() in source_data:
            if "site_eccentricity" not in source_data[self.station]:
                raise MissingDataError(f"Station {self.station.upper()!r} is not given in SITE/ECCENTRICITY SINEX block.")
            raw_info = source_data[self.station.upper()]["site_eccentricity"]
        else:
            raise MissingDataError(f"Station '{self.station}' unknown in source '{self.source}:{self.source_path}'.")

        return self._create_history(self.station, raw_info)

    def _create_history(self, station: str, raw_info: List)-> Dict:
        """Create dictionary of eccentricity history for station
        """
        history = dict()
        for eccentricity_info in raw_info:
            eccentricity = EccentricitySinex(self.station, eccentricity_info)
            interval = (eccentricity.date_from, eccentricity.date_to)
            history[interval] = eccentricity

        return history


class EccentricitySinex(SiteInfoBase):
    """ Eccentricity class handling SINEX file eccentricity station information
    """

    source: str = "snx"
    fields: Dict = dict()

    @property
    def date_from(self) -> datetime:
        """ Get eccentricity installation date from site information attribute

        Returns:
            Eccentricity installation date
        """
        if self._info["start_time"]:
            return self._info["start_time"]
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get eccentricity removing date from site information attribute

        Returns:
            Eccentricity removing date
        """
        if self._info["end_time"]:
            return self._info["end_time"]
        else:
            return datetime.max
        
    @property
    def dpos(self) -> "TrsPositionDelta":
        """ Get eccentricity from SINEX file

        Returns:
            Eccentricity
        """
        
        type_ = self._info["vector_type"]
        
        if type_ == "UNE":
            val = [self._info["vector_3"], self._info["vector_2"], self._info["vector_1"]]
            system = "enu"
        elif type == "XYZ":
            val = [self._info["vector_1"], self._info["vector_2"], self._info["vector_3"]]
            system = "xyz"
        else:
            raise ValueError(f"Reference system type '{type_}' is unknown. Type should be 'UNE' or 'XYZ'.")
        
        dpos = PositionDelta(
            val=val,
            system=system,
            ref_pos=Position(val=[0,0,0], system="trs"),
        )

        return dpos


@Eccentricity.register_source
class EccentricityHistorySsc(SiteInfoHistoryBase):

    source: str = "ssc"

    def _process_history(
                self, 
                source_data: Any,
    ) -> Union[None, Dict[Tuple[datetime, datetime], "EccentricitySsc"]]:
        """Process eccentricity site history from SSC file

        Note: SSC files does not contain eccentricity information

        Args:
            source_data:  Dictionary with site information from SSC file.

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are EccentricitySsc objects.
        """
        if self.station in source_data or self.station.upper() in source_data:
            # Station is defined but SSC files do not contain eccentricity information
            return None
        else:
            raise MissingDataError(f"Station {self.station!r} unknown in source '{self.source_path}'.")
