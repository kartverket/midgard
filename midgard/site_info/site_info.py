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


class SiteInfoHistory:

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
