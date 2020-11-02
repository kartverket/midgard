"""A parser for GALAT single point positioning result files

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnss_galat_results', file_path='galat_results.txt')
    data = p.as_dict()

Description:
------------

Reads data from files in GALAT result format.

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
from midgard.files import files
from midgard.math.unit import Unit
from midgard.parsers import LineParser


@plugins.register
class GalatResults(LineParser):
    """A parser for reading GALAT single point positioning result files

    Following **data** are available after reading GALAT SPP result file:

    | Key                      | Description                                                                      |
    |--------------------------|----------------------------------------------------------------------------------|
    | time                     | Time epoch                                                                       |
    | latitude                 | Latitude in degree                                                               |
    | longitude                | Longitude in degree                                                              |
    | height                   | Height in [m]                                                                    |
    | dlatitude                | Latitude related to reference coordinate in [m]                                  |
    | dlongitude               | Longitude related to reference coordinate in [m]                                 |
    | dheight                  | Height related to reference coordinate in [m]                                    |
    | hpe                      | Horizontal positioning error (HPE) in [m]                                        |
    | vpe                      | Vertical positioning error (VPE) in [m]                                          |
    | site_vel_3d              | 3D site velocity in [m/s]                                                        |
    | pdop                     | Precision dilution of precision                                                  |
    | num_satellite_available  | Number of available satellites                                                   |
    | num_satellite_used       | Number of used satellites                                                        |
    

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


        # % GALAT - SPP Single Point Positioning
        # % -------------------------------------
        # % Processing Option
        # % ------------------
        # % GNSS system(s) : GALILEO
        # % Orbit type     : Broadcast - INAV
        # % Solution type  : SPP
        # % Frequency      : E1
        # % Elevation mask : 5.0 deg
        # % Time interval  : 30.0 s
        # % Ionosphere opt : NeQuick-G
        # % Troposhere opt : GMF with GPT
        # % Obs start      : 2020/01/04 00:00:00.0 GPST (week 2086 518400.0s)
        # % Obs end        : 2020/01/04 23:59:30.0 GPST (week 2086 604770.0s)
        # % Epoch expected : 2880
        # % Epoch have     : 2880
        # %
        # % Input file(s)  : KOUG00GUF_R_20200040000_01D_30S_MO.rnx
        # % Input file(s)  : CNES0030.20L
        # % Input file(s)  : CNES0040.20L
        # % Input file(s)  : igs14.atx
        # %
        # % RINEX header info
        # % ------------------
        # % Marker         : KOUG 97301M402
        # % Receiver T/V/# : SEPT POLARX5TR      5.3.0               17323022503
        # % Antenna T/ /#  : LEIAR25.R3      LEIT                    10180007
        # % Position XYZ   :   3855263.3407 -5049731.9986   563040.4252
        # % Antenna H/E/N  :         0.0000        0.0000        0.0000
        self._parse_header()

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+--
        # 2020/01/04 00:00:00    5.098466365  -52.639742999  106.8901   -0.603   -0.821   -0.349    1.018    0.349    
        # 2020/01/04 00:00:30    5.098466094  -52.639742684  107.4962   -0.633   -0.856    0.257    1.065    0.257    
        # 2020/01/04 00:01:00    5.098466030  -52.639740961  107.6125   -0.640   -1.047    0.373    1.228    0.373    
        return dict(
            names=(
                "yyyymmdd", 
                "hhmmss", 
                "latitude", 
                "longitude", 
                "height", 
                "dlatitude", 
                "dlongitude", 
                "dheight",
                "hpe",
                "vpe",
                "site_vel_3d",
                "pdop",
                "num_satellite_available",
                "num_satellite_used",
            ),
            comments="%",
            delimiter=(10, 9, 15, 15, 10, 9, 9, 9, 9, 9, 9, 6, 4, 4),
            dtype=("U10", "U9", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8"),
            autostrip=True,
        )
            
            
    def _parse_header(self) -> None:
        """Parse header
        """
        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            
            for line in fid: 
                if not line.startswith("%"):
                    break
                
                # % Position XYZ   :   3855263.3407 -5049731.9986   563040.4252
                if line.startswith("% Position XYZ"):                    
                    pos_x, pos_y, pos_z = line.split(":")[1].split()
                    self.meta["pos_x"] = float(pos_x)
                    self.meta["pos_y"] = float(pos_y) 
                    self.meta["pos_z"] = float(pos_z)
 
      
    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        
        Returns:
            List with postprocessor function calls
        """
        return [
                self._get_time,
        ]   
    
    def _get_time(self) -> None:
        """Get time as datetime object based on 'yyyymmdd' and 'hhmmss' entries
        """
        self.data["time"] = np.zeros(len(self.data["yyyymmdd"]), dtype=object)
        
        for idx, (yyyymmdd, hhmmss) in enumerate(zip(self.data["yyyymmdd"], self.data["hhmmss"])):
            year, month, day = yyyymmdd.split("/")
            hour, minute, second = hhmmss.split(":")
            self.data["time"][idx] = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            
        del self.data["yyyymmdd"]
        del self.data["hhmmss"]
        
        

            
    #
    # GENERATE DATASET
    #
    def as_dataset(self, ref_pos: Union[np.ndarray, List[float], None] = None) -> "Dataset":
        """Return the parsed data as a Dataset

        Args:
            ref_pos: Reference position given in terrestrial reference system and meters

        Returns:
            Midgard Dataset where GALAT result data are stored with following fields:

    
           | Field                    | Type              | Description                                               |
           |--------------------------|-------------------|-----------------------------------------------------------|
           | hpe                      | np.ndarray        | Horizontal Position Error of site position vs. reference  |
           |                          |                   | position                                                  |
           | num_satellite_available  | np.ndarray        | Number of available satellites                            |
           | num_satellite_used       | np.ndarray        | Number of used satellites                                 |
           | pdop                     | np.ndarray        | Position dilution of precision                            |
           | site_pos                 | Position          | Site position                                             |
           | site_pos_vs_ref          | PositionDelta     | Site position versus reference coordinate                 |
           | site_vel_3d              | np.ndarray        | 3D site velocity                                          |
           | time                     | Time              | Parameter time given as TimeTable object                  |
           | vpe                      | np.ndarray        | Vertical Position Error of site position vs. reference    |
           |                          |                   | position                                                  |
        """
        fields = {
            #"hpe": "meter", # Recalculated based on site position and given reference coordinate
            #"vpe": "meter", # Recalculated based on site position and given reference coordinate
            "site_vel_3d": "meter/second",
            "pdop": "",
            "num_satellite_available": "",
            "num_satellite_used": "",
        }
        
        # Initialize dataset
        dset = dataset.Dataset()
        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(self.data["time"])
        
        # Add time field
        dset.add_time(
            "time",
            val=self.data["time"],
            scale="gps",
            fmt="datetime",
        )
        
        # Add float fields
        for field in fields.keys():
            dset.add_float(name=field, val=self.data[field], unit=fields[field])
            
        # Add site position field
        dset.add_position(
                "site_pos", 
                val=np.stack((
                        self.data["latitude"] * Unit.deg2rad,
                        self.data["longitude"] * Unit.deg2rad,
                        self.data["height"],
                ), axis=1),
                system="llh",
        )

        # Use either reference position from RINEX header or given argument as reference position
        if ref_pos is None:
            ref_pos = position.Position(
                    np.repeat(
                            np.array([[self.meta["pos_x"], self.meta["pos_y"], self.meta["pos_z"]]]),
                            dset.num_obs, 
                            axis=0,
                    ), 
                    system="trs",
            )
        else:
            ref_pos = position.Position(np.repeat(np.array([ref_pos]), dset.num_obs, axis=0), system="trs")            

        # Add relative position
        dset.add_position_delta(
            name="site_pos_vs_ref",
            val=(dset.site_pos.trs - ref_pos.trs).val,
            system="trs",
            ref_pos=ref_pos,
        )
            
        # Add HPE and VPE to dataset
        dset.add_float("hpe", val=np.sqrt(
                                dset.site_pos_vs_ref.enu.east ** 2 + dset.site_pos_vs_ref.enu.north ** 2), 
                                unit="meter",
        )
        dset.add_float("vpe", val=np.absolute(dset.site_pos_vs_ref.enu.up), unit="meter")
        
        return dset
