## midgard.api.transformation_api
Python wrapper around the Transformation API

**Description:**

Transformation of coordinates can be done by using Transformation API from/to different reference systems and 
projection. Available Transformation API projections can be shown by using function 'projections'.

**Example:**
from midgard.api import transformation_api

# Get instance of TransformationApi class on default URL
api = transformation_api.TransformationApi()

# Get instance of TransformationApi class based on defined URL
api = transformation_api.TransformationApi(url="https://ws.geonorge.no/transformering/v1")

# Transform from ITRF2014 to ETRS89
pos = api.transform(2169481.21111251,  627616.7736756 , 5944952.10084486, 2021.0, 4936, 7789)



### **TransformationApi**

Full name: `midgard.api.transformation_api.TransformationApi`

Signature: `(url: str = 'https://ws.geonorge.no/transformering/v1', proxy: str | None = None) -> None`

A wrapper around the transformation API

https://ws.geonorge.no/transformering/v1/transformer?x=1&y=60&z=0&t=2018&fra=4258&til=4258


## midgard.api.water_level_api
Python wrapper around the Norwegian water level API (https://vannstand.kartverket.no/tideapi_en.html)

**Description:**
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

**Terms of Use:**
The API is open for everybody and does not require registration, but the Norwegian Mapping Authority, Hydrographic
Service must be credited, since we are licensee of the data.

The use of the data is licensed through Creative Commons Attribution 4.0 international (CCBY 4.0). See also Terms of
use at Kartverket.no.

Please be careful not to abuse the API by excessive polling of data. Proper programming practice will be to cache
static data locally and limit the number of requests. Remember that you share this resource with all other users.

Users must also accept that the API is evolving, and that new elements or parameters might be added to existing
requests.

**Example:**
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




### STATION_DEF (list)
`STATION_DEF = ['ANX', 'BGO', 'BOH', 'BOO', 'BRJ', 'HFT', 'HAR', 'HEI', 'HRO', 'HVG', 'KAB', 'KSU', 'LEH', 'MSU', 'MAY', 'NVK', 'NYA', 'OSC', 'OSL', 'RVK', 'SBG', 'SIE', 'SOY', 'SVG', 'TRG', 'TOS', 'TRD', 'TAZ', 'VAW', 'VIK', 'AES']`


### **WaterLevelApi**

Full name: `midgard.api.water_level_api.WaterLevelApi`

Signature: `(file_path: str | pathlib.Path, date_from: datetime.datetime, date_to: datetime.datetime, station: str | None = None, latitude: float | None = None, longitude: float | None = None, datatype: str | None = 'all', reference_level: str | None = 'chart_datum', interval: int | str = 10, no_annual_tidal: bool | None = False, url: str | None = 'https://vannstand.kartverket.no/tideapi.php') -> None`

Python wrapper around the Norwegian water level API (https://vannstand.kartverket.no/tideapi_en.html)

