"""A parser for reading timeseries files in SAMLE format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='timeseries_samle', file_path='aasc.dat')
    data = p.as_dict()

Description:
------------

Reads data from files timeseries files in SAMLE (latitude, longitude, height) format

"""
# Standard library imports
from datetime import datetime
from typing import Any, Callable, Dict, List, Union

# External library imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.data import position
from midgard.dev import log
from midgard.dev import plugins
from midgard.math.unit import Unit
from midgard.parsers import LineParser


@plugins.register
class TimeseriesEnvParser(LineParser):
    """A parser for reading timeseries files in TSVIEW format

    Following **data** are available after reading timeseries TSVIEW file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | yy                   | Last 2 digits of year                                                                |
    | doy                  | Day of year                                                                          |
    | lat_deg              | Degree part of latitude                                                              |
    | lat_min              | Minute part of latitude                                                              |
    | lat_sec              | Second part of latitude                                                              |
    | lon_deg              | Degree part of longitude                                                             |
    | lon_min              | Minute part of longitude                                                             |
    | lon_sec              | Second part of longitude                                                             |
    | height               | Height in [m]                                                                        |

    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__params__          | np.genfromtxt parameters                                                             |
    | \__parser_name__     | Parser name                                                                          |
    """

    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

        # ----+----1----+----2----+----3----+----4----+----5----+----6---
        # 14/115   59   39   37.21282   10   46   54.20869   133.5833
        # 14/116   59   39   37.21284   10   46   54.20867   133.5821
        # 14/117   59   39   37.21284   10   46   54.20864   133.5853
        return dict(
            names=("yy_doy", "lat_deg", "lat_min", "lat_sec", "lon_deg", "lon_min", "lon_sec", "height"),
            delimiter=(6, 5, 5, 11, 5, 5, 11, 11),
            dtype=("U6", "f8", "f8", "f8", "f8", "f8", "f8", "f8"),
            autostrip=True,
        )
  
      
    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        
        Returns:
            List with postprocessor function calls
        """
        return [
                self._expand_dimension,
                self._get_yy_doy,
        ]


    def _expand_dimension(self) -> None:
        """Expand numpy array dimension, if array is 0-dimensional array

        np.genfromtxt return a 0-dimensional array, if input file has only one line.
        """
        if self.data["yy_doy"].ndim == 0:
            for key, value in self.data.items():
                self.data[key] = np.expand_dims(value, axis=0)
   
    
    def _get_yy_doy(self) -> None:
        """Get yy and doy by splitting yy/doy
        """
        self.data["yy"] = np.zeros(len(self.data["yy_doy"]), dtype=np.int)
        self.data["doy"] = np.zeros(len(self.data["yy_doy"]), dtype=np.int)
        
        for idx, yy_doy in enumerate(self.data["yy_doy"]):
            yy, doy = yy_doy.split("/")
            self.data["yy"][idx] = yy
            self.data["doy"][idx] = doy
            
        del self.data["yy_doy"]
        
        
    #
    # CONVERTERS
    #    
    def _get_datetime(self) -> datetime:
        """Convert YYDDD time format to datetime value

        The epoch is given in YY DDD format with::

            YY    = last 2 digits of the year,
                      if YY <= 50 implies 21-st century,
                      if YY > 50 implies 20-th century,
            DDD   = 3-digit day of year..

        Returns:
            YYDDD time format converted to datetime object.
        """
        num_obs = len(self.data["yy"])
        centuries = np.full(num_obs, 1900)
        idx = self.data["yy"] <= 50
        centuries[idx] = 2000
        
        date = np.zeros(num_obs, dtype=np.object)        
        for idx, (ce, yy, doy) in enumerate(zip(centuries, self.data["yy"], self.data["doy"])):
            date[idx] = datetime.strptime(f"{ce+yy}{doy}", "%Y%j")

        return date

            
    #
    # GENERATE DATASET
    #
    def as_dataset(self, ref_pos: Union[np.ndarray, List[float]]=None) -> "Dataset":
        """Return the parsed data as a Dataset

        Args:
            ref_pos: Reference position given in terrestrial reference system and meters

        Returns:
            A dataset containing the data.
        """
        

        # Initialize dataset
        dset = dataset.Dataset()
        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(self.data["yy"])

        # Absolute position
        pos_abs = position.Position(
                np.stack(
                        (Unit.dms_to_rad(self.data["lat_deg"], self.data["lat_min"], self.data["lat_sec"]),
                        Unit.dms_to_rad(self.data["lon_deg"], self.data["lon_min"], self.data["lon_sec"]),
                        self.data["height"]),
                        axis=1,
                ),
                system="llh",
        )
                        
        # Use either first position element or given argument as reference position
        if ref_pos is None:
            ref_pos = position.Position(np.repeat(np.array([pos_abs[0].val]), dset.num_obs, axis=0), system="llh")
        else:
            ref_pos = position.Position(np.repeat(np.array([ref_pos]), dset.num_obs, axis=0), system="trs")
  
        # Add relative position
        dset.add_position_delta(
            name="pos",
            val=(pos_abs.trs - ref_pos.trs).val,
            system="trs",
            ref_pos=ref_pos,
        )

        # Add time
        dset.add_time(
                name="time", 
                val=self._get_datetime(), 
                scale="utc", 
                fmt="datetime", 
                write_level="operational",
        )

        return dset
