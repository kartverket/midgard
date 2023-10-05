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
from midgard.dev.exceptions import MissingDataError
from midgard.site_info.gnsseu.api import GnssEuApi
from midgard.site_info._site_info import SiteInfoBase, SiteInfoHistoryBase, ModuleBase
from midgard.site_info import convert_to_utc

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
    def dpos(self) -> List:
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

        return val

    @property
    def vector_type(self) -> str:
        """ Get type of eccentricity vector for property dpos

        Returns:
            Eccentricity vector type
        """
        if self._info["vector_type"] == "UNE":
            return "ENU"
        elif self._info["vector_type"] == "XYZ":
            return "XYZ"
        else:
            raise ValueError(f"Reference system type '{type_}' is unknown. Type should be 'UNE' or 'XYZ'.")
        return self._info["vector_type"]
    
    @property
    def east(self) -> float:
        """ Get the east component of the eccentricity vector

            Returns:
                East [meter] or None
        """
        if self._info["vector_type"] == "UNE":
            return self._info["vector_3"]

    @property
    def north(self) -> float:
        """ Get the north component of the eccentricity vector

            Returns:
                North [meter] or None
        """
        if self._info["vector_type"] == "UNE":
            return self._info["vector_2"]
    
    @property
    def up(self) -> float:
        """ Get the up component of the eccentricity vector

            Returns:
                Up [meter] or None
        """
        if self._info["vector_type"] == "UNE":
            return self._info["vector_1"]

    @property
    def x(self) -> float:
        """ Get the X component of the eccentricity vector

            Returns:
                X [meter] or None
        """
        if self._info["vector_type"] == "XYZ":
            return self._info["vector_1"]

    @property
    def y(self) -> float:
        """ Get the Y component of the eccentricity vector

            Returns:
                Y [meter] or None
        """
        if self._info["vector_type"] == "XYZ":
            return self._info["vector_2"]

    @property
    def z(self) -> float:
        """ Get the Z component of the eccentricity vector

            Returns:
                Z [meter] or None
        """
        if self._info["vector_type"] == "XYZ":
            return self._info["vector_3"]


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


@Eccentricity.register_source
class EccentricityHistoryGnssEu(SiteInfoHistoryBase):

    source = "gnsseu"

    def _process_history(self, source_data) -> Dict[Tuple[datetime, datetime], "EccentricityGnssEu"]:
        """Read eccentricity site history from gnssEu API

        Args:
            source_data:    api object for gnsseu

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are EccentricityGnssEu objects.
        """
        # Get eccentricity history information
        if isinstance(source_data, GnssEuApi):
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


        # Create list of eccentricity history
        history = dict()
        for eccentricity_info in station_data["sitelog"]["antennas"]:
            eccentricity = EccentricityGnssEu(self.station, eccentricity_info)
            interval = (eccentricity.date_from, eccentricity.date_to)
            history[interval] = eccentricity

        return history


class EccentricityGnssEu(SiteInfoBase):
    """ Eccentricity class handling gnssEu API eccentricity station information
    """

    source = "gnsseu"
    fields = dict()

    @property
    def date_from(self) -> datetime:
        """ Get eccentricity installation date from gnssEu API site information attribute

        Returns:
            Eccentricity installation date
        """
        if self._info["dateInstalled"]:
            return convert_to_utc(datetime.fromisoformat(self._info["dateInstalled"]))
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get eccentricity removing date from gnssEu API site information attribute

        Returns:
            Eccentricity removing date
        """
        if self._info["dateRemoved"]:
            return convert_to_utc(datetime.fromisoformat(self._info["dateRemoved"]))
        else:
            return datetime.max

    @property
    def dpos(self) -> List:
        """ Get eccentricity from gnssEu API site information attribute

        Returns:
            Eccentricity [meter, meter, meter]
        """
        return [self._info["markerARP"]["east"], self._info["markerARP"]["north"], self._info["markerARP"]["up"]]

    @property
    def vector_type(self)-> str:
        """ Get type of eccentricity vector for property dpos

        Returns:
            Eccentricity vector type
        """
        return "ENU"

    @property
    def east(self) -> float:
        """ Get the east component of the eccentricity vector

            Returns:
                East [meter]
        """
        return self._info["markerARP"]["east"]

    @property
    def north(self) -> float:
        """ Get the north component of the eccentricity vector

            Returns:
                North [meter]
        """
        return self._info["markerARP"]["north"]

    @property
    def up(self) -> float:
        """ Get the up component of the eccentricity vector

            Returns:
                Up [meter]
        """
        return self._info["markerARP"]["up"]

