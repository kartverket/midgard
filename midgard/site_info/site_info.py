"""Module that provides site information as unified objects independent of source. 

Description:
------------

"""
# Standard library imports
from datetime import datetime
from typing import Union, Any

from midgard.site_info.antenna import Antenna
from midgard.site_info.receiver import Receiver
from midgard.site_info.site_coord import SiteCoord


_MODULES = [Antenna, Receiver, SiteCoord]

class SiteInfo:
    """Main site information class for getting site information object depending on site information source

    The site information source can be e.g. a SINEX file. The source data has to be read for each station from a file,
    whereby the file path is defined via 'source_path' argument. If site information for several stations should be 
    provided, then it is recommended to provide the data via 'source_data' argument. The data can be read e.g. for a 
    SINEX file like:

        from midgard import parsers
        p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
        source_data = p.as_dict()

    """

    sources = dict()

    @classmethod
    def get(
        cls,
        source: str, 
        stations: str, 
        date: datetime, 
        source_data: Union[None, Any],
        source_path: Union[None, str] = None,
    ) -> Union[Any, Any]:
        """Get site information object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            date:         Date for getting site information
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored. 

        Returns:
            Site information object 
        """
        site_info_history = {}
        
        if isinstance(stations, str):
            stations = [s.strip() for s in stations.split(",")]
        
        for sta in stations:
            site_dict = site_info_history.setdefault(sta, {})      
            for module in _MODULES:
                module_name = module.__name__.lower()
                history = module.get_history(source, sta, source_data, source_path)
                site_dict[module_name] = history.get(date) if history is not None else None

        return {s: site_info_history[s] for s in stations}

    @classmethod
    def get_history(
            cls, 
            source: str,
            stations: str,
            source_data: Union[None, Any],
            source_path: Union[None, str] = None,
            
    ) -> Union[Any, Any]:
        """Get site information history object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored. 

        Returns:
            Site information object 
        """
        site_info_history = {}
        
        if isinstance(stations, str):
            stations = [s.strip() for s in stations.split(",")]
        
        for sta in stations:
            site_dict = site_info_history.setdefault(sta, {})      
            for module in _MODULES:
                module_name = module.__name__.lower()
                site_dict[module_name] = module.get_history(source, sta, source_data, source_path)

        return {s: site_info_history[s] for s in stations}
    


# class SiteInfoHistory:
#
#     sources = dict()
#
#     @classmethod
#     def get(
#             cls, 
#             module: str, 
#             source: str, 
#             source_data: Union[None, Any],
#             station: str = None, 
#             source_path: Union[None, str] = None,
#
#     ) -> Union[Any, Any]:
#         """Get history class depending on given source  from a specific site information (e.g. antenna, receiver)
#
#         The module name is used to distinguish between different site information classes calling this function.
#
#         Args:
#             module:       Module name.
#             source:       Site information source e.g. 'sinex' (SINEX file)
#             station:      Station name.
#             source_path:  Source path of site information source (e.g. file path of SINEX file)
#             source_data:  Source data with site information. If source data are defined, then 'source_path' is 
#                           ignored.
#
#         Returns: cls.sources[f"{source}_{type_}"]
#             History class depending on given source
#         """
#
#         type_ = module.split(".")[-1]
#         if f"{source}_{type_}" not in cls.sources:
#             sources = set([v.split("_")[0] for v in cls.sources.keys()])
#             raise ValueError(f"Source {source!r} unknown. Use one of: {', '.join(sources)}.")
#
#         return cls.sources[f"{source}_{type_}"](station, source_data, source_path)
