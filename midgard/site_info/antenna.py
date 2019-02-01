""" Antenna site information classes

Description:
------------
The antenna module generates a antenna object based on site information from 
the SINEX file or other sources.

Example for getting antenna object:
    from midgard.site_info import antenna
    antenna.Antenna.get(source="sinex", station="ales", date=datetime(2018, 10, 1)) 

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
"""
# Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union


class AntennaHistory:

    sources = dict()

    @classmethod
    def get(cls, source: str, station: str) -> Union["AntennaHistorySinex", Any]:
        """Get antenna history class depending on given source

        Returns:
            Antenna history class depending on given source
        """
        try:
            return cls.sources[source](station)
        except KeyError:
            sources = ", ".join(sorted(cls.sources))
            raise ValueError(f"Source {source!r} unknown. Use one of {sources}")

    @classmethod
    def date_installed(cls, source: str, station: str) -> List[datetime]:
        """Get all antenna installation dates for an given station

        Returns:
            List with antenna installation site dates
        """
        antenna_info = cls.get(source, station)
        return [date_from for (date_from, date_to) in antenna_info.history.keys()]

    @classmethod
    def date_removed(cls, source: str, station: str) -> List[datetime]:
        """Get all antenna removing dates for an given station

        Returns:
            List with antenna removing site dates
        """
        antenna_info = cls.get(source, station)
        return [date_to for (date_from, date_to) in antenna_info.history.keys()]

    @classmethod
    def register_source(cls, source_cls: Union["AntennaHistorySinex", Any]) -> Union["AntennaHistorySinex", Any]:
        """Register antenna history class in source attribute

        This routine is called via plugins module, which register existing antenna history classes (e.g.
        AntennaHistorySinex). 

        Args:
            source_cls: Antenna history class

        Returns:
            Antenna history class
        """
        cls.sources[source_cls.source] = source_cls
        return source_cls


class AntennaHistoryBase:
    """Antenna history base class defining common attributes and methods
    """

    source = None

    def __init__(self, station: str) -> None:
        """Initialize antenna history information object

        Args:
            station:       Station name.
        """
        self.station = station.lower()
        self.history = self._read_history()

    def _read_history(self):
        raise NotImplementedError

    def __repr__(self):
        """A string describing the antenna history information object

        The string describes the antenna history information object and lists station and fields. This string is mainly
        meant to be used when working interactively.

        Returns:
            String with antenna history information object information.
        """
        return f"{type(self).__name__}(station={self.station!r})"

    def get(self, date: datetime) -> Union["AntennaSinex", Any]:
        """Get antenna object for given date

        Args:
            date:  Date for which antenna information is chosen

        Returns:
            Antenna object for given date            
        """
        for (date_from, date_to), antenna in self.history.items():
            if date_from <= date < date_to:
                return antenna

        raise ValueError(f"Antenna information is not available for {self.station!r} at {date}")


@AntennaHistory.register_source
class AntennaHistorySinex(AntennaHistoryBase):

    source = "sinex"


class Antenna:
    """Main antenna class for getting antenna object depending on site information source

    The site information source can be e.g. a SINEX file.
    """

    sources = dict()

    @classmethod
    def get(cls, source: str, station: str, date: datetime) -> Union["AntennaSinex", Any]:
        """Get antenna object depending on given source

        Args:
            station: Station name.
            date:    Date for getting site information
            source:  Site information source e.g. 'sinex' (SINEX file)

        Returns:
            Antenna object 
        """
        history = AntennaHistory.get(source, station)
        return history.get(date)


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
            antenna_info:  
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


class AntennaSinex(AntennaBase):
    """ Antenna class handling SINEX file antenna station information
    """

    source = "sinex"
    fields = dict(
        type="antennaTypeName",
        serial_number="serialNumber",
        radome_type="radomeType",
        radome_serial_number="radomeSnr",
    )
