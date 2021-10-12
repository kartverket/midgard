""" Antenna site information classes

Description:
------------
The antenna module generates a antenna object based on site information from 
the SINEX file or other sources.

Following steps are carried out for getting a antenna object:

    1. Plugins modulen register SiteInfoHistory classes (e.g. 
       AntennaHistorySinex) and updates the 'sources' attribute of the 
       SiteInfoHistory class. 
    2. The Antenna object is initialized by calling the Antenna.get function. 
    3. The SiteInfoHistory.get function is called via the Antenna.get function.
       Here the correct SiteInfoHistory class is choosen by accessing the 
       registered 'sources' attribute of the SiteInfoHistory class.
    4. The SiteInfoBase.get function reads the antenna information via the
       _read_history() function of the AntennaHistorySinex or other 
       calls. The antenna information is selected via a given date. 


Example:
--------
    
    from midgard.site_info import antenna; from datetime import datetime
    antenna.Antenna.get(source="sinex", station="zimm", date=datetime(2018, 10, 1), source_path="igs.snx") 
"""


# Standard library imports
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Union

# Midgard imports
from midgard import parsers
from midgard.dev import log
from midgard.site_info.site_info import SiteInfoBase, SiteInfoHistory, SiteInfoHistoryBase 


class Antenna():
    """Main antenna class for getting antenna object depending on site information source

    The site information source can be e.g. a SINEX file.
    """

    sources = dict()

    @classmethod
    def get(
            cls, 
            source: str, 
            station: str, 
            date: datetime, 
            source_path: Union[None, str] = None,
            source_data: Union[None, Any] = None,
    ) -> Union["AntennaSinex", Any]:
        """Get antenna object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            date:         Date for getting site information
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored.


        Returns:
            Antenna object 
        """
        history = SiteInfoHistory.get(__name__, source, station, source_path, source_data)
        return history.get(date)

    @classmethod
    def get_history(
            cls, 
            source: str, 
            station: str, 
            source_path: Union[None, str] = None,
            source_data: Union[None, Any] = None,
    ) -> Union["AntennaSinex", Any]:
        """Get antenna history object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored.

        Returns:
            Antenna object 
        """
        history = SiteInfoHistory.get(__name__, source, station, source_path, source_data)
        return history


@SiteInfoHistory.register_source
class AntennaHistorySinex(SiteInfoHistoryBase):

    source = "sinex"

    def _read_history(self) -> Dict[Tuple[datetime, datetime], "AntennaSinex"]:
        """Read antenna site history from SINEX file

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are AntennaSinex objects.
        """
        # Get SINEX file data by reading from file 'source_path'
        if not self.source_data:
            if self.source_path is None:
                log.fatal("No SINEX file path is defined.")

            # Find site_id and read antenna history
            p = parsers.parse_file("gnss_sinex_igs", file_path=self.source_path)
            self.source_data = p.as_dict()

        if self.station in self.source_data:
            raw_info = self.source_data[self.station]["site_antenna"]
        elif self.station.upper() in self.source_data:
            raw_info = self.source_data[self.station.upper()]["site_antenna"]
        else:
            raise ValueError(f"Station '{self.station}' unknown in source '{self.source_path}'.")

        # Create list of antenna history
        history = dict()
        for antenna_info in raw_info:
            antenna = AntennaSinex(self.station, antenna_info)
            interval = (antenna.date_from, antenna.date_to)
            history[interval] = antenna

        return history


class AntennaSinex(SiteInfoBase):
    """ Antenna class handling SINEX file antenna station information
    """

    source = "sinex"
    fields = dict(
        type="antenna_type",
        serial_number="serial_number",
        radome_type="radome_type",
        radome_serial_number="radome_type",
    )

    @property
    def date_from(self) -> datetime:
        """ Get antenna installation date from site information attribute

        Returns:
            Antenna installation date
        """
        if self.info["start_time"]:
            return self.info["start_time"]
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get antenna removing date from site information attribute

        Returns:
            Antenna removing date
        """
        if self.info["end_time"]:
            return self.info["end_time"]
        else:
            return datetime.max - timedelta(days=367)  # TODO: Minus 367 days is necessary because
            #       _year2days(cls, year, scale) in ./midgard/data/_time.py
            #      does not work. Exceeding of datetime limit 9999 12 31.
