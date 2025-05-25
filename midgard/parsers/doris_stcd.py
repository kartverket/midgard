"""A parser for reading DORIS station coordinate timeseries file in STCD format


Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='doris_stcd', file_path='ids21wd03.stcd.svac')
    data = p.as_dict()

Description:
------------

Reads station coordinate timeseries data from files in DORIS STCD format

"""
# Standard library imports
from collections import namedtuple
from typing import Callable, List

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.data.position import Position
from midgard.dev import plugins, log
from midgard.files import files
from midgard.parsers._parser_sinex import SinexParser, SinexBlock, SinexField


FieldDef = namedtuple(
    "FieldDef", ["field", "unit"]
)
FieldDef.__new__.__defaults__ = (None,) * len(FieldDef._fields)
FieldDef.__doc__ = """A convenience class for defining dataset fields 

    Args:
        field (str):             Dataset field name
        unit (str):              Unit of field
    """


@plugins.register
class DorisStcdParser(SinexParser):
    """A parser for reading DORIS station coordinate timeseries file in STCD format
    """

    def __init__(self, file_path, encoding=None):
        """Set up the basic information needed by the parser

        Args:
            file_path (String/Path):    Path to file that will be read.
            encoding (String):          Encoding of file that will be read.
        """
        super().__init__(file_path, encoding)

    def setup_parser(self):
        return [
            self.file_reference, # End line -FILE/REFERENCE of SINEX block is missing. Therefore also FILE/COMMENT block is read in addition.
            #self.file_comment, 
            self.site_id,
            self.solution_apriori,
    ]
    
    
    def read_data(self) -> None:
        """Read data from a Sinex file and parse the contents

        First the whole Sinex file is read and the requested blocks are stored in self._sinex. After the file has been 
        read, a parser is called on each block so that self.data is properly populated.
        
        The header information of the DORIS STCD timeseries format follows to a certain extend the SINEX format. 
        Therefore the SINEX parser is used. The timeseries data itself are read by the timeseries_data() function.
        """
        # Read raw sinex data to self._sinex from file
        with files.open(self.file_path, mode="rb") as fid:
            if self._header:
                self.parse_header_line(next(fid))  # Header must be first line
            self.parse_blocks(fid)

        # Apply parsers to raw sinex data, the information returned by parsers is stored in self.data
        for sinex_block in self.sinex_blocks:
            if sinex_block.parser and sinex_block.marker in self._sinex:
                params = self._sinex.get("__params__", dict()).get(sinex_block.marker, ())
                data = sinex_block.parser(self._sinex.get(sinex_block.marker), *params)
                if data is not None:
                    self.data[sinex_block.marker] = data
                    
        # Read timeseries data
        self.timeseries_data()
    
        
    #
    # Definition of SINEX blocks to parse
    # 
    
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
    # +FILE/REFERENCE
    #  DESCRIPTION   Analysis of the IDS (16-17) weekly solutions by the IDS Combination Center
    #  INPUT         Weekly sinex in free-network
    #  OUTPUT        Weekly sinex expressed in DPOD2014
    #  CONTACT       Guilhem.Moreaux@cls.fr
    #  SOFTWARE      CATREF software
    # *_______________________________________________________________________________ 
    
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0
    # +FILE/COMMENT
    #  FIELDS - modified julian date, dX, dY, dZ, sX, sY, sZ, dEast, dNorth, dUp, sEast, sNorth, sUp
    #  FORMAT - 2x,f7.1,2(2x,3(1x,f6.3),3(1x,f5.3))
    #  UNITS - all position residuals in millimeters  
    #  REFERENCE SYSTEM - DORIS terrestrial system
    #  EARTH ELLIPSOID - flattening factor: 298.257810 equatorial radius: 6378136.0 m
    # -FILE/COMMENT
    # *_______________________________________________________________________________
    @property
    def file_reference(self) -> SinexBlock:
        """Information about how the Sinex file was created

        Provides information on the Organization, point of contact, the
        software and hardware involved in the creation of the file.
        """        
        return SinexBlock(
            marker="FILE/REFERENCE",
            fields=(SinexField("comment", 1, "U100"),),  #TODO: Why is length of characters limited to U79 even if U100 is given?
            parser=self.parse_file_reference,
        )    
    
    
    def parse_file_reference(self, data):
        """Parse FILE/REFERENCE SINEX block and FILE/COMMENT SINEX block due to missing end of SINEX block
        (-FILE/REFERNCE) in the DORIS STCD format
        """
        data = data[np.newaxis] if data.ndim == 0 else data
        self.data.setdefault("file_reference", list())
        for d in data:
            self.data["file_reference"].append(d[0])    

    #def parse_file_comment(self, data):
    #    """Parse FILE/COMMENT SINEX block"""
    #    data = data[np.newaxis] if data.ndim == 0 else data
    #    self.data.setdefault("file_comment", list())
    #    for d in data:
    #        self.data["file_comment"].append(d[0])
    
    
    #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
    # +SITE/ID
    # *Code Pt __Domes__ T _Station Description__ _Longitude_ _Latitude__ _Height
    #  SVAC  A 10338S003 D NY-ALESUND II, NORWAY   11 50 29.7  78 56 27.8    65.8
    # -SITE/ID
    # *_______________________________________________________________________________
    def parse_site_id(self, data):
        """Parse SITE/ID SINEX block"""
        data = data[np.newaxis] if data.ndim == 0 else data
        self.data.setdefault("site_id", dict())
        for d in data:
            self.data["site_id"].update(
                {n: d[n] for n in d.dtype.names}
            )
     
    #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
    # +SOLUTION/APRIORI
    # *Index _Type_ Code Pt Soln _Ref_Epoch__ Unit S __Estimated Value____ _Std_Dev___
    #     -- STAX   SVAC -- ---- 00:001:00000 m    2 +1.20130004166439e+06 2.00720e-03
    #     -- STAY   SVAC -- ---- 00:001:00000 m    2 +2.51874432173654e+05 2.00660e-03
    #     -- STAZ   SVAC -- ---- 00:001:00000 m    2 +6.23800030817128e+06 1.90070e-03
    # -SOLUTION/APRIORI
    # *_______________________________________________________________________________      
    def parse_solution_apriori(self, data):
        """Parse SOLUTION/APRIORI SINEX block"""
        data = data[np.newaxis] if data.ndim == 0 else data
        self.data.setdefault("solution_apriori", dict())
        for d in data:
            param_name = d["param_name"].lower()
            self.data["solution_apriori"].setdefault(param_name, dict())
            self.data["solution_apriori"][param_name].update(
                {n: d[n] for n in d.dtype.names}
            )
            for key in ["param_idx", "param_name", "point_code", "site_code", "soln"]:
                del self.data["solution_apriori"][param_name][key]
                
                
    def timeseries_data(self):
        """Custom made block describing the solution.
        
        Is a list of keywords and values

        Example:
              58408.5      -328.1     201.4     311.6       6.4       6.3       6.2       263.5     333.4     252.1       6.2       6.4       6.2
              58415.5      -319.8     184.6     306.9       2.7       2.5       2.3       245.5     327.9     248.4       2.5       2.7       2.3
              58422.5      -319.8     186.9     317.5       3.1       2.8       2.5       247.8     329.5     258.9       2.8       3.0       2.6
            0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3--
                      
        """
        #modified julian date, dX, dY, dZ, sX, sY, sZ, dEast, dNorth, dUp, sEast, sNorth, sUp
        
        # Read raw sinex data to self._sinex from file
        with files.open(self.file_path, mode="rt") as fid:
            for line in fid:
                if line.startswith("-SOLUTION/APRIORI"):
                    self.parse_timeseries_data(fid)


    def parse_timeseries_data(self, fid) -> None:
        """Parser for timeseries data
         
        Args:
            fid: File handle
        """
        column_name_def = [
            "mjd",
            "dx",
            "dy",
            "dz",
            "sig_x",
            "sig_y",
            "sig_z",
            "deast",
            "dnorth",
            "dup",
            "sig_east",
            "sig_north",
            "sig_up",
        ]
        self.data.setdefault("timeseries_data", dict())
        
        # Read timeseries data
        data = list()
        for line in fid:
        
            # Skip comment lines
            if line.startswith("*"):
                continue                
                
            data.append(line.split())
            
        # Save data in attribute timeseries_data by using the column names
        data = np.array(data)
        for name, col in zip(column_name_def, data.T):           
            self.data["timeseries_data"][name] = col.astype(float)
                         
    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing"""
        return [
            self._divide_file_reference_from_comment_block,
        ]


    def _divide_file_reference_from_comment_block(self) -> None:
        """Divide FILE/REFERENCE entries from FILE/COMMENT entries
        
        End line -FILE/REFERENCE of SINEX block is missing. Therefore also FILE/COMMENT block is read in addition by
        parse_file_reference() parser.
        """
        if len(self.data["file_reference"]) != 10:
            log.fatal(f"Number of FILE/REFERENCE and FILE/COMMENT lines differs. Parser expects 10 lines, {len(self.data["file_reference"])} are given")

        self.data["file_comment"] = self.data["file_reference"][5:10]
        self.data["file_reference"]  = {d[0:14].strip().lower(): d[14:] for d in self.data["file_reference"][0:5]}

                
    #
    # GET DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Store SINEX timeseries data block entries in a dataset
        
        Note: The dEast, dNorth, dUp values can not be reproduced by using dX, dY, dZ values together with 
              SOLUTION/APRIORI coordinate as reference coordinate (difference with up to 1 mm). The difference is not
              related to use of GRS80 ellipsoid instead of DORIS one. Maybe it is related to rounding of dX, dY, dZ
              values or reference coordinate.

        Returns:
            Midgard Dataset whereby following SINEX timeseries data block entries could be stored (depending on input 
            data):

       | Field                    | Type              | Description                                                   |
       | :----------------------- | :---------------- | :------------------------------------------------------------ |
       | dsite_pos                | PositionDelta     | Position delta object refered to a reference position         |       
       | dsite_pos_east_sigma     | numpy.ndarray     | Standard deviation of topocentric East-coordinate             |
       | dsite_pos_north_sigma    | numpy.ndarray     | Standard deviation of topocentric North-coordinate            |
       | dsite_pos_up_sigma       | numpy.ndarray     | Standard deviation of topocentric Up-coordinate               |
       | dsite_pos_x_sigma        | numpy.ndarray     | Standard deviation of geocentric X-coordinate                 |
       | dsite_pos_y_sigma        | numpy.ndarray     | Standard deviation of geocentric Y-coordinate                 |
       | dsite_pos_z_sigma        | numpy.ndarray     | Standard deviation of geocentric Z-coordinate                 |
       | site_pos                 | Position          | Position object with given station coordinates                |
       | time                     | Time              | Parameter time given as TimeTable object                      |
           
        and **meta**-data:

       | Key              | Type          | Description                                                               |
       | :--------------- | :------------ | :------------------------------------------------------------------------ |
       | __data_path__    | str           | Data file path                                                            |
       | \__params__      | dict          | np.genfromtxt parameters                                                  |
       | __parser_name__  | str           | Parser name                                                               |
       | file_comment     | list          | General comments about the Sinex data file                                |
       | file_reference   | dict          | Information about how the Sinex file was created                          |
       | ref_epoch        | str           | Reference epoch of reference station coordinate in ISO format             |
       |                  |               | yyyy-mm-ddTHH:MM:SS (e.g. 2025-01-01T00:00:00)                            |
       | ref_pos_x        | float         | X-coordinate of reference station coordinate in [m]                       |
       | ref_pos_y        | float         | Y-coordinate of reference station coordinate in [m]                       |
       | ref_pos_z        | float         | Z-coordinate of reference station coordinate in [m]                       | 
       | site_id          | dict          | General information of site                                               | 
       """
        dset = dataset.Dataset(num_obs=len(self.data["timeseries_data"]["mjd"]))
        dset.meta.update(self.meta)
        dset.meta["station"] = self.data["site_id"]["site_code"].lower() if "site_id" in self.data.keys() else "NONE" 
        
        # Move solution apriori information to meta reference coordinate variables
        dset.meta["ref_epoch"] = self.data["solution_apriori"]["stax"]["ref_epoch"].isoformat()
        dset.meta["ref_pos_x"] = self.data["solution_apriori"]["stax"]["apriori"]
        dset.meta["ref_pos_y"] = self.data["solution_apriori"]["stay"]["apriori"]
        dset.meta["ref_pos_z"] = self.data["solution_apriori"]["staz"]["apriori"]
        
        # Add site_info dictionary to meta variable
        for block in ["file_comment", "file_reference", "site_id"]:
            if block in self.data.keys():
                dset.meta[block] = self.data[block]
        
        # Add time field to dataset
        dset.add_time("time", val=self.data["timeseries_data"]["mjd"], scale="utc", fmt="mjd")
                             
        # Add position_delta field to dataset
        if "dx" in self.data["timeseries_data"].keys():
            ref_pos = Position(
                val = [ 
                    dset.meta["ref_pos_x"],
                    dset.meta["ref_pos_y"],
                    dset.meta["ref_pos_z"],
                ],
                system="trs",
            )
            
            dset.add_position_delta(
                "dsite_pos",
                val=np.vstack((
                    self.data["timeseries_data"]["dx"], 
                    self.data["timeseries_data"]["dy"], 
                    self.data["timeseries_data"]["dz"]),
                ).T,
                system="trs",
                ref_pos=ref_pos,
            )
            
            dset.add_position(
                "site_pos",
                val=np.vstack((
                    self.data["timeseries_data"]["dx"] + dset.meta["ref_pos_x"], 
                    self.data["timeseries_data"]["dy"] + dset.meta["ref_pos_y"], 
                    self.data["timeseries_data"]["dz"] + dset.meta["ref_pos_z"]),
                ).T,
                system="trs",
            )
                    
        # Add float field to dataset
        field_def = {
            "sig_x": FieldDef("dsite_pos_x_sigma", "meter"),
            "sig_y": FieldDef("dsite_pos_y_sigma", "meter"),
            "sig_z": FieldDef("dsite_pos_z_sigma", "meter"),
            "sig_east": FieldDef("dsite_pos_east_sigma", "meter"),
            "sig_north": FieldDef("dsite_pos_north_sigma", "meter"),
            "sig_up": FieldDef("dsite_pos_up_sigma", "meter"),
        }
              
        for type_, def_ in field_def.items():
            if type_ in self.data["timeseries_data"].keys():
                dset.add_float(def_.field, val=self.data["timeseries_data"][type_], unit=def_.unit)

        return dset
    
