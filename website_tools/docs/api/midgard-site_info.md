# midgard.site_info


## midgard.site_info._site_info
Base classes for site information.

**Description:**

All the base classes are abstract classes. There are three base classes defined.



### **ModuleBase**

Full name: `midgard.site_info._site_info.ModuleBase`

Signature: `()`

Base class for each module of site information (e.g. Antenna, Receiver, ...).

Allows different sources of site information history to be registered.


### **SiteInfoBase**

Full name: `midgard.site_info._site_info.SiteInfoBase`

Signature: `(station: str, site_info: Dict[str, Any]) -> None`

Site information base class defining common attributes and methods

### **SiteInfoHistoryBase**

Full name: `midgard.site_info._site_info.SiteInfoHistoryBase`

Signature: `(station: str, source_data: Any = None, source_path: str = None) -> None`

Base class defining common attributes and methods for history classes

### **SiteInfoHistoryIterator**

Full name: `midgard.site_info._site_info.SiteInfoHistoryIterator`

Signature: `(site_info_history)`

Iterator class for SiteInfoHistory classes

## midgard.site_info.antenna
Antenna information classes

**Description:**
This module is divided into three different types of classes:

    1. Main class Antenna that provides basic functionality to the user. See examples
    2. Antenna source type classes:
        - There is one class for each source type
        - A class with all relevant site coordinate information for a point in time.
    3. Antenna history source type classes:
        - There is one class for each source type
        - Converts input from source_data to a object of type AntennaHistorySinex, etc and provides functions
          for accessing the history and relevant dates. 
        - The history consist of a time interval for which the entry is valid and an instance of an antenna 
          source type class for each defined time interval.

    If a source type does not contain information about the antenna the module will return 'None'.

**Example:**
    
    from midgard import parsers
    p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
    source_data = p.as_dict()
    all_stations = source_data.keys()
    
    Antenna.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
    Antenna.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)
    
    Antenna.get_history("snx", "osls", source_data, source_path=p.file_path)
    Antenna.get_history("snx", all_stations, source_data, source_path=p.file_path)



### **Antenna**

Full name: `midgard.site_info.antenna.Antenna`

Signature: `()`

Main class for converting antenna information from various sources into unified classes

### **AntennaHistorySinex**

Full name: `midgard.site_info.antenna.AntennaHistorySinex`

Signature: `(station: str, source_data: Any = None, source_path: str = None) -> None`



### **AntennaHistorySsc**

Full name: `midgard.site_info.antenna.AntennaHistorySsc`

Signature: `(station: str, source_data: Any = None, source_path: str = None) -> None`



### **AntennaSinex**

Full name: `midgard.site_info.antenna.AntennaSinex`

Signature: `(station: str, site_info: Dict[str, Any]) -> None`

Antenna class handling SINEX file antenna station information


## midgard.site_info.receiver
Receiver information classes

**Description:**
This module is divided into three different types of classes:

    1. Main class Receiver that provides basic functionality to the user. See examples
    2. Receiver source type classes:
        - There is one class for each source type
        - A class with all relevant site coordinate information for a point in time.
    3. Receiver history source type classes:
        - There is one class for each source type
        - Converts input from source_data to a object of type ReceiverHistorySinex, etc and provides functions
          for accessing the history and relevant dates. 
        - The history consist of a time interval for which the entry is valid and an instance of a receiver 
          source type class for each defined time interval.

    If a source type does not contain information about the receiver the module will return 'None'.

**Example:**
    
    from midgard import parsers
    p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
    source_data = p.as_dict()
    all_stations = source_data.keys()
    
    Receiver.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
    Receiver.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)
    
    Receiver.get_history("snx", "osls", source_data, source_path=p.file_path)
    Receiver.get_history("snx", all_stations, source_data, source_path=p.file_path)



### **Receiver**

Full name: `midgard.site_info.receiver.Receiver`

Signature: `()`

Main class for converting receiver information from various sources into unified classes

### **ReceiverHistorySinex**

Full name: `midgard.site_info.receiver.ReceiverHistorySinex`

Signature: `(station: str, source_data: Any = None, source_path: str = None) -> None`



### **ReceiverHistorySsc**

Full name: `midgard.site_info.receiver.ReceiverHistorySsc`

Signature: `(station: str, source_data: Any = None, source_path: str = None) -> None`



### **ReceiverSinex**

Full name: `midgard.site_info.receiver.ReceiverSinex`

Signature: `(station: str, site_info: Dict[str, Any]) -> None`

Receiver class handling SINEX file receiver station information


## midgard.site_info.site_coord
Site cooridnate information classes

**Description:**
This module is divided into three different types of classes:

    1. Main class SiteCoord that provides basic functionality to the user. See examples
    2. Site coordinate source type classes:
        - There is one class for each source type
        - A class with all relevant site coordinate information for a point in time.
    3. Site coordinate history source type classes:
        - There is one class for each source type
        - Converts input from source_data to a object of type SiteCoordHistorySinex, etc and provides functions
          for accessing the history and relevant dates. 
        - The history consist of a time interval for which the entry is valid and an instance of a site coordinate 
          source type class for each defined time interval.

    If a source type does not contain information about the site coordinates the module will return 'None'.

**Example:**
    
    from midgard import parsers
    from midgard.site_info.site_coord import SiteCoord

    # Read SINEX data    
    p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
    source_data = p.as_dict()
    all_stations = source_data.keys()
    
    # Get station information
    SiteCoord.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
    SiteCoord.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)
    
    SiteCoord.get_history("snx", "osls", source_data, source_path=p.file_path)
    SiteCoord.get_history("snx", all_stations, source_data, source_path=p.file_path)



### **SiteCoord**

Full name: `midgard.site_info.site_coord.SiteCoord`

Signature: `()`

Main class for converting site coordinates from various sources into unified classes

### **SiteCoordHistorySinex**

Full name: `midgard.site_info.site_coord.SiteCoordHistorySinex`

Signature: `(station: str, source_data: Any = None, source_path: str = None) -> None`



### **SiteCoordHistorySsc**

Full name: `midgard.site_info.site_coord.SiteCoordHistorySsc`

Signature: `(station: str, source_data: Any = None, source_path: str = None) -> None`



### **SiteCoordSinex**

Full name: `midgard.site_info.site_coord.SiteCoordSinex`

Signature: `(station: str, site_info: Dict[str, Any]) -> None`

Site coordinate class handling SINEX file station coordinate information

### **SiteCoordSsc**

Full name: `midgard.site_info.site_coord.SiteCoordSsc`

Signature: `(station: str, site_info: Dict[str, Any]) -> None`

Site coordinate class handling SSC file station coordinate information


## midgard.site_info.site_info
Module that provides site information as unified objects independent of source. 

Site information consists of antenna and receiver information and coordinates for a station.
If a source type does not contain information about the antenna, receiver or coordinate the 
corresponding entry will be set to 'None'.

Example:

from midgard import parsers
p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
source_data = p.as_dict()
all_stations = source_data.keys()

SiteInfo.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
SiteInfo.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)

SiteInfo.get_history("snx", "osls", source_data, source_path=p.file_path)
SiteInfo.get_history("snx", all_stations, source_data, source_path=p.file_path)

**Description:**



### **SiteInfo**

Full name: `midgard.site_info.site_info.SiteInfo`

Signature: `()`

Main site information class for site information from various sources into unified classes

