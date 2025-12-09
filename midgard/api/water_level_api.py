"""Python wrapper around the Norwegian water level API (https://vannstand.kartverket.no/tideapi_en.html)

Description:
------------
The Python wrapper access only the water level data from the API.

Water level information includes information about levels, tide tables with high and low waters and tidal 
constituents, and data such as predicted tides, (estimated) observed water level and surge, and water level forecasts.

Using the API, water level information can be requested from a specific water level station, typically one of the 
permanent tide gauges, or for a particular position. All requests for water level information for a position are based
on a model where the Norwegian coast has been divided into tidal zones. For each valid zone, the tide tables, 
predictions and tide related levels are calculated based on tidal prediction from an associated station with assigned
correction factor for height and delay for time shift. Most zones return the observed weather effect (surge) from the
closest permanent station. The estimated observations of water level returned are the sum of the adjusted tidal 
predictions and the observed weather effects from the most relevant permanent tide gauge. The adjusted tidal 
predictions and the observed weather effect can be based on different stations. 

The different types of levels include important reference levels used in maps and other official products, astronomical
levels related to the tide, observed extremes and statistical return levels for extreme water levels with different
return periods.

Terms of Use:
-------------
The API is open for everybody and does not require registration, but the Norwegian Mapping Authority, Hydrographic
Service must be credited, since we are licensee of the data.

The use of the data is licensed through Creative Commons Attribution 4.0 international (CCBY 4.0). See also Terms of
use at Kartverket.no.

Please be careful not to abuse the API by excessive polling of data. Proper programming practice will be to cache
static data locally and limit the number of requests. Remember that you share this resource with all other users.

Users must also accept that the API is evolving, and that new elements or parameters might be added to existing
requests.

Example:
---------
# Standard library imports
from datetime import datetime

# Import water level API wrapper
from midgard.api import water_level_api

# Define file path of XML file received by water level API
file_path = "../examples/api/water_level_api.xml"

# Get instance of WaterLevelApi class 
api = water_level_api.WaterLevelApi(
        file_path=file_path,
        date_from=datetime(2025, 1, 1),
        date_to=datetime(2025, 1, 2),
        station="ANX",
)


from datetime import datetime
from midgard.api import water_level_api 
api = water_level_api.WaterLevelApi(
        file_path="test.xml",
        date_from=datetime(2025, 1, 1),
        date_to=datetime(2025, 1, 2),
        station="ANX",
)


"""

# Standard library imports
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Third party imports
import pycurl

# Midgard imports
from midgard import parsers
from midgard.dev import log
from midgard.math.unit import Unit
from midgard.files import files


# Available 3-digit tide gauge station names
STATION_DEF = ["ANX", "BGO", "BOO", "BRJ", "HFT", "HAR", "HEI", "HRO", "HVG", "KAB", "KSU", "LEH", "MSU", "MAY", 
               "NVK", "NYA", "OSC", "OSL", "RVK", "SBG", "SIE", "SOY", "SVG", "TRG", "TOS", "TRD", "TAZ", "VAW",
               "VIK", "AES"]

