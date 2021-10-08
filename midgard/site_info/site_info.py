"""Basic functionality for parsing and saving site information

Description:
------------

This module contains functions and classes for parsing site information.

This file defines the general structure shared by site information types. More specific format details are implemented
in subclasses. 
"""

# Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union



class SiteInfo:
    """Main site information class for getting site information object depending on site information source

    The site information source can be e.g. a SINEX file.
    """

    sources = dict()

    @classmethod
    def get(
        cls, source: str, station: str, date: datetime, source_path: Union[None, str] = None
    ) -> Union[Any, Any]:
        """Get site information object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            date:         Date for getting site information
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Site information object 
        """
        history = SiteInfoHistory.get(source, station, source_path)
        return history.get(date)

    @classmethod
    def get_history(
        cls, source: str, station: str, source_path: Union[None, str] = None
    ) -> Union[Any, Any]:
        """Get site information history object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            Site information object 
        """
        history = SiteInfoHistory.get(source, station, source_path)
        return history


class SiteInfoBase:
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
        self.info = site_info

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
            return self.info[self.fields[key]]
        raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __setattr__(self, key: str, value: Any) -> None:
        """Set a attribute from the site information object

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


class SiteInfoHistory:

    sources = dict()

    @classmethod
    def get(cls, module: str, source: str, station: str, source_path: Union[None, str] = None) -> Union[Any, Any]:
        """Get history class depending on given source  from a specific site information (e.g. antenna, receiver)

        The module name is used to distinguish between different site information classes calling this function.

        Args:
            module:       Module name.
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)

        Returns:
            History class depending on given source
        """
        type_ = module.split(".")[-1]
        try:
            return cls.sources[f"{source}_{type_}"](station, source_path)
        except KeyError:
            sources = set([v.split("_")[0] for v in cls.sources.keys()])
            raise ValueError(f"Source {source!r} unknown. Use one of: {', '.join(sources)}.")


    @classmethod
    def register_source(cls, source_cls: Union[Any, Any]) -> Union[Any, Any]:
        """Register history class in source attribute

        This routine is called via plugins module, which register existing history classes. 

        Args:
            source_cls: Site information history class (e.g. antenna, receiver, ...)

        Returns:
            Site information history class (e.g. antenna, receiver, ...)
        """
        type_ = source_cls.__module__.split(".")[-1]
        cls.sources[f"{source_cls.source}_{type_}"] = source_cls
        return source_cls


class SiteInfoHistoryBase:
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
    def date_from(self) -> List[datetime]:
        """Get all installation dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with installation site dates from a specific site information (e.g. antenna, receiver)
        """
        return [date_from for (date_from, date_to) in self.history.keys()]

    @property
    def date_to(self) -> List[datetime]:
        """Get all removing dates for an given station from a specific site information (e.g. antenna, receiver)

        Returns:
            List with removing site dates from a specific site information (e.g. antenna, receiver)
        """
        return [date_to for (date_from, date_to) in self.history.keys()]
