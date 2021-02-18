"""A parser for reading COST format for ground-based GNSS delay and water vapour data

Example:
--------

    from midgard import parsers
    
    # Parse data
    parser = parsers.parse_file(parser_name="cost", file_path=file_path)
    
    # Get Dataset with parsed data
    dset = parser.as_dataset()

Description:
------------

Reads data from files in the COST file format 2.2a (see :cite:`cost`).

"""

# Standard library imports
from collections import namedtuple
from datetime import datetime
import itertools
from typing import Any, Callable, Dict, Iterable, List

# External library imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.dev import plugins
from midgard.dev import log
from midgard.math.unit import Unit
from midgard.parsers import ChainParser, ParserDef


UnitField = namedtuple(
    "UnitField", ["from_", "to_"]
)


UnitField.__new__.__defaults__ = (None,) * len(UnitField._fields)
UnitField.__doc__ = """A convenience class for defining a COST units of fields

    Args:
        from (str):              Original field unit
        to (str):                Destination field unit
    """

UNIT_DEF = {
  "gradients_ew":  UnitField("millimeter", "meter"),
  "gradients_ns":  UnitField("millimeter", "meter"),
  "height_geoid": UnitField("meter", "meter"),
  "humidity":  UnitField("", ""),
  "iwv":  UnitField("kilogram/meter**2", "kilogram/meter**2"),
  "pressure":  UnitField("hectopascal", "pascal"),
  "sigma_gradients_ew":  UnitField("millimeter", "meter"),
  "sigma_gradients_ns":  UnitField("millimeter", "meter"),
  "sigma_ztd": UnitField("millimeter", "meter"),
  #TODO "tec":  UnitField("tecu", "tecu"),
  "temperature":  UnitField("kelvin", "kelvin"),
  "ztd": UnitField("millimeter", "meter"),
  "zwd": UnitField("millimeter", "meter"),
}
        


