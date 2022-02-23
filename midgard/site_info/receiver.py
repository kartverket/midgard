""" Receiver site information classes

Description:
------------

The receiver module generates a receiver object based on site information from 
the SINEX file or other sources.

Following steps are carried out for getting a receiver object:

    1. Plugins modulen register SiteInfoHistory classes (e.g. 
       ReceiverHistorySinex) and updates the 'sources' attribute of the 
       SiteInfoHistory class. 
    2. The Receiver object is initialized by calling the Receiver.get function. 
    3. The SiteInfoHistory.get function is called via the Receiver.get function.
       Here the correct SiteInfoHistory class is choosen by accessing the 
       registered 'sources' attribute of the SiteInfoHistory class.
    4. The SiteInfoBase.get function reads the receiver information via the
       _read_history() function of the ReceiverHistorySinex or other 
       calls. The receiver information is selected via a given date. 

Example:
--------

    from midgard.site_info import receiver
    receiver.Receiver.get(source="sinex", station="ales", date=datetime(2018, 10, 1), source_path="igs.snx") 
"""

# Standard library imports
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Union

# Midgard imports
from midgard import parsers
from midgard.dev import log
from midgard.site_info._site_info import SiteInfoBase, SiteInfoHistoryBase 
from midgard.site_info.site_info import SiteInfoHistory

class Receiver:
    """Main receiver class for getting receiver object depending on site information source

    The site information source can be e.g. a SINEX file.
    """

    sources = dict()

    @classmethod
    def get(
            cls, 
            source: str,  
            source_data: Union[None, Any],
            station: str,
            date: datetime, 
            source_path: Union[None, str] = None,
    ) -> Union["ReceiverSinex", Any]:
        """Get receiver object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            date:         Date for getting site information
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored.

        Returns:
            Receiver object 
        """
        history = SiteInfoHistory.get(__name__, source, source_data, station, source_path)
        return history.get(date)

    @classmethod
    def get_history(
            cls, 
            source: str, 
            source_data: Union[None, Any],
            station: str, 
            source_path: Union[None, str] = None,
    ) -> Union["ReceiverSinex", Any]:
        """Get receiver history object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored.

        Returns:
            Receiver object 
        """
        history = SiteInfoHistory.get(__name__, source, source_data, station, source_path)
        return history


@SiteInfoHistory.register_source
class ReceiverHistorySinex(SiteInfoHistoryBase):

    source = "snx"

    def _process_history(
                self, 
                source_data: Union[None, Any] = None,
    ) -> Dict[Tuple[datetime, datetime], "ReceiverSinex"]:
        """Read receiver site history from SINEX file

        Args:
            source_data:  Source data with site information. If source data are defined, then data are not read
                          from 'source_path'.

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are ReceiverSinex objects.
        """
        # Get SINEX file data by reading from file 'source_path'
        #if not source_data:
        #    if self.source_path is None:
        #        log.fatal("No SINEX file path is defined.")

        #    # Find site_id and read antenna history
        #    print(f"Reading file {self.source_path} in ReceiverHistorySinex")
        #    p = parsers.parse_file("sinex_site", file_path=self.source_path)
        #    source_data = p.as_dict()

        #if self.station is None:
        #    # Create history for all stations in source
        #    histories = list()
        #    for station, station_data in source_data.items():
        #        histories.append(self._create_history(station, station_data["site_receiver"]))
        #    return histories

        if self.station in source_data:
            if "site_receiver" not in source_data[self.station]:
                raise ValueError(f"Station {self.station!r} is not given in SITE/RECEIVER SINEX block.")
            raw_info = source_data[self.station]["site_receiver"]
        elif self.station.upper() in source_data:
            if "site_receiver" not in source_data[self.station]:
                raise ValueError(f"Station {self.station.upper()!r} is not given in SITE/RECEIVER SINEX block.")
            raw_info = source_data[self.station.upper()]["site_receiver"]
        else:
            raise ValueError(f"Station {self.station!r} unknown in source '{self.source_path}'.")
        
        return self._create_history(self.station, raw_info)

    def _create_history(self, station, raw_info):
        """Create dictionary of antenna history for station
        """
        history = dict()
        for receiver_info in raw_info:
            receiver = ReceiverSinex(self.station, receiver_info)
            interval = (receiver.date_from, receiver.date_to)
            history[interval] = receiver

        return history


class ReceiverSinex(SiteInfoBase):
    """ Receiver class handling SINEX file receiver station information
    """

    source = "snx"
    fields = dict(type="receiver_type", serial_number="serial_number", firmware="firmware")

    @property
    def date_from(self) -> datetime:
        """ Get receiver installation date from site information attribute

        Returns:
            Receiver installation date
        """
        if self._info["start_time"]:
            return self._info["start_time"]
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get receiver removing date from site information attribute

        Returns:
            Receiver removing date
        """
        if self._info["end_time"]:
            return self._info["end_time"]
        else:
            return datetime.max - timedelta(days=367)  # TODO: Minus 367 days is necessary because
            #       _year2days(cls, year, scale) in ./midgard/data/_time.py
            #      does not work. Exceeding of datetime limit 9999 12 31.


@SiteInfoHistory.register_source
class ReceiverHistorySsc(SiteInfoHistoryBase):

    source = "ssc"

    def _process_history(
                self, 
                source_data: Union[None, Any] = None,
    ) -> Dict[Tuple[datetime, datetime], "ReceiverSinex"]:
        """Read receiver site history from SINEX file

        Args:
            source_data:  Source data with site information. If source data are defined, then data are not read
                          from 'source_path'.

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are ReceiverSinex objects.
        """
        ### SSC files do not contain receiver information
        return None


class ReceiverSsc(SiteInfoBase):
    """ Receiver class handling SINEX file receiver station information
    """

    source = "ssc"
    fields = dict(type="receiver_type", serial_number="serial_number", firmware="firmware")

    @property
    def date_from(self) -> datetime:
        """ Get receiver installation date from site information attribute

        Returns:
            Receiver installation date
        """
        if self._info["start_time"]:
            return self._info["start_time"]
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get receiver removing date from site information attribute

        Returns:
            Receiver removing date
        """
        if self._info["end_time"]:
            return self._info["end_time"]
        else:
            return datetime.max - timedelta(days=367)  # TODO: Minus 367 days is necessary because
            #       _year2days(cls, year, scale) in ./midgard/data/_time.py
            #      does not work. Exceeding of datetime limit 9999 12 31.
