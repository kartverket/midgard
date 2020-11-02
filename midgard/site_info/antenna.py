""" Antenna site information classes

Description:
------------
The antenna module generates a antenna object based on site information from 
the SINEX file or other sources.

Following steps are carried out for getting a antenna object:

    1. Plugins modulen register AntennaHistory classes (e.g. 
       AntennaHistorySinex) and updates the 'sources' attribute of the 
       AntennaHistory class. 
    2. The Antenna object is initialized by calling the Antenna.get function. 
    3. The AntennaHistory.get function is called via the Antenna.get function.
       Here the correct AntennaHistory class is choosen by accessing the 
       registered 'sources' attribute of the AntennaHistory class.
    4. The AntennaBase.get function reads the antenna information via the
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

# from midgard.site_info.site_info import SiteInfoHistory, SiteInfoHistoryBase  TODO: Does not work together with registering receiver plugin?


class Antenna:
    """Main antenna class for getting antenna object depending on site information source

    The site information source can be e.g. a SINEX file.
    """

    sources = dict()

    @classmethod
    def get(
        cls, source: str, station: str, date: datetime, source_path: Union[None, str] = None
    ) -> Union["AntennaSinex", Any]:
        """Get antenna object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            date:         Date for getting site information
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Antenna object 
        """
        history = AntennaHistory.get(source, station, source_path)
        return history.get(date)

    @classmethod
    def get_history(
        cls, source: str, station: str, source_path: Union[None, str] = None
    ) -> Union["AntennaSinex", Any]:
        """Get antenna history object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Antenna object 
        """
        history = AntennaHistory.get(source, station, source_path)
        return history


class AntennaBase:
    """Antenna base class defining common attributes and methods
    """

    source = None
    fields = dict(
        date_installed="date_installed",
        date_removed="date_removed",
        type="type",
        serial_number="serial_number",
        radome_type="radome_type",
        radome_serial_number="radome_serial_number",
    )

    def __init__(self, station: str, antenna_info: Dict[str, Any]) -> None:
        """Initialize antenna information object

        Args:
            station:       Station name.
            antenna_info:  Dictionary with antenna information.
        """
        self.station = station.lower()
        self.info = antenna_info

    def __repr__(self) -> str:
        """A string describing the antenna information object

        The string describes the antenna information object and lists station and fields. This string is mainly meant to
        be used when working interactively.

        Returns:
            String with antenna information object information.
        """
        field_str = ", ".join(f"{f}={getattr(self, f)!r}" for f in self.fields)
        return f"{type(self).__name__}(station={self.station!r}, {field_str})"

    def __getattr__(self, key: str) -> Any:
        """Get a attribute from the antenna information object using the attribute-notation

        This method is called when a attribute is accessed using a dot, e.g. antenna.type. This is done by 
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
        """Set a attribute from the antenna information object

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
class AntennaHistory:

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


# TODO: Find common solution. Receiver class uses the same functionality.
class AntennaHistoryBase:
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
        return [date_from for (date_from, date_to) in self.history.keys()]

    @property
    def date_removed(self) -> List[datetime]:
        """Get all removing dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with removing site dates from a specific site information (e.g. antenna, receiver)
        """
        return [date_to for (date_from, date_to) in self.history.keys()]


@AntennaHistory.register_source
class AntennaHistorySinex(AntennaHistoryBase):

    source = "sinex"

    def _read_history(self) -> Dict[Tuple[datetime, datetime], "AntennaSinex"]:
        """Read antenna site history from SINEX file

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are AntennaSinex objects.
        """
        if self.source_path is None:
            log.fatal("No SINEX file path is defined.")

        # Find site_id and read antenna history
        p = parsers.parse_file("gnss_sinex_igs", file_path=self.source_path)
        data = p.as_dict()
        if self.station in data:
            raw_info = data[self.station]["site_antenna"]
        elif self.station.upper() in data:
            raw_info = data[self.station.upper()]["site_antenna"]
        else:
            raise ValueError(f"Station '{self.station}' unknown in source '{self.source_path}'.")

        # Create list of antenna history
        history = dict()
        for antenna_info in raw_info:
            antenna = AntennaSinex(self.station, antenna_info)
            interval = (antenna.date_installed, antenna.date_removed)
            history[interval] = antenna

        return history


class AntennaSinex(AntennaBase):
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
    def date_installed(self) -> datetime:
        """ Get antenna installation date from site information attribute

        Returns:
            Antenna installation date
        """
        if self.info["start_time"]:
            return self.info["start_time"]
        else:
            return datetime.min

    @property
    def date_removed(self) -> datetime:
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
