"""A parser for reading water level data from open Norwegian water level API


Example:
--------

    from datetime import datetime
    from midgard import parsers

    # XML file with water level data exists
    p = parsers.parse_file(parser_name='api_water_level_norway', file_path='api_water_level_norway')
    data = p.as_dict()

    # Water level data has to be downloaded from API
    p = parsers.parse_file(
                    parser_name='api_water_level_norway', 
                    file_path='api_water_level_norway',
                    latitude=58.974339,
                    longitude=5.730121,
                    from_date=datetime(2021,11,21),
                    to_date=datetime(2021,11,22),
    )
    data = p.as_dict()
    

Description:
------------

See https://api.sehavniva.no/tideapi_no.html for an example
"""
# Standard library imports
from datetime import datetime
import pathlib
import pytz
from typing import Optional, Union
from xml.dom.minidom import parse

# Third party imports
import numpy as np
import pycurl

# Midgard imports
from midgard.data import dataset
from midgard.dev import log
from midgard.dev import plugins
from midgard.files import files
from midgard.math.unit import Unit
from midgard.parsers import Parser


@plugins.register
class ApiWaterLevelNorwayParser(Parser):
    """A parser for reading water level data from open Norwegian water level API

    See https://api.sehavniva.no/tideapi_no.html for an example

    Following **data** are available after water level data:

    | Parameter           | Description                                                                           |
    |---------------------|---------------------------------------------------------------------------------------|
    | flag                | Data flag (obs: observation, pre: prediction, weather: weather effect, forecast:      |
    |                     | forecast)                                                                             |
    | time                | Observation                                                                           |
    | water_level         | Water level in [cm]                                                                   |

    and **meta**-data:

    | Key                 | Description                                                                           |
    |---------------------|---------------------------------------------------------------------------------------|
    | __data_path__       | File path                                                                             |
    | __parser_name__     | Parser name                                                                           |
    | __url__             | URL of water level API                                                                |
    """

    URL = "https://api.sehavniva.no/tideapi.php"

    def __init__(
            self, 
            file_path: Union[str, pathlib.Path], 
            encoding: Optional[str] = None, 
            url: Optional[str] = None,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            from_date: Optional[datetime] = None, 
            to_date: Optional[datetime] = None,
            reference_level: Optional[str] = "chart_datum",
    ) -> None:
        """Set up the basic information needed by the parser

        Args:
            file_path:       Path to file that will be read or downloaded.
            encoding:        Encoding of file that will be read.
            url:             Optional URL from where to download water level data.
            latitude:        Latitude of position in [deg] 
            longitude:       Longitude of position in [deg] 
            from_date:       Starting date of data period
            to_date:         Ending date of data period
            reference_level: Choose reference, which can be chart_datum, mean_sea_level or nn1954
        """
        super().__init__(file_path, encoding)
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            self.download_xml(latitude, longitude, from_date, to_date, url, reference_level)
            self.data_available = self.file_path.exists()

    def download_xml(
            self,  
            latitude: float,
            longitude: float,
            from_date: datetime, 
            to_date: datetime,
            url: Optional[str] = None,
            reference_level: Optional[str] = "chart_datum", 
    ) -> None:
        """Download XML file from url

        Args:
            latitude:        Latitude of position in [deg] 
            longitude:       Longitude of position in [deg] 
            from_date:       Starting date of data period
            to_date:         Ending date of data period
            url:             URL to download from, if None use self.URL instead.
            reference_level: Choose reference, which can be chart_datum, mean_sea_level or nn1954
        """
        reference_level_def = {
            "chart_datum": "cd",
            "mean_sea_level": "msl",
            "nn1954": "nn1954",
            
        }

        # Get URL
        url = self.URL if url is None else url

        try:
            args = dict(
                lat=latitude,
                lon=longitude,
                fromtime=from_date.strftime("%Y-%m-%dT%H:%M"),
                totime=to_date.strftime("%Y-%m-%dT%H:%M"),
                datatype="all",
                refcode=reference_level_def[reference_level],
                place="",
                file="",
                lang="nn",
                interval=10,
                dst=0,  # summer time is not used
                tzone=0,  # UTC
                tide_request="locationdata",
            )
        except AttributeError:
            log.fatal("Following arguments has to be set: latitude, longitude, from_date and to_date")

        url=f"{url}?{'&'.join([f'{k}={v}' for k, v in args.items()])}"
        print(f"Downloading {url} to {self.file_path}")

        # Read data from API to file path
        with files.open(self.file_path, mode="wb") as fid:
            c = pycurl.Curl()
            c.setopt(c.URL, url)
            c.setopt(c.WRITEDATA, fid)
            try:
                c.perform()
            finally:
                c.close()

        self.meta["__url__"] = url


    def read_data(self) -> None:
        """Read data from the XML file

        """
        self.data = {
            "value": list(),
            "time": list(),
            "flag": list(),
        }
        document = parse(str(self.file_path))
        elements = document.getElementsByTagName("waterlevel")
 
        # Read XML elements
        # 
        # Example:
        #   <waterlevel value="104.5" time="2021-11-22T00:00:00+01:00" flag="pre"/>
        for element in elements:
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
       |----------------------|-------------------|-------------------------------------------------------------------|
       | flag                 | numpy.ndarray     | Data flag (obs: observation, pre: prediction, weather: weather    |
       |                      |                   | effect, forecast: forecast)                                       |
       | time                 | TimeTable         | Observation time given as TimeTable object                        |
       | water_level          | numpy.ndarray     | Water level in [m]                                                |

            and following Dataset `meta` data:

       |  Entry               | Type              | Description                                                       |
       |----------------------|-------------------|-------------------------------------------------------------------|
       | __data_path__        | str               | File path                                                         |
       | __url__              | str               | URL of water level API                                            |

        """
        dset = dataset.Dataset(num_obs=len(self.data["time"]))

        time = [d.astimezone(tz=pytz.utc).replace(tzinfo=None) for d in self.data["time"]] # Convert time to UTC
        dset.add_time("time", val=time, scale="utc", fmt="datetime")
        dset.add_float("water_level", val=np.array(self.data["value"]) * Unit.centimeter2meter)
        dset.add_text("flag", val=self.data["flag"])

        dset.meta.update(self.meta)
        return dset



