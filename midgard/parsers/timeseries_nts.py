"""A parser for reading timeseries files in NTS format

TODO: Header is not read completely and also not several data records.

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='timeseries_nts', file_path='stas.nts')
    data = p.as_dict()

Description:
------------

Reads data from files timeseries files in NTS format

"""
# Standard library imports
import numpy as np
from typing import Any, Dict, List, Tuple, Union

# Midgard imports
from midgard.data import dataset
from midgard.data.position import Position
from midgard.dev import log
from midgard.dev import plugins
from midgard.files import files
from midgard.math.unit import Unit
from midgard.parsers import LineParser


@plugins.register
class TimeseriesNtsPaser(LineParser):
    """A parser for reading timeseries files in NTS format

    Following **data** can be available after reading timeseries NTS file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | date                 | Date in format yyyy-mm-dd (e.g. 2018-05-10).                                         |
    | year                 | Date in unit year.                                                                   |
    | x                    | X-coordinate.                                                                        |
    | y                    | Y-coordinate.                                                                        |
    | z                    | Z-coordinate.                                                                        |
    | east                 | East coordinate.                                                                     |
    | north                | North coordinate.                                                                    |
    | vertical             | Vertical coordinate.                                                                 |
    | sigma_east           | Standard deviation of east coordinate.                                               |
    | sigma_north          | Standard deviation of north coordinate.                                              |
    | sigma_height         | Standard deviation of height coordinate.                                             |
    | sigma_x              | Standard deviation of X-coordinate.                                                  |
    | sigma_y              | Standard deviation of Y-coordinate.                                                  |
    | sigma_z              | Standard deviation of Z-coordinate.                                                  |

    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | names_of_columns     | List with column names                                                               |
    | units_of_columns     | List with unit given for each column                                                 |
    | \__data_path__       | File path                                                                            |
    | \__params__          | np.genfromtxt parameters                                                             |
    | \__parser_name__     | Parser name                                                                          |
    """
    
    def __init__(
        self,
        *args: Tuple[Any],
        **kwargs: Dict[Any, Any],
    ) -> None:
        """Initialize timeseries NTS format parser

        Args:
            args:           Parameters without keyword.
            kwargs:         Keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.dtype = list()

        
    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

        # Parse header
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+
        #\BEGIN HEADER 
        #\FILE_TYPE   NMA time series 1.6
        #\FILE_VERSION 
        #\CREATION  May 2005
        #\COMPUTER  
        #\COMPUTED_BY  
        #\CONTACT_PERSON  
        #\META_INFORMATION  No additional meta information
        #\END HEADER 
        #
        #\BEGIN PROGRAM 
        #\ID  gamit/glred
        #\PROGRAM_NAME  
        #\PROGRAM_VERSION 
        #\PROVIDER  
        #\DESCRIPTION   
        #\SCRIPT_SYSTEM   
        #\SCRIPT_VERSION  
        #\END PROGRAM 
        #
        #\BEGIN TS_FORMAT
        #\ID  eseas_env
        #\NUMBER_OF_COLUMNS 14
        #\NAMES_OF_COLUMNS date year x y z sigma_x sigma_y sigma_z east north height sigma_east sigma_north sigma_height 
        #\UNITS_OF_COLUMNS yyyy-mm-dd yr mm mm mm mm mm mm mm mm mm mm mm mm
        #\MISSING_VALUES ????-??-?? 9999.99999 100000.0 10000.0 100000.0 10000.0 100000.0 10000.0  100000.0 10000.0 100000.0 10000.0 100000.0 10000.0 
        #\FORMAT
        #\SAMPLING 
        #\END TS_FORMAT
        #
        #\BEGIN REF_FRAME 
        #\ID ITRF2005
        #\REF_SYSTEM ITRS 
        #\REF_FRAME ITRF2005 
        #\DESCRIPTION  
        #\END REF_FRAME 
        #
        #\BEGIN RECORD 
        #\ID day values
        #\NUMBER_OF_COLUMNS 14
        #\NAMES_OF_COLUMNS date year x y z sigma_x sigma_y sigma_z east north height sigma_east sigma_north sigma_height 
        #\UNITS_OF_COLUMNS yyyy-mm-dd yr mm mm mm mm mm mm mm mm mm mm mm mm
        #\REF_COORDINATE.ID  svalbard_ref
        #\REF_FRAME.ID ITRF20005
        #\DATA 
        self._parse_header()
        
        # Parse data
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----
        # 2000-05-01  2000.3299   157.26  -155.12   -85.49   2.60   1.10   3.60     0.00     0.00     0.00   1.05  
        # 2000-05-02  2000.3326   156.72  -154.76   -88.18   2.20   0.90   3.10     0.44    -1.00    -2.54   0.88  
        # 2000-05-03  2000.3354   157.13  -154.31   -85.98   2.10   0.90   2.90     0.83    -0.24    -0.43   0.86  
        # 2000-05-04  2000.3381   156.47  -153.98   -86.76   2.00   0.90   2.80     1.24    -0.14    -1.41   0.84         
        return dict(
            comments="\\",
            names=self.meta["names_of_columns"],
            dtype=self.dtype,
            autostrip=True,
        )


    def _parse_header(self) -> None:
        """Parse header
        """
        # TODO: better solution for parsing of NTS header
        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            
            for line in fid: 

                if line.startswith("\\BEGIN RECORD"):
                    break
                
                if line.startswith("\\NAMES_OF_COLUMNS"):
                    
                    # TODO "self.dtype" is a workaround. The problem is that setup_parser is called two times in _parser.parse
                    # and _parser_line.read_data function. Better would be to skip self.setup_parser in _parser.parse. What
                    # would be consequences?
                    if self.dtype:
                        break
                    
                    self.meta["names_of_columns"] = line.split()[1:]
                    for name in self.meta["names_of_columns"]:
                        self.dtype.append("U10" if name == "date" else "f8")
                        
                if line.startswith("\\UNITS_OF_COLUMNS"):
                    self.meta["units_of_columns"] = line.split()[1:]
                

    def as_dataset(self, ref_pos: Union[np.ndarray, List[float]] = [0.0, 0.0, 0.0]) -> "Dataset":
        """Return the parsed data as a Dataset

        Args:
            ref_pos: Reference position given in terrestrial reference system and meters

        Returns:
            Midgard Dataset where timeseries data are stored with following fields:

    
           | Field               | Type              | Description                                                    |
           |---------------------|-------------------|----------------------------------------------------------------|
           | pos                 | PositionDelta     | Position delta object referred to a reference position         |
           | pos_sigma_east      | numpy.array       | Standard deviation of east position                            |
           | pos_sigma_north     | numpy.array       | Standard deviation of north position                           |
           | pos_sigma_up        | numpy.array       | Standard deviation of up position                              |
           | time                | Time              | Parameter time given as TimeTable object                       |
        """

        # Initialize dataset
        dset = dataset.Dataset()
        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(self.data["year"])
        dset.meta.update(self.meta)

        # Add position
        unit = self.meta["units_of_columns"][self.meta["names_of_columns"].index("east")]
        ref_pos = Position(np.repeat(np.array([ref_pos]), dset.num_obs, axis=0), system="trs")
        dset.add_position_delta(
            name="pos",
            val=np.stack((
                    self.data["east"] * Unit(unit, "meter"), 
                    self.data["north"] * Unit(unit, "meter"), 
                    self.data["height"] * Unit(unit, "meter"),
            ), axis=1),
            system="enu",
            ref_pos=ref_pos,
        )

        # TODO: sigma functionality has to be improved: pos_sigma.enu.east, pos_sigma.trs.x
        ## Add position sigma
        # sigma = np.stack((self.data["sigma_east"], self.data["sigma_north"], self.data["sigma_height"]), axis=1)
        # dset.add_sigma(name="pos_sigma", val=dset.pos.val, sigma=sigma, unit="meter")
        sigma_unit = self.meta["units_of_columns"][self.meta["names_of_columns"].index("sigma_east")]
        dset.add_float(
                name="pos_sigma_east", 
                val=self.data["sigma_east"] * Unit(sigma_unit, "meter"), 
                unit="meter",
        )
        dset.add_float(
                name="pos_sigma_north", 
                val=self.data["sigma_north"]  * Unit(sigma_unit, "meter"), 
                unit="meter",
        )
        dset.add_float(
                name="pos_sigma_up", 
                val=self.data["sigma_height"]  * Unit(sigma_unit, "meter"), 
                unit="meter",
        )

        # Add time
        dset.add_time(
            name="time", val=self.data["year"], scale="utc", fmt="decimalyear", write_level="operational"
        )

        return dset
