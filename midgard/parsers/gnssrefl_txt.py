"""A parser for reading daily GNSSREFL reflector height results (output of 'gnssir' program)

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnssrefl_txt', file_path='218.txt')
    data = p.as_dict()

Description:
------------

Reads data from daily GNSSREFL files given as output from program 'gnssir'

"""
# Standard library imports
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List

# External library imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.dev import log, plugins
from midgard.math.unit import Unit
from midgard.parsers import LineParser


@plugins.register
class GnssreflTxt(LineParser):
    """A parser for reading daily GNSSREFL reflector height results (output of 'gnssir' program)

    Following **data** are available after reading the file:

    | Parameter                 | Description                                                                     |
    | :------------------------ | :------------------------------------------------------------------------------ |
    | amplitude                 | Amplitude                                                                       |
    | azimuth                   | Azimuth in [deg]                                                                |
    | elevation_max             | Maximal elevation [deg]                                                         |
    | elevation_min             | Minimal elevation [deg]                                                         |
    | elevation_rate            | Elevation rate [rad/hour]                                                       |
    | frequency                 | GNSS frequency identifier                                                       |
    | number_of_observation     | Number of SNR observation                                                       |
    | peak2noise                | Peak to noise (maximal amplitude/noise)                                         |
    | reflector_height          | Reflector height in [m]                                                         |
    | refraction_model          | Defining used refraction model                                                  |
    |                           |    0: No refraction correction applied                                          |
    |                           |    1: Standard Bennett refraction correction                                    |
    |                           |    2: Standard Bennett refraction correction, time-varying                      |
    |                           |    3: Ulich refraction correction                                               |
    |                           |    4: Ulich refraction correction, time-varying                                 |
    |                           |    5: NITE refraction correction (Peng et al.)                                  |
    |                           |    6: MPF refraction correction, Wiliams and Nievinski                          |
    | rising_satellite          | Rising satellite is set to 1 and setting satellite to -1                        | 
    | satellite                 | Satellite number                                                                |
    | satellite_arc_length      | Satellite arc length in [min]                                                   |
    | time                      | Time as datetime object                                                         |

    and **meta**-data:

    | Key                  | Description                                                                          |
    | :------------------- | :----------------------------------------------------------------------------------- |
    | __data_path__        | File path                                                                            |
    | __parser_name__      | Parser name                                                                          |

    """

    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

        # % gnssrefl, https://github.com/kristinemlarson 
        # % Phase Center corrections have NOT been applied 
        # % year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD   refr-appl
        # % (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16)   (17)
        # %             m        hrs    deg   v/v    deg    deg  values            hrs               min         1 is yes  
        #  2023 365  9.249   2 10.325  57.51  30.16   5.05   9.97   48   1  1  0.40159   3.15   15.67 60309.430197 1 
        #  2023 365  8.800   5 16.939 114.08  23.77   5.11   9.90   39   1  1  0.33263   3.00   12.67 60309.705787 1 
        #  2023 365  8.355   6 13.167 114.47  33.06   5.01   9.91   39   1  1  0.32283   3.15   12.67 60309.548600 1 
        #----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0
        return dict(
            comments="%",
            names=(
                "year",
                "doy",
                "refraction_model",
                "satellite",
                "hour",
                "azimuth",
                "amplitude",
                "elevation_min",
                "elevation_max",
                "number_of_observation",
                "frequency",
                "rising_satellite",
                "elevation_rate",
                "peak2noise",
                "satellite_arc_length",
                "mjd",
                "use_gpt2",
            ),
            dtype=("f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8"),
        )

    #
    # SETUP CALCULATION
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        """
        return [self._add_time_field]

    def _add_time_field(self) -> None:
        """Add time parameter to data and delete 'year', 'doy', 'hour' and 'mjd'
        """
        self.data["time"] = [ datetime.strptime(f"{int(yy)}-{int(dd)}", "%Y-%j") + timedelta(hours=hh) for yy,dd,hh in zip(self.data["year"], self.data["doy"], self.data["hour"]) ]
        
        for key in ["year", "doy", "hour", "mjd"]:
            del self.data[key]


    #
    # DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            Midgard Dataset where timeseries data are stored with following fields:
   
           | Field                 | Type              | Description                                                  |
           | :-------------------- | :---------------- | :----------------------------------------------------------- |
           | amplitude             | numpy.array       | Amplitude                                                    |
           | azimuth               | numpy.array       | Azimuth in [rad]                                             |
           | elevation_max         | numpy.array       | Maximal elevation [rad]                                      |
           | elevation_min         | numpy.array       | Minimal elevation [rad]                                      |
           | elevation_rate        | numpy.array       | Elevation rate [rad/s]                                       |        
           | frequency             | numpy.array       | GNSS frequency identifier                                    |
           | number_of_observation | numpy.array       | Number of SNR observation                                    |
           | peak2noise            | numpy.array       | Peak to noise (maximal amplitude/noise)                      |
           | reflector_height      | numpy.array       | Reflector height in [m]                                      |
           | refraction_model      | numpy.array       | Defining used refraction model:                              |
           |                       |                   |    0: No refraction correction applied                       |
           |                       |                   |    1: Standard Bennett refraction correction                 |
           |                       |                   |    2: Standard Bennett refraction correction, time-varying   |
           |                       |                   |    3: Ulich refraction correction                            |
           |                       |                   |    4: Ulich refraction correction, time-varying              |
           |                       |                   |    5: NITE refraction correction (Peng et al.)               |
           |                       |                   |    6: MPF refraction correction, Wiliams and Nievinski       |
           | rising_satellite      | numpy.array       | Rising satellite if True and setting satellite if False      |
           | satellite             | numpy.array       | Satellite number                                             |
           | satellite_arc_length  | numpy.array       | Satellite arc length in [s]                                  |
           | time                  | Time              | Time                                                         |
               
        """
        
        freq_def = {
            1: "L1",     # G
            2: "L2",     # G
            5: "L5",     # G
            20: "L2C",   # G
            101: "L1",   # R
            102: "L2",   # R
            201: "E1",   # E 
            205: "E5a",  # E
            206: "E6",   # E
            207: "E5b",  # E
            208: "E5",   # E
            302: "B1_2", # C
            306: "B3",   # C
            307: "B2b",  # C
        }

        float_fields = {
                "amplitude": None,
                "azimuth": "radian",
                "delt": "minute",
                "elevation_rate": "radian/second",
                "elevation_max": "radian",
                "elevation_min": "radian",
                "number_of_values": None,
                "peak2noise": None, 
                "use_gpt2": None,
                "reflector_height": "meter",
                "refraction_model": None,
                "satellite_arc_length": "second",           
        }

        # Initialize dataset
        dset = dataset.Dataset()
        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(self.data["time"])

        # Add text fields
        satellite = list()
        system = list()
        for sat in self.data["satellite"]:
            if sat >= 1 and sat < 100: # GPS satellites
                system.append("G")
                satellite.append("G" + str(int(sat)).zfill(2))
            elif sat >= 101 and sat < 200: # GLONASS satellites
                system.append("R")
                satellite.append("R" + str(int(sat))[1:3])
            elif sat >= 201 and sat < 300: # Galileo satellites
                system.append("E")
                satellite.append("E" + str(int(sat))[1:3])
            elif sat >= 301 and sat < 400: # BeiDou satellites
                system.append("C")
                satellite.append("C" + str(int(sat))[1:3])
            else:
                log.fatal("GNSSREFL satellite number {sat} is not defined. Valid satellite numbers are between [1-399].")

        dset.add_text(
                name="system", 
                val=system, 
                write_level="operational",
        )

        dset.add_text(
                name="satellite", 
                val=satellite, 
                write_level="operational",
        )

        dset.add_text(
                name="frequency", 
                val=[freq_def[v] for v in self.data["frequency"]], 
                write_level="operational",
        ) 
        
        # Add time field
        dset.add_time(
                name="time", 
                val=self.data["time"], 
                scale="utc", 
                fmt="datetime", 
                write_level="operational",
        )
        
        # Add boolean field
        dset.add_bool(
                name="rising_satellite",
                val=[ True if v == 1 else False for v in self.data["rising_satellite"]],
                write_level="operational",
        )
        
        # Add float fields
        for field in float_fields.keys():
            if field not in self.data.keys():
                log.warn(f"Field '{field}' does not exist in file {self.meta['__data_path__']}.")
                continue
            
            if field in ["azimuth", "elevation_min", "elevation_max"]:
                value = self.data[field] * Unit.deg2rad
            elif field == "elevation_rate":
                value = self.data[field] * Unit.hour2second
            elif field == "satellite_arc_length":
                value = self.data[field] * Unit.minute2second
            else:
                value = self.data[field]
            unit = "" if float_fields[field] is None else float_fields[field]
            
            dset.add_float(name=field, val=value, unit=unit, write_level="operational")
        
        return dset


        
