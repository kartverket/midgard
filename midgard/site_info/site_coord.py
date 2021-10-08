""" Site coordinate information classes

Description:
------------
The site_coord module generates a SiteCoord object based on site information from 
the SINEX file or other sources.

Following steps are carried out for getting a SiteCoord object:

    1. Plugins modulen register SiteInfoHistory classes (e.g. 
       SiteCoordHistorySinex) and updates the 'sources' attribute of the 
       SiteInfoHistory class. 
    2. The SiteCoord object is initialized by calling the SiteCoord.get function. 
    3. The SiteInfoHistory.get function is called via the SiteCoord.get function.
       Here the correct SiteInfoHistory class is choosen by accessing the 
       registered 'sources' attribute of the SiteInfoHistory class.
    4. The SiteInfoBase.get function reads the antenna information via the
       _read_history() function of the SiteInfoHistorySinex or other 
       calls. The antenna information is selected via a given date. 


Example:
--------
    
    from midgard.site_info import site_coord; from datetime import datetime
    site_coord.SiteCoord.get(source="sinex", station="zimm", date=datetime(2018, 10, 1), source_path="igs.snx") 
"""


# Standard library imports
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Union

# Midgard imports
from midgard import parsers
from midgard.data.position import Position
from midgard.dev import log
from midgard.site_info.site_info import SiteInfoBase, SiteInfoHistory, SiteInfoHistoryBase 


class SiteCoord():
    """Main site coordinate class for getting site coordinate object depending on site information source

    The site information source can be e.g. a SINEX file.
    """

    sources = dict()

    @classmethod
    def get(
        cls, source: str, station: str, date: datetime, source_path: Union[None, str] = None
    ) -> Union["SiteCoordSinex", Any]:
        """Get site coordinate object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            date:         Date for getting site information
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Site coordinate object 
        """
        history = SiteInfoHistory.get(__name__, source, station, source_path)
        return history.get(date)

    @classmethod
    def get_history(
        cls, source: str, station: str, source_path: Union[None, str] = None
    ) -> Union["SiteCoordSinex", Any]:
        """Get site coordinate history object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Site coordinate object 
        """
        history = SiteInfoHistory.get(__name__, source, station, source_path)
        return history


@SiteInfoHistory.register_source
class SiteCoordHistorySinex(SiteInfoHistoryBase):

    source = "sinex"

    def _read_history(self) -> Dict[Tuple[datetime, datetime], "SiteCoordSinex"]:
        """Read site coordinate history from SINEX file

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are SiteCoordSinex objects.
        """
        if self.source_path is None:
            log.fatal("No SINEX file path is defined.")

        # Find site_id and read site coordinate history
        p = parsers.parse_file("gnss_sinex_igs", file_path=self.source_path)
        data = p.as_dict()
        if self.station in data:
            raw_info = data[self.station]["site_antenna"]
        elif self.station.upper() in data:
            raw_info = data[self.station.upper()]["site_antenna"]
        else:
            raise ValueError(f"Station '{self.station}' unknown in source '{self.source_path}'.")

        # Create list of site coordinate history
        history = dict()
        for site_coord_info in raw_info:
            site_coord = SiteCoordSinex(self.station, antenna_info)
            interval = (site_coord.date_from, site_coord.date_to)
            history[interval] = site_coord

        return history


class SiteCoordSinex(SiteInfoBase):
    """ Site coordinate class handling SINEX file antenna station information
    """

    source = "sinex"
    fields = dict()

    @property
    def pos(self) -> "TrsPosition":
        """ Get site coordinate from seSite API site information attribute

        Returns:
            Site coordinate 
        """
        #TODO
        return 

    @property
    def frame(self) -> str:
        """ Get reference frame from seSite API site information attribute

        Returns:
            Reference frame
        """
        #TODO
        return 

    @property
    def date_from(self) -> datetime:
        """ Get site coordinate starting date from site information attribute

        Returns:
            Site coordinate starting date
        """
        if self.info["start_time"]:
            return self.info["start_time"]
        else:
            return datetime.min

    @property
    def date_end(self) -> datetime:
        """ Get site coordinate ending date from site information attribute

        Returns:
            Site coordinate ending date
        """
        if self.info["end_time"]:
            return self.info["end_time"]
        else:
            return datetime.max - timedelta(days=367)  # TODO: Minus 367 days is necessary because
            #       _year2days(cls, year, scale) in ./midgard/data/_time.py
            #      does not work. Exceeding of datetime limit 9999 12 31.
