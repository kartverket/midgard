"""Base classes for site information with and without history.

Description:
------------

Abstract classes.
"""

# Standard library imports
import abc
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Union
from abc import abstractmethod


class SiteInfoBase(abc.ABC):
    """Site information base class defining common attributes and methods
    """

    source = None
    fields = dict()

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
        return super().__dir__() + list(self.fields)

    def copy(self) -> object:
        """Return a copy of object

        Returns:
            A copy of object
        """        
        return type(self)(self.station, deepcopy(self._info))

    @property
    @abstractmethod
    def date_from(self):
        """
        """
        return NotImplemented

    @property
    @abstractmethod
    def date_to(self):
        """
        """
        return NotImplemented


class SiteInfoHistoryBase(abc.ABC):
    """History base class defining common attributes and methods from a specific site information (e.g. antenna, receiver)
    """

    source = None

    def __init__(self, station: str, source_data: Any, source_path: str) -> None:
        """Initialize history information object from a specific site information (e.g. antenna, receiver)

        Args:
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored.
        """
        self.station = station.lower()
        self.source_path = source_path
        self.history = self._process_history(source_data)

    def _process_history(self, **kwargs):
        """Read site information history 

        Routine has to be implemented in site_info module classes.
        """
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
        if self.history is None:
            return None
        
        for (date_from, date_to), site_info in self.history.items():
            if date_from <= date < date_to:
                return site_info

    @property
    def date_from(self) -> List[datetime]:
        """Get all installation dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with installation site dates from a specific site information (e.g. antenna, receiver)
        """
        if self.history is None:
            return None
        
        return [date_from for (date_from, date_to) in self.history.keys()]

    @property
    def date_to(self) -> List[datetime]:
        """Get all removing dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with removing site dates from a specific site information (e.g. antenna, receiver)
        """
        if self.history is None:
            return None
        
        return [date_to for (date_from, date_to) in self.history.keys()]
