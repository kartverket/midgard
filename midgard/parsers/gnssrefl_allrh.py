"""A parser for reading GNSSREFL reflector height timeseries files

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnssrefl_allrh', file_path='tgde_allRH.txt')
    data = p.as_dict()

Description:
------------

Reads data from files in GNSSREFL reflector height timeseries files

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
class GnssreflAllRh(LineParser):
    """A parser for reading GNSSREFL reflector height timeseries files

    Following **data** are available after reading Terrapos residual file:

    | Parameter                 | Description                                                                     |
    |---------------------------|---------------------------------------------------------------------------------|
    | amplitude                 | Amplitude                                                                       |
    | azimuth                   | Azimuth in [deg]                                                                |
    | frequency                 | GNSS frequency identifier                                                       |
    | peak2noise                | Peak to noise                                                                   |
    | reflection_height         | Reflection height in [m]                                                        |
    | satellite                 | Satellite number                                                                |
    | time                      | Time as datetime object                                                         |

    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |

    """

    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

	# % year,doy, RH(m), Month, day, azimuth(deg),freq, satNu, LSP amp,pk2noise,UTC(hr)  
	# 2021     9   4.888  1  9  225.3    1    2   9.51   3.23  10.08
	# 2021     9   5.018  1  9  181.3    1   15   7.79   2.84  15.67
	# 2021     9   5.123  1  9  185.4    1   16   6.27   3.01   0.68
        #----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7
        return dict(
            skip_header=1,
            names=(
                "year",
                "doy",
                "reflection_height",
                "month",
                "day",
                "azimuth",
                "frequency",
                "satellite",
                "amplitude",
                "peak2noise",
                "hour",
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
        """Add time parameter to data and delete 'year', 'doy', 'month', 'day' and 'hour' field
        """
        self.data["time"] = [datetime(int(yyyy), int(mm), int(dd)) + timedelta(hours=hh) for yyyy, mm, dd, hh in zip(self.data["year"], self.data["month"], self.data["day"], self.data["hour"])]
        for key in ["year", "doy", "month", "day", "hour"]:
            del self.data[key]


    #
    # DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            Midgard Dataset where timeseries data are stored with following fields:

    
           | Field                 | Type              | Description                                                  |
           |-----------------------|-------------------|--------------------------------------------------------------|
           | amplitude             | numpy.array       | Amplitude                                                    |
           | azimuth               | numpy.array       | Azimuth in [rad]                                             |
           | frequency             | numpy.array       | GNSS frequency identifier                                    |
           | peak2noise            | numpy.array       | Peak to noise                                                |
           | satellite             | numpy.array       | Satellite number                                             |
           | reflection_height     | numpy.array       | Reflection height in [m]                                     |
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
                "peak2noise": None, 
                "reflection_height": "meter", 
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
        
        # Add float fields
        for field in float_fields.keys():
            if field not in self.data.keys():
                log.warn(f"Field '{field}' does not exist in file {self.meta['__data_path__']}.")
                continue
            
            value = np.deg2rad(self.data[field]) if field == "azimuth" else self.data[field]
            unit = "" if float_fields[field] is None else float_fields[field]
            
            dset.add_float(name=field, val=value, unit=unit, write_level="operational")
        
        return dset


        