class WaterLevelApi(object):
    """Python wrapper around the Norwegian water level API (https://vannstand.kartverket.no/tideapi_en.html)
    
    """

    def __init__(
            self, 
            file_path: Union[str, Path], 
            date_from: datetime, 
            date_to: datetime,
            station: Optional[str] = None,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            datatype: Optional[str] = "all",
            reference_level: Optional[str] = "chart_datum", 
            interval: Union[int, str] = 10, 
            no_annual_tidal: Optional[bool] = False,
            url: Optional[str] = "https://vannstand.kartverket.no/tideapi.php",
    ) -> None:
        """Initialize water level API object

        Args:
            file_path:       Path to XML file that will be downloaded from API.
            date_from:       Starting date of data period
            date_to:         Ending date of data period
            station:         3-digit station name
            latitude:        Latitude of position in [deg] 
            longitude:       Longitude of position in [deg]
            datatype:        Choose type of water level data, which can be:
                                        'all'  - obs and pre data and in addition forecast if available
                                        'obs'  - observed/estimated water level
                                        'pre'  - tidal predictions
                                        'tab'  - tide table with high and low tides
            reference_level: Choose reference, which can be chart_datum, mean_sea_level or nn2000
            interval:        Data interval in [min], which can be either 10 or 60 min  
            no_annual_tidal: Annual tidal constituent SA is removed from the tidal predictions, if set to True                                     
            url:             URL to download from water level data
        """
        self.file_path = Path(file_path)
        self.download_xml(
                    date_from, 
                    date_to, 
                    station, 
                    latitude, 
                    longitude, 
                    datatype,
                    reference_level,
                    interval,
                    no_annual_tidal,
                    url,
        )
        self.data_available = self.file_path.exists()
        

    def as_dataset(self) -> "Dataset":
        """Return the water level data as Midgard Dataset
        
        Returns:
            Dataset where water level observation are stored with following fields in dependency of given data:
       
       |  Field                     | Type              | Description                                                 |
       | :------------------------- | :---------------- | :---------------------------------------------------------- |
       | flag                       | numpy.array       | Data flag of water level observation data (obs: observation,|
       |                            |                   | pre: prediction), which can also predicted tidal data       |
       | time                       | TimeTable         | Observation time given as TimeTable object                  |
       | water_level                | numpy.array       | Observed/estimated water level data in [m]                  |
       | water_level_predicted      | numpy.array       | Tidal prediction data in [m]                                |
       | water_level_weather_effect | numpy.array       | Weather effect [m]                                          |
            
        """
        p = parsers.parse_file(parser_name="water_level_api_xml",  file_path=self.file_path)
        return p.as_dataset()
  
        
    def as_dict(self) -> Dict[str, Any]:
        """Return the water level data as dictionary
        
        Returns:

            Dictionary with water level data saved in following keys:

        | Keys                       | Description                                                                    |
        | :------------------------- | :----------------------------------------------------------------------------- |
        | flag                       | Data flag of water level observation data (obs: observation, pre: prediction), |
        |                            | which can also predicted tidal data                                            |
        | time                       | Observation time                                                               |
        | water_level                | Observed/estimated water level data in [m]                                     |
        | water_level_predicted      | Tidal prediction data in [m]                                                   |
        | water_level_weather_effect | Weather effect [m]                                                             |
        """
        p = parsers.parse_file(parser_name="water_level_api_xml",  file_path=self.file_path)
        data = p.as_dict()
        for key in data.keys():
            if key in ["water_level", "water_level_predicted", "water_level_weather_effect"]:
                 data[key] = [ v * Unit.cm2m for v in data[key]]
        return data


    def download_xml(
            self, 
            date_from: datetime, 
            date_to: datetime,
            station: Optional[str] = None,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            datatype: Optional[str] = "all",
            reference_level: Optional[str] = "chart_datum", 
            interval: Union[int, str] = 10, 
            no_annual_tidal: Optional[bool] = False,
            url: Optional[str] = "https://vannstand.kartverket.no/tideapi.php",
    ) -> None:
        """Download XML file from url either for a given station or position (latitude/longitude)

        Args:
            date_from:       Starting date of data period
            date_to:         Ending date of data period
            station:         3-digit station name
            latitude:        Latitude of position in [deg] 
            longitude:       Longitude of position in [deg]
            datatype:        Choose type of water level data, which can be:
                                        'all'  - obs and pre data and in addition tidal forecast if available
                                        'obs'  - observed/estimated water level
                                        'pre'  - tidal predictions
                                        'tab'  - tide table with high and low tides
            reference_level: Choose reference, which can be chart_datum, mean_sea_level or nn2000
            interval:        Data interval in [min], which can be either 10 or 60 min    
            no_annual_tidal: Annual tidal constituent SA is removed from the tidal predictions, if set to True                                     
            url:             URL to download from water level data
        """
        reference_level_def = {
            "chart_datum": "cd",
            "mean_sea_level": "msl",
            "nn2000": "nn2000",         
        }
        
        if station:
            station = station.upper()

            if station not in STATION_DEF:
                raise ValueError(f"Unkown station name '{station}'. Following 3-digit station names can be chosen: {', '.join(STATION_DEF)}")

        if (date_from is None) or (date_to is None):
            raise ValueError("Following arguments has to be set: date_from, date_to")

        if (station is None) and (latitude is None):
            raise ValueError("Following arguments has to be set: station or latitude/longitude")
            
        if str(interval) not in ["10", "60"]:
            raise ValueError(f"Invalid interval {str(interval)}. Valid values are 10 or 60.")
                
        # Define arguments
        args = dict(
            fromtime=date_from.strftime("%Y-%m-%dT%H:%M"),
            totime=date_to.strftime("%Y-%m-%dT%H:%M"),
            datatype=datatype,
            uncertainty=0,
            refcode=reference_level_def[reference_level],
            place="",
            file="",
            lang="en",
            interval=str(interval),
            dst=0,  # summer time is not used
            tzone=0,  # UTC
        )
        
        if no_annual_tidal:
            args.update(
                flag="nosa",
            )

        if station:
            args.update(
                stationcode=station,
                tide_request="stationdata",
            )
        else:
            args.update(
                lat=latitude,
                lon=longitude,
                tide_request="locationdata",
            )

        # Define URL
        url=f"{url}?{'&'.join([f'{k}={v}' for k, v in args.items()])}"
        log.info(f"Downloading {url} to {self.file_path}")

        # Read data from API to file path
        with files.open(self.file_path, mode="wb") as fid:
            c = pycurl.Curl()
            c.setopt(c.URL, url)
            c.setopt(c.WRITEDATA, fid)
            try:
                c.perform()
            except pycurl.error as e:
                error_code, error_message = e.args
                raise ValueError(f"PycURL error (code {error_code}): {error_message}")
            finally:
                c.close()

