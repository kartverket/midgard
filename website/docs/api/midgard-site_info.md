# midgard.site_info


## midgard.site_info.antenna
 Antenna site information classes

**Description:**
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


**Example:**
    
    from midgard.site_info import antenna; from datetime import datetime
    antenna.Antenna.get(source="sinex", station="zimm", date=datetime(2018, 10, 1), source_path="igs.snx") 


### **Antenna**

Full name: `midgard.site_info.antenna.Antenna`

Signature: `()`

Main antenna class for getting antenna object depending on site information source

The site information source can be e.g. a SINEX file.


### **AntennaBase**

Full name: `midgard.site_info.antenna.AntennaBase`

Signature: `(station: str, antenna_info: Dict[str, Any]) -> None`

Antenna base class defining common attributes and methods


### **AntennaHistory**

Full name: `midgard.site_info.antenna.AntennaHistory`

Signature: `()`



### **AntennaHistoryBase**

Full name: `midgard.site_info.antenna.AntennaHistoryBase`

Signature: `(station: str, source_path: str) -> None`

History base class defining common attributes and methods from a specific site information (e.g. antenna, receiver)


### **AntennaHistorySinex**

Full name: `midgard.site_info.antenna.AntennaHistorySinex`

Signature: `(station: str, source_path: str) -> None`



### **AntennaSinex**

Full name: `midgard.site_info.antenna.AntennaSinex`

Signature: `(station: str, antenna_info: Dict[str, Any]) -> None`

Antenna class handling SINEX file antenna station information


## midgard.site_info.receiver
 Receiver site information classes

**Description:**

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

**Example:**

    from midgard.site_info import receiver
    receiver.Receiver.get(source="sinex", station="ales", date=datetime(2018, 10, 1), source_path="igs.snx") 


### **Receiver**

Full name: `midgard.site_info.receiver.Receiver`

Signature: `()`

Main receiver class for getting receiver object depending on site information source

The site information source can be e.g. a SINEX file.


### **ReceiverBase**

Full name: `midgard.site_info.receiver.ReceiverBase`

Signature: `(station: str, receiver_info: Dict[str, Any]) -> None`

Receiver base class defining common attributes and methods


### **ReceiverHistory**

Full name: `midgard.site_info.receiver.ReceiverHistory`

Signature: `()`



### **ReceiverHistoryBase**

Full name: `midgard.site_info.receiver.ReceiverHistoryBase`

Signature: `(station: str, source_path: str) -> None`

History base class defining common attributes and methods from a specific site information (e.g. antenna, receiver)


### **ReceiverHistorySinex**

Full name: `midgard.site_info.receiver.ReceiverHistorySinex`

Signature: `(station: str, source_path: str) -> None`



### **ReceiverSinex**

Full name: `midgard.site_info.receiver.ReceiverSinex`

Signature: `(station: str, receiver_info: Dict[str, Any]) -> None`

Receiver class handling SINEX file receiver station information


## midgard.site_info.site_info
Basic functionality for parsing and saving site information

**Description:**

This module contains functions and classes for parsing site information.

This file defines the general structure shared by site information types. More specific format details are implemented
in subclasses. 


### **SiteInfoHistory**

Full name: `midgard.site_info.site_info.SiteInfoHistory`

Signature: `()`



### **SiteInfoHistoryBase**

Full name: `midgard.site_info.site_info.SiteInfoHistoryBase`

Signature: `(station: str, source_path: str) -> None`

History base class defining common attributes and methods from a specific site information (e.g. antenna, receiver)
