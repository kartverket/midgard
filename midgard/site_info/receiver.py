""" Receiver site information classes

Description:
------------

The receiver module generates a receiver object based on site information from 
the SINEX file or other sources.

Following steps are carried out for getting a receiver object:

    1. Plugins modulen register ReceiverHistory classes (e.g. 
       ReceiverHistorySinex) and updates the 'sources' attribute of the 
       ReceiverHistory class. 
    2. The Receiver object is initialized by calling the Receiver.get function. 
    3. The ReceiverHistory.get function is called via the Receiver.get function.
       Here the correct ReceiverHistory class is choosen by accessing the 
       registered 'sources' attribute of the ReceiverHistory class.
    4. The ReceiverBase.get function reads the receiver information via the
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

# from midgard.site_info.site_info import SiteInfoHistory, SiteInfoHistoryBase # TODO: Does not work together with registering antenna plugin?


class Receiver:
    """Main receiver class for getting receiver object depending on site information source

    The site information source can be e.g. a SINEX file.
    """

    sources = dict()

    @classmethod
    def get(
        cls, source: str, station: str, date: datetime, source_path: Union[None, str] = None
    ) -> Union["ReceiverSinex", Any]:
        """Get receiver object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            date:         Date for getting site information
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Receiver object 
        """
        history = ReceiverHistory.get(source, station, source_path)
        return history.get(date)

    @classmethod
    def get_history(
        cls, source: str, station: str, source_path: Union[None, str] = None
    ) -> Union["ReceiverSinex", Any]:
        """Get antenna history object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Antenna object 
        """
        history = ReceiverHistory.get(source, station, source_path)
        return history


class ReceiverBase:
    """Receiver base class defining common attributes and methods
    """

    source = None
    fields = dict(
        date_installed="date_installed",
        date_removed="date_removed",
        firmware="firmware",
        type="type",
        serial_number="serial_number",
    )

    def __init__(self, station: str, receiver_info: Dict[str, Any]) -> None:
        """Initialize receiver information object

        Args:
            station:        Station name.
            receiver_info:  Dictionary with receiver information.
        """
        self.station = station.lower()
        self.info = receiver_info

    def __repr__(self) -> str:
        """A string describing the receiver information object

        The string describes the receiver information object and lists station and fields. This string is mainly meant to
        be used when working interactively.

        Returns:
            String with receiver information object information.
        """
        field_str = ", ".join(f"{f}={getattr(self, f)!r}" for f in self.fields)
        return f"{type(self).__name__}(station={self.station!r}, {field_str})"

    def __getattr__(self, key: str) -> Any:
        """Get a attribute from the receiver information object using the attribute-notation

        This method is called when a attribute is accessed using a dot, e.g. receiver.type. This is done by 
        forwarding the call to __getitem__. This functionality is used when working interactively.

        Args:
            key:   String, the name of the attribute.

        Returns:
            Attribute data. The datatype depends on the attribute type.
        """
        if key in self.fields:
            return self.info[self.fields[key]]
        raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __setattr__(self, key: str, value: Any) -> None:
        """Set a attribute from the receiver information object

        Args:
            key:     String, the name of the attribute.
            value:   Attribute value.
        """
        if key in self.fields:
            self.info[self.fields[key]] = value
        else:
            super().__setattr__(key, value)

    def __dir__(self) -> List[str]:
        """List all fields and attributes on the class"""
        return super().__dir__() + list(self.fields)


# TODO: Find common solution. Receiver class uses the same functionality.
class ReceiverHistory:

    sources = dict()

    @classmethod
    def get(cls, source: str, station: str, source_path: Union[None, str] = None) -> Union[Any, Any]:
        """Get history class depending on given source  from a specific site information (e.g. antenna, receiver)

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            History class depending on given source
        """
        try:
            return cls.sources[source](station, source_path)
        except KeyError:
            sources = ", ".join(sorted(cls.sources))
            raise ValueError(f"Source {source!r} unknown. Use one of {sources}")

    @classmethod
    def register_source(cls, source_cls: Union[Any, Any]) -> Union[Any, Any]:
        """Register history class in source attribute

        This routine is called via plugins module, which register existing history classes. 

        Args:
            source_cls: Site information history class (e.g. antenna, receiver, ...)

        Returns:
            Site information history class (e.g. antenna, receiver, ...)
        """
        cls.sources[source_cls.source] = source_cls
        return source_cls


# TODO: Find common solution. Antenna class uses the same functionality.
class ReceiverHistoryBase:
    """History base class defining common attributes and methods from a specific site information (e.g. antenna, receiver)
    """

    source = None

    def __init__(self, station: str, source_path: str) -> None:
        """Initialize history information object from a specific site information (e.g. antenna, receiver)

        Args:
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)
        """
        self.station = station.lower()
        self.source_path = source_path
        self.history = self._read_history()

    def _read_history(self):
        raise NotImplementedError

    def __repr__(self):
        """A string describing the history information object from a specific site information (e.g. antenna, receiver)

        The string describes the history information object and lists station and fields. This string is mainly
        meant to be used when working interactively.

        Returns:
            String with history information object information from a specific site information
            (e.g. antenna, receiver).
        """
        return f"{type(self).__name__}(station={self.station!r})"

    def get(self, date: datetime) -> Union[Any, Any]:
        """Get site information object for given date

        Args:
            date:  Date for which site information is chosen

        Returns:
            Site information object for given date            
        """
        for (date_from, date_to), site_info in self.history.items():
            if date_from <= date < date_to:
                return site_info

    @property
    def date_installed(self) -> List[datetime]:
        """Get all installation dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with installation site dates from a specific site information (e.g. antenna, receiver)
        """
        date_installed = list()
        type_prev = None
        for (date_from, date_to) in self.history.keys():

            # Check if receiver was changed
            if type_prev != self.history[(date_from, date_to)].type:
                date_installed.append(date_from)
            type_prev = self.history[(date_from, date_to)].type

        return date_installed

    @property
    def date_removed(self) -> List[datetime]:
        """Get all removing dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with removing site dates from a specific site information (e.g. antenna, receiver)
        """
        date_removed = list()
        type_prev = None
        for (date_from, date_to) in self.history.keys():

            # Check if receiver was changed
            if type_prev != self.history[(date_from, date_to)].type:
                date_removed.append(date_to)
                print(date_to, self.history[(date_from, date_to)].type)
            type_prev = self.history[(date_from, date_to)].type

        return date_removed

    @property
    def firmware_changed(self) -> List[datetime]:
        """Get all dates for an given station, when firmware was changed

        Returns:
            List with removing site dates from a specific site information (e.g. antenna, receiver)
        """
        dates = list()
        firmware_prev = None
        for (date_from, date_to) in self.history.keys():

            # Check if firmware was changed
            if firmware_prev != self.history[(date_from, date_to)].firmware:
                dates.append(date_to)
                print(date_to, self.history[(date_from, date_to)].firmware)
            firmware_prev = self.history[(date_from, date_to)].firmware

        return dates


@ReceiverHistory.register_source
class ReceiverHistorySinex(ReceiverHistoryBase):

    source = "sinex"

    def _read_history(self) -> Dict[Tuple[datetime, datetime], "ReceiverSinex"]:
        """Read receiver site history from SINEX file

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are ReceiverSinex objects.
        """
        if self.source_path is None:
            log.fatal("No SINEX file path is defined.")

        # Find site_id and read antenna history
        p = parsers.parse_file("gnss_sinex_igs", file_path=self.source_path)
        data = p.as_dict()
        if self.station in data:
            raw_info = data[self.station]["site_receiver"]
        elif self.station.upper() in data:
            raw_info = data[self.station.upper()]["site_receiver"]
        else:
            raise ValueError(f"Station {self.station!r} unknown in source '{self.source_path}'.")

        # Create list of receiver history
        history = dict()
        for receiver_info in raw_info:
            receiver = ReceiverSinex(self.station, receiver_info)
            interval = (receiver.date_installed, receiver.date_removed)
            history[interval] = receiver

        return history


class ReceiverSinex(ReceiverBase):
    """ Receiver class handling SINEX file receiver station information
    """

    source = "sinex"
    fields = dict(type="receiver_type", serial_number="serial_number", firmware="firmware")

    @property
    def date_installed(self) -> datetime:
        """ Get receiver installation date from site information attribute

        Returns:
            Receiver installation date
        """
        if self.info["start_time"]:
            return self.info["start_time"]
        else:
            return datetime.min

    @property
    def date_removed(self) -> datetime:
        """ Get receiver removing date from site information attribute

        Returns:
            Receiver removing date
        """
        if self.info["end_time"]:
            return self.info["end_time"]
        else:
            return datetime.max - timedelta(days=367)  # TODO: Minus 367 days is necessary because
            #       _year2days(cls, year, scale) in ./midgard/data/_time.py
            #      does not work. Exceeding of datetime limit 9999 12 31.
