"""A parser for reading water level file in XML format form Norwegian water level API


Description:
------------


Example:
--------

    from midgard import parsers

    p = parsers.parse_file(parser_name="water_level_api_xml",  file_path="water_level_api.xml")
    data = p.as_dict()
    
    from midgard import parsers;p = parsers.parse_file(parser_name="water_level_api_xml",  file_path="water_level_api.xml");data = p.as_dict()
   
"""
# Standard library imports
from datetime import datetime
import pytz
from xml.dom.minidom import parse

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.dev import log, plugins
from midgard.math.unit import Unit
from midgard.parsers import Parser


@plugins.register
class WaterLevelApiXml(Parser):
    """A parser for reading water level file in XML format form Norwegian water level API

    See https://vannstand.kartverket.no/tideapi_no.html for an example

    Following **data** are available after water level data:

    | Parameter           | Description                                                                           |
    | :------------------ | :------------------------------------------------------------------------------------ |
    | flag                | Data flag (obs: observation, pre: prediction, weather: weather effect, forecast:      |
    |                     | forecast)                                                                             |
    | time                | Observation time                                                                      |
    | value               | Water level in [cm]                                                                   |

    and **meta**-data:

    | Key                 | Description                                                                           |
    | :------------------ | :------------------------------------------------------------------------------------ |
    | code                | 3-digit station identifier                                                            |
    | delay               | Time shift applied to the tidal prediction to best represent the given locations in   |
    |                     | [min]                                                                                 | 
    | descr               | Description of water level data                                                       |
    | factor              | Amplitude correction factor                                                           |
    | latitude            | Latitude of water level position in [deg]                                             |
    | longitude           | Longitude of water level position in [deg]                                            |
    | name                | Station name                                                                          |
    | obsname             | Station name of observations                                                          |
    | obscode             | 3-digit station identifier of observations                                            |
    | quality_flag        | Quality flag                                                                          |
    | quality_class       | Quality class                                                                         |
    | quality_description | Quality description                                                                   |    
    | type                | Data type of water level data                                                         |
    | unit                | Unit of water level data                                                              | 
    | __data_path__       | File path                                                                             |
    | __parser_name__     | Parser name                                                                           |
    | __url__             | URL of water level API                                                                |
    """
    
    def read_data(self) -> None:
        """Read data from the XML file

        """
        attribute_def = {
            "qualityClass": "quality_class",
            "qualityDescription": "quality_description",
            "qualityFlag": "quality_flag",
        }
        
        self.data = {
            "value": list(),
            "time": list(),
            "flag": list(),
        }
        document = parse(str(self.file_path))
        
        # Read XML location and data information
        # 
        # Example for locationdata:
        #   <location name="Andenes" code="ANX" latitude="69.326067" longitude="16.134848" delay="0" factor="1.00" obsname="Andenes" obscode="ANX" descr="Tides from Andenes"/>
        #   <reflevelcode>CD</reflevelcode>
        #   <data type="prediction" unit="cm" qualityFlag="1" qualityClass="Quality High" qualityDescription="High quality data: It has been verified against measurements that the data represents physical conditions.">
        #
        # Example for stationdata:
        #   <location name="Andenes" code="ANX" latitude="69.326067" longitude="16.134848">
        #   <data type="observation" unit="cm" reflevelcode="CD">
        #       
        for tagname in ["location", "data"]:
            element = document.getElementsByTagName(tagname)
            if element: 
                for attribute, value in element[0].attributes.items():
                
                    # Rename selected attributes
                    if attribute in attribute_def.keys():
                        attribute = attribute_def[attribute]
                        
                    # Add information to meta variable
                    self.meta[attribute] = value

        # Read XML reflevelcode information
        # 
        # Example for locationdata:
        #   <reflevelcode>CD</reflevelcode>   
        #                 
        element = document.getElementsByTagName("reflevelcode")
        if element:
            self.meta["reflevelcode"] = element[0].childNodes[0].data
            
        # Read XML water level data elements
        # 
        # Example:
        #   <waterlevel value="104.5" time="2021-11-22T00:00:00+01:00" flag="pre"/>
        elements_waterlevel = document.getElementsByTagName("waterlevel")
        for element in elements_waterlevel:
            self.data["value"].append(float(element.attributes.get("value").value))
            self.data["time"].append(datetime.fromisoformat(element.attributes.get("time").value)) # Example to read: 2021-11-22T00:00:00+01:00
            flag = element.attributes.get("flag").value if "flag" in element.attributes.keys() else "weather"
            self.data["flag"].append(flag)


    #
    # GET DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            dset (Dataset): The Dataset where water level observation are stored with following fields:

       |  Field               | Type              | Description                                                       |
       | :------------------- | :---------------- | :---------------------------------------------------------------- |
       | flag                 | numpy.ndarray     | Data flag (obs: observation, pre: prediction, weather: weather    |
       |                      |                   | effect, forecast: forecast)                                       |
       | time                 | TimeTable         | Observation time given as TimeTable object                        |
       | water_level          | numpy.ndarray     | Water level in [m]                                                |

            and following Dataset `meta` data:

       |  Entry               | Type              | Description                                                       |
       | :------------------- | :---------------- | :---------------------------------------------------------------- |
       | __data_path__        | str               | File path                                                         |
       | __url__              | str               | URL of water level API                                            |

        """
        dset = dataset.Dataset(num_obs=len(self.data["time"]))

        time = [d.astimezone(tz=pytz.utc).replace(tzinfo=None) for d in self.data["time"]] # Convert time to UTC
        dset.add_time("time", val=time, scale="utc", fmt="datetime")
        dset.add_float("water_level", val=np.array(self.data["value"]) * Unit.centimeter2meter, unit="meter")
        dset.add_text("flag", val=self.data["flag"])

        dset.meta.update(self.meta)
        return dset



