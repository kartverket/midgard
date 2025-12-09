"""A parser for reading water level file in XML format form Norwegian water level API


Description:
------------
Note, that 'forecast' data are not read by this parser.

Example:
--------

    from midgard import parsers

    p = parsers.parse_file(parser_name="water_level_api_xml",  file_path="water_level_api.xml")
    data = p.as_dict()
   
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

    Following **data** are available in dependency of given water level data:

    | Parameter                  | Description                                                                    |
    | :------------------------- | :----------------------------------------------------------------------------- |
    | flag                       | Data flag of water level observation data (obs: observation, pre: prediction), |
    |                            | which can also predicted tidal data                                            |
    | time                       | Observation time                                                               |
    | water_level                | Observed/estimated water level data in [cm]                                    |
    | water_level_predicted      | Tidal prediction data in [cm]                                                  |
    | water_level_weather_effect | Weather effect [cm]                                                            |

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
    | quality_flag        | Quality flag of 'type' data                                                           |
    | quality_class       | Quality class of 'type' data                                                          |
    | quality_description | Quality description of 'type' data                                                    |    
    | type                | Data type of water level data                                                         |
    | unit                | Unit of water level data (information provided from 'type' data)                      | 
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
            "water_level": list(),
            "water_level_predicted": list(),
            "water_level_weather_effect": list(),
            "time": list(),
            "flag": list(),
        }

        type_def = {
            "observation": "water_level",
            "prediction": "water_level_predicted",
            "weathereffect": "water_level_weather_effect",

        }

        # Read XML file
        document = parse(str(self.file_path))
        
        # Get XML location and data information
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

        # Get XML reflevelcode information
        # 
        # Example for locationdata:
        #   <reflevelcode>CD</reflevelcode>   
        #                 
        element = document.getElementsByTagName("reflevelcode")
        if element:
            self.meta["reflevelcode"] = element[0].childNodes[0].data
            
        # Get XML water level data elements
        # 
        # Example:
        #    <data type="observation" unit="cm" qualityFlag="2" qualityClass="Quality OK" qualityDescription="Data with good quality suited for most uses: Either it has been verified against measurements that the data mostly represents the physical conditions, or we assume the data represents the physical conditions, but it has not been verified against measurements.">
        #    <waterlevel value="-28.5" time="2024-01-01T00:00:00+00:00" flag="obs"/>
        #    <waterlevel value="-28.4" time="2024-01-01T00:10:00+00:00" flag="obs"/>
        #    </data>
        #    <data type="prediction" unit="cm" qualityFlag="1" qualityClass="Quality High" qualityDescription="High quality data: It has been verified against measurements that the data represents physical conditions.">
        #    <waterlevel value="-1.2" time="2024-01-01T00:00:00+00:00" flag="pre"/>
        #    <waterlevel value="-1.7" time="2024-01-01T00:10:00+00:00" flag="pre"/>
        #    </data>
        for type_ in ["observation", "prediction", "weathereffect"]:

            elements = self._get_data_by_type(document, type_)
            if not elements:
                del self.data[type_def[type_]]  # Delete 'type_' for which no observations exists
                if type_ == "observation":
                    del self.data["flag"]
                continue

            if not self.data["time"]:
                for element in elements:
                    self.data["time"].append(datetime.fromisoformat(element.getAttribute("time"))) # Example to read: 2021-11-22T00:00:00+01:00

                    if type_ == "observation":
                        self.data["flag"].append(element.getAttribute("flag"))

            for element in elements:
                self.data[type_def[type_]].append(float(element.getAttribute("value")))
              

    #
    # GET DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Note, that 'forecast' data are not saved in the dataset.

        Returns:
            dset (Dataset): The Dataset where water level observation are stored with following fields:

       |  Field                     | Type              | Description                                                 |
       | :------------------------- | :---------------- | :---------------------------------------------------------- |
       | flag                       | numpy.array       | Data flag of water level observation data (obs: observation,|
       |                            |                   | pre: prediction), which can also predicted tidal data       |
       | time                       | TimeTable         | Observation time given as TimeTable object                  |
       | water_level                | numpy.array       | Observed/estimated water level data in [m]                  |
       | water_level_predicted      | numpy.array       | Tidal prediction data in [m]                                |
       | water_level_weather_effect | numpy.array       | Weather effect [m]                                          |

            and following Dataset `meta` data:

       |  Entry               | Type              | Description                                                       |
       | :------------------- | :---------------- | :---------------------------------------------------------------- |
       | __data_path__        | str               | File path                                                         |
       | __url__              | str               | URL of water level API                                            |

        """
        dset = dataset.Dataset(num_obs=len(self.data["time"]))
        dset.meta.update(self.meta)

        for field in self.data.keys():
            if field == "time":
                time = np.array([d.astimezone(tz=pytz.utc).replace(tzinfo=None) for d in self.data["time"]]) # Convert time to UTC
                dset.add_time("time", val=time, scale="utc", fmt="datetime")

            elif field == "flag":
                dset.add_text(field, val=self.data[field])

            elif field in ["water_level", "water_level_predicted", "water_level_weather_effect"]:
                dset.add_float(field, val=np.array(self.data[field]) * Unit.centimeter2meter, unit="meter")

        return dset


    #
    # AUXILIARY FUNCTIONS
    #
    def _get_data_by_type(self, document, type_: str):
        """Get water level by given type name

        Args:
            type_: Type name, which can be 'observation', 'prediction' or 'weathereffect'

        Returns:
            
        """
        # Find the specific <data type="..."> tag
        data_nodes = document.getElementsByTagName("data")
        for data_node in data_nodes:

            if data_node.getAttribute("type") == type_:
                # Get all child <waterlevel> elements
                return data_node.getElementsByTagName("waterlevel")

        return []



