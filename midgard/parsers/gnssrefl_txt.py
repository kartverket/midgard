"""A parser for reading daily GNSSREFL reflector height results (output of 'gnssir' and 'subdaily' program)

TODO: subdaily produces several different formats. Not all of them are handled so far by this parser. At the moment
      only the final subdaily file with RHdot and interfrequency bias corrections can be read.

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
from midgard.files import files
from midgard.math.unit import Unit
from midgard.parsers import LineParser


@plugins.register
class GnssreflTxt(LineParser):
    """A parser for reading daily GNSSREFL reflector height results (output of 'gnssir' and 'subdaily' program)

    Following **data** can be available after reading the file:

    | Parameter                 | Description                                                                     |
    | :------------------------ | :------------------------------------------------------------------------------ |
    | amplitude                 | Amplitude                                                                       |
    | azimuth                   | Azimuth in [deg]                                                                |
    | elevation_max             | Maximal elevation [deg]                                                         |
    | elevation_min             | Minimal elevation [deg]                                                         |
    | elevation_rate            | Elevation rate [rad/hour]                                                       |
    | frequency                 | GNSS frequency identifier                                                       |
    | interfreq_bias_correction | Interfrequency bias correction in [m] (Note: Information added to data.)        |
    | number_of_observation     | Number of SNR observation                                                       |
    | peak2noise                | Peak to noise (maximal amplitude/noise)                                         |
    | reflector_height          | Reflector height in [m]                                                         |
    | reflector_height_with_    | Reflector height with interfrequency corrections in [m]                         |
    |  interfreq_corr           |                                                                                 |
    | reflector_height_with_    | Reflector height with time varying height corrections (RHDOT) in [m]            | 
    |  rhdot_corr               |                                                                                 |
    | refraction_model          | Defining used refraction model                                                  |
    |                           |    0: No refraction correction applied                                          |
    |                           |    1: Standard Bennett refraction correction                                    |
    |                           |    2: Standard Bennett refraction correction, time-varying                      |
    |                           |    3: Ulich refraction correction                                               |
    |                           |    4: Ulich refraction correction, time-varying                                 |
    |                           |    5: NITE refraction correction (Peng et al.)                                  |
    |                           |    6: MPF refraction correction, Wiliams and Nievinski                          |
    | rhdot_correction          | Time varying height corrections (RHDOT) in [m]                                  |
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

        self._parse_header()

        if self.meta["file_type"] == "gnssir":
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
                    "reflector_height",
                    "satellite",
                    "hour_utc",
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
                    "refraction_model",
                ),
                dtype=("f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8"),
            )

        elif self.meta["file_type"] == "subdaily":
            # % Results for moss calculated on 2024-10-27 19:57     
            # % gnssrefl, https://github.com/kristinemlarson 
            # % Traditional phase center corrections have NOT been applied 
            # % Reflector heights set to the L1-phase center are in column 25 
            # % (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22)   (23)      (24)    (25)
            # % year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS  RH with    RHdot     RH with  
            # %             m       hours   deg   v/v    deg   deg                1/-1       ratio    minute        1/0                   RHdotCorr  Corr m    IF Corr  m  
            return dict(
                comments="%",
                names=(
                    "year",
                    "doy",
                    "reflector_height",
                    "satellite",
                    "hour_utc",
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
                    "refraction_model",
                    "month",
                    "day",
                    "hour",
                    "minute",
                    "second",
                    "reflector_height_with_rhdot_corr",
                    "rhdot_correction",
                    "reflector_height_with_interfreq_corr",
                ),
                dtype=("f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", 
                       "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8"),
            )
          


    def _parse_header(self) -> None:
        """Parse header to determine the file type

        The output file can be either generated by 'gnssir' or 'subdaily' program. 'subdaily' output files includes
        more columns than 'gnssir' files.
        """
        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            
            for line in fid: 
                
                if line.startswith("%"):
                    if line.startswith("% year"):
                        if "RHdot" in line:
                            self.meta["file_type"] = "subdaily"
                        else:
                            self.meta["file_type"] = "gnssir"
                else:
                    break

    #
    # SETUP CALCULATION
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        """
        return [
            self._add_time_field,
            self._add_interfreq_bias_correction_field,
        ]

    def _add_time_field(self) -> None:
        """Add time parameter to data and delete 'year', 'doy', 'hour_utc' and 'mjd'
        """
        if self.meta["file_type"] == "gnssir":
            self.data["time"] = [ datetime.strptime(f"{int(yy)}-{int(dd)}", "%Y-%j") + timedelta(hours=hh) for yy,dd,hh in zip(self.data["year"], self.data["doy"], self.data["hour_utc"]) ]
        elif self.meta["file_type"] == "subdaily":
            self.data["time"] = [ datetime.strptime(f"{int(yy)}-{int(dd)}-{int(hh)}-{int(mm)}-{int(ss)}", "%Y-%j-%H-%M-%S") for yy,dd,hh,mm,ss in zip(self.data["year"], self.data["doy"], self.data["hour"], self.data["minute"], self.data["second"]) ]

        for key in ["year", "doy", "hour_utc", "hour", "minute", "mjd", "second"]:
            if key in self.data.keys():
                del self.data[key]
                
    def _add_interfreq_bias_correction_field(self) -> None:
        """Add interfrequency bias correction field to data
        """
        if "reflector_height_with_interfreq_corr" in self.data.keys():
            self.data["interfreq_bias_correction"] = self.data["reflector_height_with_interfreq_corr"] - self.data["reflector_height_with_rhdot_corr"] 


    #
    # DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            Midgard Dataset where data can be stored with following fields:
   
           | Field                     | Type          | Description                                                  |
           | :------------------------ | :------------ | :----------------------------------------------------------- |
           | amplitude                 | numpy.array   | Amplitude                                                    |
           | azimuth                   | numpy.array   | Azimuth in [rad]                                             |
           | elevation_max             | numpy.array   | Maximal elevation [rad]                                      |
           | elevation_min             | numpy.array   | Minimal elevation [rad]                                      |
           | elevation_rate            | numpy.array   | Elevation rate [rad/s]                                       |        
           | frequency                 | numpy.array   | GNSS frequency identifier                                    |
           | interfreq_bias_correction | numpy.array   | Interfrequency bias correction in [m]                        |
           | number_of_observation     | numpy.array   | Number of SNR observation                                    |
           | peak2noise                | numpy.array   | Peak to noise (maximal amplitude/noise)                      |
           | reflector_height          | numpy.array   | Reflector height with correction applied in [m]              |
           | refraction_model          | numpy.array   | Defining used refraction model:                              |
           |                           |               |    0: No refraction correction applied                       |
           |                           |               |    1: Standard Bennett refraction correction                 |
           |                           |               |    2: Standard Bennett refraction correction, time-varying   |
           |                           |               |    3: Ulich refraction correction                            |
           |                           |               |    4: Ulich refraction correction, time-varying              |
           |                           |               |    5: NITE refraction correction (Peng et al.)               |
           |                           |               |    6: MPF refraction correction, Wiliams and Nievinski       |
           | rhdot_correction          | numpy.array   | Time varying height corrections (RHDOT) in [m]               |
           | rising_satellite          | numpy.array   | Rising satellite if True and setting satellite if False      |
           | satellite                 | numpy.array   | Satellite number                                             |
           | satellite_arc_length      | numpy.array   | Satellite arc length in [s]                                  |
           | system                    | numpy.ndarray | GNSS identifier                                              |
           | time                      | Time          | Time                                                         |
               
        """
        
        freq_def = {
            1: "L1",     # G  1575.42
            2: "L2",     # G  1227.60
            5: "L5",     # G  1176.45
            20: "L2C",   # G  1227.60
            101: "G1",   # R
            102: "G2",   # R
            201: "E1",   # E  1575.420
            205: "E5a",  # E  1176.450
            206: "E6",   # E  1278.70
            207: "E5b",  # E  1207.140
            208: "E5",   # E  1191.795   
            301: "B1C",  # C  1575.42
            302: "B1",   # C  1561.098 
            305: "B2a",  # C  1176.45
            306: "B3",   # C  1268.52
            307: "B2b",  # C  1207.14  B2 BDS-2 signal/B2b BDS-3 signal
            308: "B2",   # C  1191.795 B2a+B2b BDS-3 signal
        }
            
        float_fields = {
                "amplitude": None,
                "azimuth": "radian",
                "delt": "minute",
                "elevation_rate": "radian/second",
                "elevation_max": "radian",
                "elevation_min": "radian",
                "interfreq_bias_correction": "meter",
                "number_of_observation": None,
                "peak2noise": None, 
                "reflector_height": "meter",
                "reflector_height_with_interfreq_corr": "meter", # Not added to dataset, but unit information is needed.
                "reflector_height_with_rhdot_corr": "meter", # Not added to dataset, but unit information is needed.
                "refraction_model": None,
                "rhdot_correction": "meter",
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
            # Skip fields:
            if field in ["reflector_height_with_interfreq_corr", "reflector_height_with_rhdot_corr"]:
                continue
                
            if field not in self.data.keys():
                #log.warn(f"Field '{field}' does not exist in file {self.meta['__data_path__']}.")
                continue
            
            if field in ["azimuth", "elevation_min", "elevation_max"]:
                value = self.data[field] * Unit.deg2rad
            elif field == "elevation_rate":
                value = self.data[field] * Unit.hour2second
            elif field == "reflector_height": # Change field values depending on which corrections are available
                if "reflector_height_with_interfreq_corr" in self.data.keys():
                    value = self.data["reflector_height_with_interfreq_corr"]
                elif "reflector_height_with_rhdot_corr" in self.data.keys():
                    value = self.data["reflector_height_with_rhdot_corr"] 
            elif field == "satellite_arc_length":
                value = self.data[field] * Unit.minute2second
            else:
                value = self.data[field]
            unit = "" if float_fields[field] is None else float_fields[field]
            
            dset.add_float(name=field, val=value, unit=unit, write_level="operational")
        
        return dset


        
