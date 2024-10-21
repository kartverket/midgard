"""A parser for reading GNSSREFL SNR files

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnssrefl_snr', file_path='ande2740.24.snr66')
    data = p.as_dict()

Description:
------------

Reads data from files in GNSSREFL SNR format

"""
# Standard library imports
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List

# External library imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.dev import log
from midgard.dev import plugins
from midgard.parsers import LineParser


@plugins.register
class GnssreflSnr(LineParser):
    """A parser for reading GNSSREFL SNR files
    
    Following **data** are available after reading the file:

    | Parameter                 | Description                                                                     |
    | :------------------------ | :------------------------------------------------------------------------------ |
    | azimuth                   | Azimuth in [deg]                                                                |
    | elevation                 | Elevation in [deg]                                                              |
    | elevation_rate            | Elevation angle rate of change [deg/s]                                          |
    | seconds_of_day            | Seconds of day (GPS time)                                                       |
    | satellite                 | Satellite number                                                                |
    | S1                        | SNR observation data on L1                                                      |
    | S2                        | SNR observation data on L2                                                      |
    | S5                        | SNR observation data on L5                                                      |
    | S6                        | SNR observation data on L6                                                      |
    | S7                        | SNR observation data on L7                                                      |   
    | S8                        | SNR observation data on L8                                                      | 
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

        # 314   10.7907  345.5731       0.0 -0.004728  32.12   0.00  41.75   0.00  41.81   0.00
        # 326   27.0452  315.3763       0.0  0.004863  45.62   0.00  47.56   0.00   0.00   0.00
        # 327   24.5786   78.4961       0.0 -0.006435  43.06   0.00  46.12   0.00   0.00   0.00
        # ----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7-----
        return dict(
            names=(
                "satellite",
                "elevation",
                "azimuth",
                "seconds_of_day",
                "elevation_rate",
                "S6",
                "S1",
                "S2",
                "S5",
                "S7",
                "S8",
            ),
            dtype=("f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8"),
        )

    #
    # SETUP CALCULATION
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        """
        return [self._add_time_field]

    def _add_time_field(self) -> None:
        """Add time parameter based on file name and seconds of day
        """
        
        # Extract date based on file name
        doy, year = self.file_path.stem.split(".")
        doy = doy[4:7]
        
        # 1980 is the border to decide if year should in 1900 or 2000 century. 
        year = f"19{year}" if int(year) > 80 else f"20{year }"
        
        time = datetime.strptime(f"{year}-{doy}", "%Y-%j")
        self.data["time"] = [ time + timedelta(seconds=s) for s in self.data["seconds_of_day"] ]


    #
    # DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            Midgard Dataset where timeseries data are stored with following fields:

           | Field                 | Type              | Description                                                  |
           | :-------------------- | :---------------- | :----------------------------------------------------------- |
           | azimuth               | numpy.array       | Azimuth in [deg]                                             |
           | elevation             | numpy.array       | Elevation in [deg]                                           |
           | elevation_rate        | numpy.array       | Elevation angle rate of change [deg/s]                       |
           | seconds_of_day        | numpy.array       | Seconds of day (GPS time)                                    |
           | satellite             | numpy.array       | Satellite number                                             |
           | S1                    | numpy.array       | SNR observation data on L1                                   |
           | S2                    | numpy.array       | SNR observation data on L2                                   |
           | S5                    | numpy.array       | SNR observation data on L5                                   |
           | S6                    | numpy.array       | SNR observation data on L6                                   |
           | S7                    | numpy.array       | SNR observation data on L7                                   |   
           | S8                    | numpy.array       | SNR observation data on L8                                   | 
           | time                  | Time              | Time                                                         |               
        """
        
        float_fields = {
                "azimuth": "radian",
                "elevation": "radian",
                "elevation_rate": "radian/second",
                "S1": None,
                "S2": None,
                "S5": None,
                "S6": None,
                "S7": None,
                "S8": None,
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
      
        # Add time field
        dset.add_time(
                name="time", 
                val=self.data["time"], 
                scale="gps", 
                fmt="datetime", 
                write_level="operational",
        )
        
        # Add float fields
        for field in float_fields.keys():
            if field not in self.data.keys():
                log.warn(f"Field '{field}' does not exist in file {self.meta['__data_path__']}.")
                continue
            
            value = np.deg2rad(self.data[field]) if field in ["azimuth", "elevation", "elevation_rate"] else self.data[field]
            unit = "" if float_fields[field] is None else float_fields[field]
            
            dset.add_float(name=field, val=value, unit=unit, write_level="operational")
        
        return dset


        
