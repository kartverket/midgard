"""Antenna information classes

Description:
------------
This module is divided into three different types of classes:

    1. Main class Antenna provides basic functionality to the user. See exampless
    2. Antenna source type classes:
        - There is one class for each source type.
        - A class with all relevant antenna information for a point in time.
    3. Antenna history source type classes:
        - There is one class for each source type.
        - Converts input from source_data to a object of type AntennaHistorySinex, etc and provides functions
          for accessing the history and relevant dates. 
        - The history consist of a time interval for which the entry is valid and an instance of an antenna 
          source type class for each defined time interval.

    If a source type does not contain information about the antenna the module will return 'None'.

Example:
--------
    
    from midgard import parsers
    from midgard.site_info.antenna import Antenna
    from datetime import datetime
    
    # Read SINEX data  
    p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
    source_data = p.as_dict()
    all_stations = source_data.keys()

    # Get station information    
    Antenna.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
    Antenna.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)
    
    Antenna.get_history("snx", "osls", source_data, source_path=p.file_path)
    Antenna.get_history("snx", all_stations, source_data, source_path=p.file_path)

"""


# Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union, Callable

# Midgard imports
from midgard.dev.exceptions import MissingDataError
from midgard.site_info.gnsseu.api import GnssEuApi
from midgard.site_info._site_info import SiteInfoBase, SiteInfoHistoryBase, ModuleBase
from midgard.site_info import convert_to_utc

class Antenna(ModuleBase):
    """Main class for converting antenna information from various sources into unified classes"""
    
    sources: Dict[str, Callable] = dict()


@Antenna.register_source
class AntennaHistorySinex(SiteInfoHistoryBase):

    source: str = "snx"

    def _process_history(
                self, 
                source_data: Dict,
    ) -> Dict[Tuple[datetime, datetime], "AntennaSinex"]:
        """Process antenna site history from SINEX file

        Args:
            source_data:  Source data with site information.

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are AntennaSinex objects.
        """
                
        if self.station in source_data:
            if "site_antenna" not in source_data[self.station]:
                raise MissingDataError(f"Station {self.station!r} is not given in SITE/ANTENNA SINEX block.")
            raw_info = source_data[self.station]["site_antenna"]
        elif self.station.upper() in source_data:
            if "site_antenna" not in source_data[self.station]:
                raise MissingDataError(f"Station {self.station.upper()!r} is not given in SITE/ANTENNA SINEX block.")
            raw_info = source_data[self.station.upper()]["site_antenna"]
        else:
            raise MissingDataError(f"Station '{self.station}' unknown in source '{self.source}:{self.source_path}'.")

        return self._create_history(self.station, raw_info)

    def _create_history(self, station: str, raw_info: List)-> Dict:
        """Create dictionary of antenna history for station
        """
        history = dict()
        for antenna_info in raw_info:
            antenna = AntennaSinex(self.station, antenna_info)
            interval = (antenna.date_from, antenna.date_to)
            history[interval] = antenna

        return history


class AntennaSinex(SiteInfoBase):
    """ Antenna class handling SINEX file antenna station information
    """

    source: str = "snx"
    fields: Dict[str, str] = dict(
        type="antenna_type",
        serial_number="serial_number",
        radome_type="radome_type",
        radome_serial_number="radome_type",
    )
    
    @property
    def calibration(self) -> bool:
        """ Get information if individual antenna calibration file exists

        Returns:
            True if individual antenna calibration file exits otherwise False
        """
        #Note: Information about individual antenna calibration is not given in SINEX file. 
        return False

    @property
    def date_from(self) -> datetime:
        """ Get antenna installation date from site information attribute

        Returns:
            Antenna installation date
        """
        if self._info["start_time"]:
            return self._info["start_time"]
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get antenna removing date from site information attribute

        Returns:
            Antenna removing date
        """
        if self._info["end_time"]:
            return self._info["end_time"]
        else:
            return datetime.max


@Antenna.register_source
class AntennaHistorySsc(SiteInfoHistoryBase):

    source: str = "ssc"

    def _process_history(
                self, 
                source_data: Any,
    ) -> Union[None, Dict[Tuple[datetime, datetime], "AntennaSsc"]]:
        """Process antenna site history from SSC file

        Note: SSC files does not contain antenna information

        Args:
            source_data:  Dictionary with site information from SSC file.

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are AntennaSsc objects.
        """
        if self.station in source_data or self.station.upper() in source_data:
            # Station is defined but SSC files do not contain receiver information
            return None
        else:
            raise MissingDataError(f"Station {self.station!r} unknown in source '{self.source_path}'.")


@Antenna.register_source
class AntennaHistoryGnssEu(SiteInfoHistoryBase):

    source = "gnsseu"

    def _process_history(self, source_data) -> Dict[Tuple[datetime, datetime], "AntennaGnssEu"]:
        """Read antenna site history from seStation API

        Args:
            source_data:    api object for gnsseu

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are AntennaGnssEu objects.
        """
        # Get antenna history information
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

        # Create list of antenna history
        history = dict()
        for antenna_info in station_data["sitelog"]["antennas"]:
            # Add Antenna object to history information
            antenna = AntennaGnssEu(self.station, antenna_info)
            interval = (antenna.date_from, antenna.date_to)
            history[interval] = antenna

        return history


class AntennaGnssEu(SiteInfoBase):
    """ Antenna class handling GnssEu API antenna station information
    """

    source = "gnsseu"
    fields = dict(
        serial_number="serialNumber",
    )

    @property
    def calibration(self) -> bool:
        """ Get information if individual antenna calibration file exists

        Returns:
            True if individual antenna calibration file exits otherwise False
        """
        # No calibration information found in api sitelog
        return False

    @property
    def date_from(self) -> datetime:
        """ Get antenna installation date from seStation API site information attribute

        Returns:
            Antenna installation date
        """
        if self._info["dateInstalled"] is not None:
            return convert_to_utc(datetime.fromisoformat(self._info["dateInstalled"]))
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get antenna removing date from seStation API site information attribute

        Returns:
            Antenna removing date
        """
        if self._info["dateRemoved"] is not None:
            return convert_to_utc(datetime.fromisoformat(self._info["dateRemoved"]))
        else:
            return datetime.max

    @property
    def radome_serial_number(self) -> str:
        """ Get radome serial number

        Returns:
            Radome serial number
        """
        return self._info["radomeSerialNumber"]

    @property
    def radome_type(self) -> str:
        """ Get radome type

        Returns:
            Radome type
        """
        return self._info["antennaRadomeType"] if self._info["antennaRadomeType"] != "NONE" else ""

    @property
    def reference_point(self) -> str:
        """ Get antenna reference point

        Returns:
            Antenna reference point
        """
        return self._info["referencePoint"]

    @property
    def type(self) -> str:
        """ Get antenna type

        Returns:
            Antenna type
        """
        return self._info["antenna"]

