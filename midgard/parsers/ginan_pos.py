"""A parser for reading GINAN position (POS) output file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='ginan_pos', file_path='ginan_pos')
    data = p.as_dict()

Description:
------------

Reads data from files in GINAN position (POS) output format.

"""
# Standard library imports
from datetime import datetime
from typing import Any, Dict, Tuple, Union

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.data.time import Time
from midgard.data.position import Position
from midgard.dev import plugins
from midgard.files import files
from midgard.math.unit import Unit
from midgard.parsers import LineParser


@plugins.register
class GinanPosParser(LineParser):
    """A parser for reading GINAN position (POS) output file

    Following **data** are available after reading GINAN position (POS) file:

    | Key                  | Description                                                                          |
    | :------------------- | :----------------------------------------------------------------------------------- |
    | gpsweek              | GPS week                                                                             |
    | gpssec               | Seconds of GPS week                                                                  |
    | head                 | Head in [deg]                                                                        |
    | height               | Ellipsoidal height in [m]                                                            |
    | lat                  | Latitude in [deg]                                                                    |
    | lon                  | Longitude in [deg]                                                                   |
    | num_sat              | Number of satellites                                                                 |
    | pdop                 | Position Dilution of Precision (PDOP)                                                |
    | pitch                | Pitch in [deg]                                                                       |
    | reliability_east     | East position external reliability in [m] #TODO: Is that correct?                    |
    | reliability_height   | Height position external reliability in [m] #TODO: Is that correct?                  |
    | reliability_north    | North position external reliability in [m] #TODO: Is that correct?                   |
    | roll                 | Roll in [deg]                                                                        |
    | sigma_east           | Standard deviation of East position in [m] #TODO: Is that correct?                   |
    | sigma_height         | Standard deviation of Height position in [m] #TODO: Is that correct?                 |
    | sigma_north          | Standard deviation of North position in [m] #TODO: Is that correct?                  |

    and **meta**-data:

    | Key                  | Description                                                                          |
    | :------------------- | :----------------------------------------------------------------------------------- |
    | \\__data_path__      | File path                                                                            |
    | \\__parser_name__    | Parser name                                                                          |
    """
    
    def __init__(
        self,
        *args: Tuple[Any],
        station: Union[None, str] = None,
        **kwargs: Dict[Any, Any],
    ) -> None:
        """Initialize parser
        
        Args:
            args:           Parameters without keyword.
            station:        Station name.
            kwargs:         Keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.station = station


    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """
        
        # Parse header 
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8--
        # PBO Station Position Time Series. Reference Frame : IGS20
        # Format Version: 2.0.0
        # 4-character ID: ALTC
        # First Epoch   : 2026-01-01T00:00:00.00
        # XYZ Reference position :  2011819.992200 866267.819400 5970245.069300 (IGS20)
        # NEU Reference position :  69.976762635662 23.296186051668 98.142905543 (IGS20/WGS84)
        # Start Field Description
        # YYYY-MM-DDTHH:MM:SS.SSS  Date and Time of given position epoch (GPS Time)
        # YYYY.YYYYYYYYY          Decimal year of given position epoch (GPS Time)
        # X                       X coordinate, Specified Reference Frame, meters
        # Y                       Y coordinate, Specified Reference Frame, meters
        # Z                       Z coordinate, Specified Reference Frame, meters
        # Sx                      Sigma of the X position
        # Sy                      Sigma of the Y position
        # Sz                      Sigma of the Z position
        # Rxy                     Correlation between the X and Y position
        # Rxz                     Correlation between the X and Z position
        # Ryz                     Correlation between the Y and Z position
        # Nlat                    North latitude, WGS-84 ellipsoid, decimal degrees
        # Elong                   East longitude, WGS-84 ellipsoid, decimal degrees
        # Height (Up)             Height relative to WGS-84 ellipsoid, meters
        # dN                      Difference in North component from NEU reference position, meters
        # dE                      Difference in East component from NEU reference position, meters
        # dU                      Difference in vertical component from NEU reference position, meters
        # Sn                      Sigma of dN, meters
        # Se                      Sigma of dE, meters
        # Su                      Sigma of dU, meters
        # Rne                     Correlation between dN and dE
        # Rnu                     Correlation between dN and dU
        # Reu                     Correlation between dE and dU
        # Soln                    Solution type
        # End Field Description
        #
        self._parse_header()        

        # Parser for GINAN position (POS) output file

        # *YYYY-MM-DDTHH:MM:SS.SSS YYYY.YYYYYYYYY        X             Y              Z           Sx         Sy        Sz      Rxy     Rxz     Ryz        NLat            Elong        Height         dN          dE          dU        Sn       Se         Su       Rne     Rnu     Reu  soln
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+--
        #  2026-01-01T00:00:30.000 2026.002740107 2011818.18297 866269.60359 5970247.22710   0.83014   1.10513   2.43854  -0.123   0.404   0.541   69.9767773102   23.2962476334    99.84291     1.63715     2.35425     1.70000   0.67271   1.10450   2.48685   0.321   0.403   0.362 ginan
        #  2026-01-01T00:01:00.000 2026.002741058 2011818.50535 866268.65373 5970245.86695   0.61034   0.71073   1.55655  -0.116   0.465   0.433   69.9767738058   23.2962214779    98.53772     1.24618     1.35433     0.39482   0.46488   0.72179   1.60107   0.233   0.281   0.220 ginan

        return dict(
            skip_header=32, # Skip header lines
            comments="*",  # Remove comment lines starting with '*'
            names=(
                "time",
                "decimalyear",
                "x",
                "y",
                "z",
                "sigma_x",
                "sigma_y",
                "sigma_z",
                "correlation_xy",
                "correlation_xz",
                "correlation_yz",
                "lat",
                "lon",
                "height",
                "north",
                "east",
                "up",
                "sigma_north",
                "sigma_east",
                "sigma_up",
                "correlation_ne",
                "correlation_nu",
                "correlation_eu",
                "solution_type",
            ),
            delimiter= None, # delimiter=None handling of whitespaces as delimiter
            dtype=None, # NumPy is defining data type for each column automatically
            encoding="utf-8", # Necessary that normal 'str' is returned and not 'bytes'
        )
        

    def _parse_header(self) -> None:
        """Parse header
        """
        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            
            for line in fid: 
            
                if "End Field Description" in line:
                    break
                
                if "Reference Frame :" in line:
                    _, ref_frame = line.split(":")
                    self.meta["ref_frame"] = ref_frame.strip()
                    continue
                    
                if "XYZ Reference position :" in line:
                    _, ref_pos = line.split(":")
                    ref_pos = [float(v) for v in ref_pos.strip().split()[0:3]]
                    self.meta["ref_pos_x"] = ref_pos[0]
                    self.meta["ref_pos_y"] = ref_pos[1]
                    self.meta["ref_pos_z"] = ref_pos[2]
                    
                    
    #
    # WRITE DATA
    #
    def as_dataset(self) -> "Dataset":
        """Store GINAN position (POS) output data in a dataset

        Returns:
            Midgard Dataset where GINAN position (POS) output data are stored with following fields:
            
       | Field                    | Type           | Description                                                      |
       | :----------------------- | :------------- | :--------------------------------------------------------------- |
       | dsite_pos                | Position delta | Position delta object refered to a reference position            |
       | dsite_pos_eu_correlation | numpy.ndarray  | Correlation between East and Up topocentric station coordinate   |
       | dsite_pos_ne_correlation | numpy.ndarray  | Correlation between North and East topocentric station coordinate|
       | dsite_pos_nu_correlation | numpy.ndarray  | Correlation between North and Up topocentric station coordinate  |
       | dsite_pos_east_sigma     | numpy.ndarray  | Standard deviation of topocentric East-coordinate                |
       | dsite_pos_north_sigma    | numpy.ndarray  | Standard deviation of topocentric North-coordinate               |
       | dsite_pos_up_sigma       | numpy.ndarray  | Standard deviation of topocentric Up-coordinate                  |
       | site_pos                 | Position       | Geocentric station coordinates x, y and z                        |
       | site_pos_xy_correlation  | numpy.ndarray  | Correlation between x and y station coordinate                   |
       | site_pos_xz_correlation  | numpy.ndarray  | Correlation between x and z station coordinate                   |
       | site_pos_yz_correlation  | numpy.ndarray  | Correlation between y and z station coordinate                   |
       | site_pos_x_sigma         | numpy.ndarray  | Standard deviation for x station coordinate                      |
       | site_pos_y_sigma         | numpy.ndarray  | Standard deviation for y station coordinate                      |
       | site_pos_z_sigma         | numpy.ndarray  | Standard deviation for z station coordinate                      |
       | time                     | Time           | Observation time given as Time object                            |
       
        and **meta**-data:       

       |  Field              | Type  | Description                                                                    |
       | :------------------ | :---- | :----------------------------------------------------------------------------- |
       | ref_epoch           | str   | Reference epoch of reference station coordinate in ISO format                  |
       |                     |       | yyyy-mm-ddTHH:MM:SS (e.g. 2025-01-01T00:00:00)                                 |
       | ref_frame           | str   | Reference frame of reference station coordinate (e.g. IGS20)                   |
       | ref_pos_x           | float | X-coordinate of reference station coordinate in [m]                            |
       | ref_pos_y           | float | Y-coordinate of reference station coordinate in [m]                            |
       | ref_pos_z           | float | Z-coordinate of reference station coordinate in [m]                            |
        
        """
        dset = dataset.Dataset(num_obs=len(self.data["time"]))
        dset.meta.update(self.meta)
        
        # Remove unnecessary entries in meta
        for key in ["__params__", "__parser_name__"]:
            del dset.meta[key]
        
        float_field_def = {
                "correlation_eu": "dsite_pos_eu_correlation",
                "correlation_ne": "dsite_pos_ne_correlation",
                "correlation_nu": "dsite_pos_nu_correlation",
                "correlation_xy": "site_pos_xy_correlation",
                "correlation_xz": "site_pos_xz_correlation",
                "correlation_yz": "site_pos_yz_correlation",
                "sigma_north": "dsite_pos_north_sigma",
                "sigma_east": "dsite_pos_east_sigma",
                "sigma_up": "dsite_pos_up_sigma",
                "sigma_x": "site_pos_x_sigma",
                "sigma_y": "site_pos_y_sigma",
                "sigma_z": "site_pos_z_sigma",
        }
        
        # Add float fields
        for key, field in float_field_def.items():
            dset.add_float(field, val=self.data[key], unit="meter")
            
        # Add time field
        dset.add_time(
            "time",
            val= Time(
                    val=[ datetime.fromisoformat(v) for v in self.data["time"] ], 
                    scale="gps", 
                    fmt="datetime",
            ),
        )
        
        # Add position field
        dset.add_position(
            "site_pos",
            time=dset.time,
            system="trs",
            val=np.stack((
                    self.data["x"],
                    self.data["y"], 
                    self.data["z"]), 
                    axis=1,
            )
        )
        
        # Add position_delta field
        ref_pos = Position(
                    np.repeat(
                        np.array([[
                            dset.meta["ref_pos_x"], 
                            dset.meta["ref_pos_y"],
                            dset.meta["ref_pos_z"],
                        ]]), 
                        dset.num_obs, 
                        axis=0,
                    ), 
                    system="trs",
        )
        
        dset.add_position_delta(
            "dsite_pos",
            val=np.vstack((
                  self.data["east"], 
                  self.data["north"], 
                  self.data["up"]),
            ).T,
            system="enu",
            ref_pos=ref_pos,
        )
                
        # TODO: Should this information be added?
        ## Add text field
        #if self.station:
        #    dset.add_text("station", val=np.repeat(self.station, dset.num_obs))
        
        return dset