@plugins.register
class CostParser(ChainParser):
    """A parser for reading COST datan file

    The parser reads ground-based GNSS delay and water vapour data in COST format version 2.2a.

    Attributes:
        data (Dict):                  The (observation) data read from file.
        data_available (Boolean):     Indicator of whether data are available.
        file_encoding (String):       Encoding of the datafile.
        file_path (Path):             Path to the datafile that will be read.
        meta (Dict):                  Metainformation read from file.
        parser_name (String):         Name of the parser (as needed to call parsers.parse_...).
    """


    #
    # PARSERS
    #
    def setup_parser(self) -> Iterable[ParserDef]:
        """Parsers defined for reading COST observation file line by line.

           First the RINEX header information are read and afterwards the RINEX observation.
        """
        # Parser for COST observation blocks

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+
        # ----------------------------------------------------------------------------------------------------
        # COST-716 V2.2a           E-GVAP                   OPER                     
        # AASC XXXXXXXXX           Aas [NO]
        # TRIMBLE NETR9            TRM57971.00 TZGD    
        #    59.660300   10.781700     133.610      94.578       0.000
        # 01-FEB-2021 03:00:00     01-FEB-2021 05:41:27
        # NGA1                     BERNESE V5.2             CODULT                   NONE                
        #    15   60  360
        # 00000075
        #    4
        #   3  0  0 FFFFFFFF 2287.9    2.1   -9.9   -9.9   -9.9   -9.9   -9.9 999.99 999.99  -9.99  -9.99 -99.999
        #    0
        #   3 15  0 FFFFFFFF 2289.3    2.2   -9.9   -9.9   -9.9   -9.9   -9.9 999.99 999.99  -9.99  -9.99 -99.999
        #    0
        #   3 30  0 FFFFFFFF 2289.3    2.3   -9.9   -9.9   -9.9   -9.9   -9.9 999.99 999.99  -9.99  -9.99 -99.999
        #    0
        #   3 45  0 FFFFFFFF 2288.9    2.5   -9.9   -9.9   -9.9   -9.9   -9.9 999.99 999.99  -9.99  -9.99 -99.999
        #    0
        # ----------------------------------------------------------------------------------------------------
        obs_parser = ParserDef(
            end_marker=lambda _l, _ln, next_line: next_line.startswith("COST-716"),
            label=lambda _l, line_num: line_num if line_num <= 9 else "observations",
            skip_line=lambda line: line.startswith("-----------------"),
            end_callback=self._copy_cache_to_obs,
            parser_def={
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                # COST-716 V2.2a           E-GVAP                   OPER      
                1: {
                    "parser": self._parse_string,
                    "strip": " \t\n",  # Remove whitespace, tabs '\t' and newline '\n' leading and trailing characters from line.
                    "fields": {
                        "format": (0, 8),
                        "version": (8, 25),
                        "project": (25, 50),
                        "file_status": (50, 70),
                    },
                },   
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                # AASC XXXXXXXXX           Aas [NO]
                2: {
                    "parser": self._parse_string,
                    "strip": " \t\n",
                    "fields": {
                        "station_id": (0, 4),
                        "domes_number": (4, 20),
                        "country": (20, 85),
                    },
                },
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                # TRIMBLE NETR9            TRM57971.00 TZGD 
                3: {
                    "parser": self._parse_string,
                    "strip": " \t\n",
                    "fields": {
                        "receiver": (0, 20),
                        "antenna": (20, 45),
                    },
                },
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                #    59.660300   10.781700     133.610      94.578       0.000
                4: {
                    "parser": self._parse_float,
                    "strip": " \t\n",
                    "fields": {
                        "latitude": (0, 12),
                        "longitude": (12, 24),
                        "height_ellipsoid": (24, 36),
                        "height_geoid": (36, 48),
                        "height_marker": (48, 60),
                    },
                },
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                # 01-FEB-2021 03:00:00     01-FEB-2021 05:41:27
                5: {
                    "parser": self._parse_date,
                    "strip": " \t\n",
                    "fields": {
                        "date_data": (0, 20),
                        "date_processing": (20, 45),
                    },
                },
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                # NGA1                     BERNESE V5.2             CODULT                   NONE   
                6: {
                    "parser": self._parse_string,
                    "strip": " \t\n",
                    "fields": {
                        "analysis_center": (0, 20),
                        "software": (20, 45),
                        "orbit_type": (45, 70),
                        "met_data": (70, 95),
                    },
                },
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                #    15   60  360
                7: {
                    "parser": self._parse_integer,
                    "strip": " \t\n",
                    "fields": {
                        "time_increment": (0, 5),
                        "update_interval": (5, 10),
                        "batch_length": (10, 15),
                    },
                },
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                # 00000075
                8: {
                    "parser": self._parse_integer, #TODO bits!!!
                    "strip": " \t\n",
                    "fields": {
                        "product_confidence": (0, 8),
                    },
                },
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----
                #    4
                9: {
                    "parser": self._parse_integer,
                    "strip": " \t\n",
                    "fields": {
                        "num_data_samples": (0, 4),
                    },
                },
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0---
                #   3  0  0 FFFFFFFF 2287.9    2.1   -9.9   -9.9   -9.9   -9.9   -9.9 999.99 999.99  -9.99  -9.99 -99.999
                #    0
                # TODO: Parsing of slant samples is not handled so far!!!
                "observations": {
                    "parser": self._parse_observation,
                    "strip": " \t\n",
                    "fields": {
                        "hour": (0, 3),
                        "minute": (3, 6),
                        "second": (6, 9),
                        "product_confidence": (9, 18),
                        "ztd": (18, 25),
                        "sigma_ztd": (25, 32),
                        "zwd": (32, 39),
                        "iwv": (39, 46),
                        "pressure": (46, 53),
                        "temperature": (53, 60),
                        "humidity": (60, 67),
                        "gradients_ns": (67, 74),
                        "gradients_ew": (74, 81),
                        "sigma_gradients_ns": (81, 88),
                        "sigma_gradients_ew": (88, 95),
                        "tec": (95, 103),
                    },
                },
            },
        )

        return itertools.chain(itertools.repeat(obs_parser))

    #
    # HEADER PARSERS
    #
    def _parse_date(self, line: Dict[str, str], cache: Dict[str, Any]) -> None:
        """Parse date entries of COST header to cache.
        """
        # Example: 01-FEB-2021 03:00:00
        cache.update({k: datetime.strptime(v, "%d-%b-%Y %H:%M:%S") for k, v in line.items()})
        
    def _parse_float(self, line: Dict[str, str], cache: Dict[str, Any]) -> None:
        """Parse float entries of COST header to cache.
        """
        cache.update({k: float(v) for k, v in line.items()})

    def _parse_integer(self, line: Dict[str, str], cache: Dict[str, Any]) -> None:
        """Parse integer entries of COST header to cache.
        """
        cache.update({k: int(v) for k, v in line.items()})

    def _parse_string(self, line: Dict[str, str], cache: Dict[str, Any]) -> None:
        """Parse string entries of COST header to cache.
        """
        cache.update({k: v.strip() for k, v in line.items()})


    #
    # OBSERVATION PARSERS
    def _parse_observation(self, line: Dict[str, str], cache: Dict[str, Any]) -> None:
        """Parse observations of COST records
        """
        
        # Skip slant sample lines
        if not line["hour"]:
            if float(line["minute"]) > 0:
                log.debug("Parsing of slant sample data is not implemented.")
            return
        
        if line["hour"][0].isalpha(): 
            return

        # Save data in cache
        for key, value in line.items():
            value = float(value) if value.replace('.','').replace('-','').isnumeric() else value
            if key in UNIT_DEF.keys():
                value = value * Unit(UNIT_DEF[key].from_, UNIT_DEF[key].to_)
                
            cache.setdefault(f"data_{key}", list()).append(value)
        
        cache.setdefault(f"data_time", list()).append(datetime(
                cache["date_data"].year, 
                cache["date_data"].month, 
                cache["date_data"].day,
                int(line["hour"]),
                int(line["minute"]),
                int(line["second"]),
        ))
        
    def _copy_cache_to_obs(self, cache: Dict[str, Any]) -> None:
        """Copy cached data in self.data and self.meta data structure
        
        This step is done for each station observation record.
        """
        # Nothing to save
        if len(cache) == 1:
            return
        
        # Save data and meta data stationwise
        station = cache["station_id"].lower()
        self.meta.setdefault(station, dict())
        self.data.setdefault(station, dict())
        del cache["station_id"]
        
        for key, value in cache.items():
            if key.startswith("data"):
                key = key.replace("data_", "")
                self.data[station][key] = value             
            else:
                self.meta[station][key] = value

        del self.meta[station]["line_num"]


    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        """
        return [
        ]


    #
    # WRITE DATA
    #
    def as_dataset(self) -> "Dataset":
        """Store COST data in a dataset

        Returns:
            Midgard Dataset where COST observation are stored with following fields:

       |  Field                   | Type           | Description                                                      |
       |--------------------------|----------------|------------------------------------------------------------------|
       | gradients_ew             | numpy.ndarray  | Gradients in East/West in [m]                                    |
       | gradients_ns             | numpy.ndarray  | Gradients in North/South in [m]                                  |
       | humidity                 | numpy.ndarray  | Relative humidity for IWV in [%]                                 |
       | iwv                      | numpy.ndarray  | Integrated Water Vapour (IWV) in [kg/m²]                         |
       | pressure                 | numpy.ndarray  | Pressure used for ZWD in [Pa]                                    |
       | product_confidence       | numpy.ndarray  | Product Confidence Data as bit flags describing the quality of   |
       |                          |                | the data sample                                                  |
       | sigma_gradients_ew       | numpy.ndarray  | Standard deviation of gradients in East/West in [m]              |
       | sigma_gradients_ns       | numpy.ndarray  | Standard deviation of gradients in North/South in [m]            |
       | sigma_ztd                | numpy.ndarray  | Standard devivation of ZTD in [m]                                |
       | station                  | numpy.ndarray  | Station name                                                     |
       | temperature              | numpy.ndarray  | Temperature used for IWV in [Kelvin]                             |
       | time                     | TimeTable      | Observation time given as TimeTable object                       |
       | ztd                      | numpy.ndarray  | Zenith Total Delay (ZTD) in [m]                                  |
       | zwd                      | numpy.ndarray  | Zenith Wet Delay (ZWD) in [m]                                    |




            and following Dataset `meta` data, which are saved for each station separately:

       |  Entry              | Type  | Description                                                                    |
       |---------------------|-------|--------------------------------------------------------------------------------|
       | analysis_center     | str   | Analysis center name                                                           |
       | antenna             | str   | Antenna type with radome                                                       |
       | batch_length        | str   | Total length of batch time                                                     |
       | country             | str   | Country name of station                                                        |
       | date_data           | str   | Date of processed observation                                                  |
       | date_processing     | str   | Date of processing started                                                     |
       | domes_number        | str   | Domes number                                                                   |
       | file_status         | str   | File status (OPER, DEMO, TEST)                                                 |
       | format              | str   | Format name (COST-716)                                                         |
       | height_ellipsoid    | str   | Antenna reference point (ARP) height above ellipsoid                           |
       | height_geoid        | str   | Antenna reference point (ARP) height above geoid                               |
       | height_marker       | str   | Antenna reference point (ARP) height above benchmark (marker)                  |
       | latitude            | str   | Station latitude in [degree]                                                   |
       | longitude           | str   | Station longitude in [degree]                                                  |
       | met_data            | str   | Source of meteorologic data                                                    |
       | num_data_samples    | str   | Number of data samples                                                         |
       | orbit_type          | str   | Orbit type                                                                     |
       | product_confidence  | str   | Product confidence data summary of overall data quality                        |
       | project             | str   | Project name (e.g. E-GVAP)                                                     |
       | receiver            | str   | Receiver type                                                                  |
       | method              | str   | Processing method                                                              |
       | time_increment      | str   | Nominal time increment between data samples                                    |
       | update_interval     | str   | batch updating interval                                                        |
       | version             | str   | COST format version                                                            |
       
        """
        skip_fields = ["hour", "minute", "second"]
        text_fields = ["product_confidence"]
        data_sum = dict()
        
        # Loop over all stations for preparing data to save in dataset
        for station, data in self.data.items():
            num_obs = len(data["time"])
            data_sum.setdefault("text", dict()).setdefault("station", list()).extend([station for v in range(0, num_obs)])
            
            # Add data 
            for field in data.keys():
                if field in skip_fields:
                    continue
                
                if field in text_fields:
                    data_sum["text"].setdefault(field, list()).extend(data[field])
                elif field == "time":
                    data_sum.setdefault("time", dict()).setdefault(field, list()).extend(data[field])
                else:
                    data_sum.setdefault("float", dict()).setdefault(field, list()).extend(data[field])
                    
            # Add site position to data
            num_obs = len(data["time"])
            for field in ["longitude", "latitude", "height_ellipsoid", "height_geoid"]:
                data_sum.setdefault(
                        "float", 
                        dict()).setdefault(field, list(),
                ).extend([self.meta[station][field]] * num_obs)

            
     
        # Generate dataset
        dset = dataset.Dataset(num_obs=len(data_sum["text"]["station"]))
        dset.meta = self.meta
        skip_fields = ["latitude", "longitude", "height_ellipsoid"]
        
        for type_ in data_sum.keys():    
            for field, val in data_sum[type_].items():
                if type_ == "text":
                    dset.add_text(field, val=val)
                elif type_ == "time":
                    dset.add_time(field, val=val, scale="utc", fmt="datetime")
                elif type_ == "float":
                    if field in skip_fields:
                        continue
                    unit = UNIT_DEF[field].to_ if field in UNIT_DEF.keys() else ""
                    dset.add_float(field, val=val, unit=unit)
                    
        # Add site_pos to dataset
        dset.add_position(
                "site_pos", 
                time=dset.time, 
                system="llh", 
                val=np.stack((
                        np.array(data_sum["float"]["latitude"]) * Unit.deg2rad,
                        np.array(data_sum["float"]["longitude"]) * Unit.deg2rad, 
                        data_sum["float"]["height_ellipsoid"]), 
                        axis=1,
                    )
        )
        
        return dset
