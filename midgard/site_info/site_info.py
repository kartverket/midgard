"""Module that provides site information as unified objects independent of source. 

Description:
------------

Site information consists of antenna, eccentricity and receiver information and coordinates 
for a station. If a source type does not contain information about the antenna, receiver or 
coordinate the corresponding entry will be set to 'None'.


Example:
--------

    from midgard import parsers
    from midgard.site_info.site_info import SiteInfo
    from datetime import datetime
    
    p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
    source_data = p.as_dict()
    all_stations = source_data.keys()
    
    SiteInfo.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
    SiteInfo.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)
    
    SiteInfo.get_history("snx", "osls", source_data, source_path=p.file_path)
    SiteInfo.get_history("snx", all_stations, source_data, source_path=p.file_path)

Description:
------------

"""
# Standard library imports
from datetime import datetime
from typing import Dict, Iterable, Union, Any

from midgard.site_info.antenna import Antenna
from midgard.site_info.eccentricity import Eccentricity
from midgard.site_info.identifier import Identifier
from midgard.site_info.receiver import Receiver
from midgard.site_info.site_coord import SiteCoord


_MODULES = [Antenna, Eccentricity, Identifier, Receiver, SiteCoord]

class SiteInfo:
    """Main site information class for site information from various sources into unified classes

    """

    @classmethod
    def get(
        cls,
        source: str, 
        source_data: Any,
        stations: Union[str, Iterable], 
        date: Union[None, datetime] = None, 
        source_path: Union[None, str] = None,
    ) -> Dict:
        """Get site information dictionary from given source for specified date

        Args:
            source:       Site information source type: e.g. 'snx' (SINEX file), 'ssc' (SSC file) or other
            source_data:  Source data with site information from specified source type.  
            stations:     List of station names.
            date:         Date for getting site information.
            source_path:  Source path of site information source (e.g. file path of SINEX file) or other. Optional
                          argument. Only used as information about where the data was obtained. 

        Returns:
            Dictionary with site information for each station given valid for the specified date
        """
        site_info: Dict[str, Dict] = {}
        
        if isinstance(stations, str):
            stations = [s.strip().lower() for s in stations.split(",")]
        else:
            stations = [s.lower() for s in stations]
        
        for sta in stations:
            site_dict = site_info.setdefault(sta, {})      
            for module in _MODULES:
                module_name = "site_coord" if module.__name__ == "SiteCoord" else module.__name__.lower()
                entry = module.get(
                    source, 
                    source_data, 
                    sta, 
                    None if module.__name__ == "Identifier" else date, 
                    source_path,
                )
                site_dict[module_name] = entry[sta] if sta in entry else None

        return site_info

    @classmethod
    def get_history(
            cls, 
            source: str,
            source_data: Any,
            stations: Union[str, Iterable],
            source_path: Union[None, str] = None,
    ) -> Dict:
        """Get site information dictionary with complete history from given source

        Args:
            source:       Site information source type: e.g. 'snx' (SINEX file), 'ssc' (SSC file) or other
            source_data:  Source data with site information from specified source type.  
            stations:     List of station names.
            source_path:  Source path of site information source (e.g. file path of SINEX file) or other. Optional
                          argument. Only used as information about where the data was obtained. 

        Returns:
            Dictionary with site information for each station given
        """

        site_info_history: Dict[str, Dict] = {}
        
        if isinstance(stations, str):
            stations = [s.strip().lower() for s in stations.split(",")]
        else:
            stations = [s.lower() for s in stations]
        
        for sta in stations:
            site_dict = site_info_history.setdefault(sta, {})      
            for module in _MODULES:
                if module.__name__ == "Identifier":
                    continue
                module_name = "site_coord" if module.__name__ == "SiteCoord" else module.__name__.lower()
                history = module.get_history(source, source_data, sta, source_path)
                site_dict[module_name] = history[sta] if sta in history else None

        return site_info_history
    
