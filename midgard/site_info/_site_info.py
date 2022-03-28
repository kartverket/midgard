"""Base classes for site information.

Description:
------------

All the base classes are abstract classes. There are three base classes defined.

"""

# Standard library imports
import abc
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Union, Iterable


class SiteInfoBase(abc.ABC):
    """Site information base class defining common attributes and methods"""

    source: Union[None, str] = None
    fields: Dict = dict()

    def __init__(self, station: str, site_info: Dict[str, Any]) -> None:
        """Initialize site information object

        Args:
            station:       Station name.
            site_info:  Dictionary with site information.
        """
        self.station = station.lower()
        self._info = site_info

    def __repr__(self) -> str:
        """A string describing the site information object

        The string describes the site information object and lists station and fields. This string is mainly meant to
        be used when working interactively.

        Returns:
            String with site information object information.
        """
        field_str = ", ".join(f"{f}={getattr(self, f)!r}" for f in self.fields)
        return f"{type(self).__name__}(station={self.station!r}, {field_str})"

    def __getattr__(self, key: str) -> Any:
        """Get a attribute from the site information object using the attribute-notation

        This method is called when a attribute is accessed using a dot, e.g. antenna.type. This is done by 
        forwarding the call to __getitem__. This functionality is used when working interactively.

        Args:
            key:   String, the name of the attribute.

        Returns:
            Attribute data. The datatype depends on the attribute type.
        """
        if key in self.fields:
            return self._info[self.fields[key]]
        raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __setattr__(self, key: str, value: Any) -> None:
        """Set a attribute from the site information object

        Args:
            key:     String, the name of the attribute.
            value:   Attribute value.
        """
        if key in self.fields:
            self._info[self.fields[key]] = value
        else:
            super().__setattr__(key, value)

    def __dir__(self) -> List[str]:
        """List all fields and attributes on the class"""
        return super().__dir__() + list(self.fields.keys())

    def copy(self) -> object:
        """Return a copy of object

        Returns:
            A copy of object
        """        
        return type(self)(self.station, deepcopy(self._info))

    @property
    @abc.abstractmethod
    def date_from(self) -> datetime:
        """First valid epoch for site info entry"""

    @property
    @abc.abstractmethod
    def date_to(self) -> datetime:
        """Last valid epoch for site info entry"""


class SiteInfoHistoryBase(abc.ABC):
    """Base class defining common attributes and methods for history classes"""

    source: Union[None, str] = None

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
        if source_data:
            self.history = self._process_history(deepcopy(source_data))
        else:
            self.history = {}

    def __iter__(self):
        """Make this class iterable"""
        return SiteInfoHistoryIterator(self)        

    def __repr__(self) -> str:
        """A string describing the history information object from a specific site information (e.g. antenna, receiver)

        The string describes the history information object and lists station and fields. This string is mainly
        meant to be used when working interactively.

        Returns:
            String with history information object information from a specific site information
            (e.g. antenna, receiver).
        """
        return f"{type(self).__name__}(station={self.station!r})"

    @abc.abstractmethod
    def _process_history(self, source_data: Any) -> Union[None, Dict]:
        """Convert site information from source to a history dictionary

        Args:
            source_data:    Raw data from source
        
        Returns:
            dictionary with history information. Keys should be a tuple of two datetimes and values should be an 
            instance of relevant the site information class based on the type of source_data
        """       

    def get(self, date: datetime) -> Any:
        """Get site information object for given date

        Args:
            date:  Date for which site information is chosen

        Returns:
            Site information object for given date            
        """
        if self.history is None:
            return None
        
        for (date_from, date_to), site_info in self.history.items():
            if date_from <= date < date_to:
                return site_info

    @property
    def date_from(self) -> Union[None, List[datetime]]:
        """Get all installation dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with installation site dates from a specific site information (e.g. antenna, receiver)
        """
        if self.history is None:
            return None
        
        return [date_from for (date_from, date_to) in self.history.keys()]

    @property
    def date_to(self) -> Union[None, List[datetime]]:
        """Get all removing dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with removing site dates from a specific site information (e.g. antenna, receiver)
        """
        if self.history is None:
            return None
        
        return [date_to for (date_from, date_to) in self.history.keys()]


class SiteInfoHistoryIterator:
    """Iterator class for SiteInfoHistory classes"""
    
    def __init__(self, site_info_history):
        """Initialize the iterator"""
        self._current_index = 0
        self._data = site_info_history
    
    def __next__(self):
        """Returns the next SiteInfo object in the history dict of SiteInfoHistory"""
        if self._current_index >= len(self._data.history):
            raise StopIteration
        result = self._data.history[self._key(self._current_index)]
        self._current_index += 1
        return result
     
    def _key(self, index):
        """Converts index to dictionary key"""
        return (self._data.date_from[index], self._data.date_to[index])

class ModuleBase(abc.ABC):
    """Base class for each module of site information (e.g. Antenna, Receiver, ...).
    
    Allows different sources of site information history to be registered.
    """
    sources: Dict = dict() 
    
    @classmethod
    def register_source(cls, source_cls: Any) -> Any:
        """Register history class in sources attribute
    
        Args:
            source_cls: Site information history class (e.g. antenna, receiver, ...)
    
        Returns:
            Site information history class (e.g. antenna, receiver, ...)
        """
        cls.sources[f"{source_cls.source}"] = source_cls
        return source_cls
    
    @classmethod
    def get(
            cls,
            source: str, 
            stations: Union[str, Iterable], 
            date: datetime, 
            source_data: Any,
            source_path: Union[None, str] = None,
    ) -> Any:
        """Get site coordinate object depending on given source

        Args:
            source:       Site information source e.g. 'snx' (SINEX file) or 'ssc' (SSC file)
            station:      Station name.
            date:         Date for getting site information
            source_data:  Source data with site information. 
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Site coordinate object 
        """
        site_dict: Dict[str, Any] = dict()
        if isinstance(stations, str):
            stations = [s.strip().lower() for s in stations.split(",")]
        else:
            stations = [s.lower() for s in stations]

        for station in stations:
            history = cls.sources[source](station, source_data, source_path)
            site_dict[station] = history.get(date) if history is not None else None

        return site_dict
        

    @classmethod
    def get_history(
            cls, 
            source: str,
            stations: Union[str, Iterable], 
            source_data: Any,
            source_path: Union[None, str] = None, 
    ) -> Any:
        """Get site coordinate history object depending on given source

        Args:
            source:       Site information source e.g. 'snx' (SINEX file) or 'ssc' (SSC file)
            station:      Station name.
            source_data:  Source data with site information.
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Site coordinate object 
        """
        site_dict: Dict[str, Any] = dict()
        if isinstance(stations, str):
            stations = [s.strip().lower() for s in stations.split(",")]
        else:
            stations = [s.lower() for s in stations]
        
        for station in stations:
            site_dict[station] = cls.sources[source](station, source_data, source_path)

        return site_dict
