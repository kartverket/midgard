"""A parser for reading coordinate comparison in Bernese OUT format


Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='bernese_compar_out', file_path='COMP211670.OUT')
    data = p.as_dict()

Description:
------------

Reads coordinate comparison data from files in OUT format

"""
# Standard library imports
from datetime import datetime
import itertools
from typing import Any, Dict, Iterable, Tuple

# Midgard imports
from midgard.data import dataset
from midgard.dev import log
from midgard.dev import plugins
from midgard.math.unit import Unit
from midgard.parsers import ChainParser, ParserDef


@plugins.register
class BerneseComparOutParser(ChainParser):
    """A parser for reading coordinate comparison in Bernese OUT format


    The parsed data are saved in variable **data** as a dictionay with 4-digit station name as key. The station
    related data are saved in a dictionary with following keys:

    | Key                   | Type        |Description                                                           |
    |-----------------------|-------------|----------------------------------------------------------------------|
    | coord_comp_east       | List[float] | List with daily station coordinate comparison results for East       |
    |                       |             | component in [m]                                                     |
    | coord_comp_north      | List[float] | List with daily station coordinate comparison results for North      |
    |                       |             | component in [m]                                                     |
    | coord_comp_up         | List[float] | List with daily station coordinate comparison results for Up         |
    |                       |             | component in [m]                                                     |
    | coord_comp_rms_east   | float       | List with daily station coordinate comparison results for East       |
    |                       |             | component in [m]                                                     |
    | coord_comp_rms_north  | float       | List with daily station coordinate comparison results for North      |
    |                       |             | component in [m]                                                     |
    | coord_comp_rms_up     | float       | List with daily station coordinate comparison results for Up         |
    |                       |             | component in [m]                                                     |
    | pos_mean_x            | float       | X-coordinate of mean station coordinate position in [m]              |
    | pos_mean_x_rms1       | float       | RMS1 of X-coordinate of mean station coordinate position in [m]      |
    | pos_mean_x_rms2       | float       | RMS2 of X-coordinate of mean station coordinate position in [m]      |
    | pos_mean_y            | float       | Y-coordinate of mean station coordinate position in [m]              |
    | pos_mean_y_rms1       | float       | RMS1 of Y-coordinate of mean station coordinate position in [m]      |
    | pos_mean_y_rms2       | float       | RMS2 of Y-coordinate of mean station coordinate position in [m]      |
    | pos_mean_z            | float       | Z-coordinate of mean station coordinate position in [m]              |
    | pos_mean_z_rms1       | float       | RMS1 of Z-coordinate of mean station coordinate position in [m]      |
    | pos_mean_z_rms2       | float       | RMS2 of Z-coordinate of mean station coordinate position in [m]      |

    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | num_coord_files      | Number of coordinate files used for analysis                                         |
    | time                 | Date of analysis session                                                             |
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |
    """


    def __init__(self, *args: Tuple[Any], **kwargs: Dict[Any, Any]):
        """
        Args:
            args:   Parameters without keyword.
            kargs:  Keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.fields = list()  # Save field names, which are read. Needed by generating of dataset.

            
    def setup_parser(self) -> Iterable[ParserDef]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """


        # Skip lines until 'Verification of fiducial stations' section
        skip_lines_parser = ParserDef(
            end_marker=lambda line, _ln, _n: (
                "LIST OF COORDINATE FILES" in line            # Start of num_coord_files_parser
                or "COMPARISON OF COORDINATES" in line        # Start of coord_comparison_parser
            ),
            label= lambda line, _ln: line,
            parser_def = {},
        )


        #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
        #
        # ================================================================================
        # Bernese GNSS Software, Version 5.2
        # --------------------------------------------------------------------------------
        # Program        : COMPAR
        # Purpose        : Coordinate comparison
        # --------------------------------------------------------------------------------
        # Campaign       : ${P}/PGS
        # Default session: 1690 year 2021
        # Date           : 19-Jun-2021 13:13:07
        # User name      : satref
        # ================================================================================
        #
        time_parser = ParserDef(
            end_marker=lambda line, _ln, _n: line.strip().startswith("User name"),
            label=lambda line, _ln: line.strip().startswith("Default session"),
            parser_def={
                True: {   
                    "parser": self._parse_time,
                    "fields": {
                        "time":   (0, None),
                    },
                },
            },
        )
       

        #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
        #
        # -------------------------------------------------------------------------------------------
        # File  Coordinate files                 
        # -------------------------------------------------------------------------------------------
        #    1  ${P}/PGS/STA/F1_211600.CRD       
        #    2  ${P}/PGS/STA/F1_211610.CRD       
        #    3  ${P}/PGS/STA/F1_211620.CRD       
        #    4  ${P}/PGS/STA/F1_211630.CRD       
        #    5  ${P}/PGS/STA/F1_211640.CRD       
        #    6  ${P}/PGS/STA/F1_211650.CRD       
        #    7  ${P}/PGS/STA/F1_211660.CRD       
        # -------------------------------------------------------------------------------------------
        #
        #
        # -------------------------------------------------------------------------------------------
        # LIST OF COORDINATE FILES
        # -------------------------------------------------------------------------------------------
        #
        # NUMBER OF COORDINATE FILES:     7
        num_coord_files_parser = ParserDef(
            end_marker=lambda line, _ln, _n: line.startswith("1"),
            label=lambda line, _ln: line.strip().startswith("NUMBER OF COORDINATE FILES"),
            parser_def={
                True: {  
                    "parser": self._parse_num_coord_files,
                    "strip": "",
                    "fields": {
                        "num_coord_files":    (0, None),
                    },
                },
            },
        )

        #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
        #
        # COMPARISON OF COORDINATES (IN NORTH, EAST, AND HEIGHT COMPONENT)
        # EPOCH FOR COMPARISON: AS IN COORDINATE FI
        # RMS: UNWEIGHTED RMS OF THE ESTIMATION OF ONE COORDINATE COMPONENT IN MM
        # ---------------------------------------------------------------------------------
        #
        # NUM  STATION         #FIL C   RMS     1     2     3     4     5     6     7
        # ---------------------------------------------------------------------------------
        #   2  AASC              7  N   1.21  -1.85 -0.41  0.90 -1.27  0.67  1.39  0.56
        #                           E   0.98   1.50 -1.02  0.47  0.51 -0.78 -1.11  0.42
        #                           U   3.09   0.54  5.33 -0.23 -3.92  0.64 -3.41  1.04
        #
        #   3  ADAC              7  N   1.76  -1.80 -1.47  0.88  3.25  0.60 -1.24 -0.23
        #                           E   0.82   0.02 -0.20  0.65 -0.84  1.47 -0.37 -0.74
        #                           U   9.21  -1.14  5.65 17.49 -0.76 -9.54 -3.61 -8.09
        #
        #  72  ENON              5  N   5.03        -7.11 -1.71 -0.84        5.30  4.37
        #                           E   1.85         0.78  0.75  2.13       -2.61 -1.06
        #                           U   6.34         8.82  2.17  1.37       -6.60 -5.76
        #
        #  33  BIRK              1  N   0.00                           0.00
        #                           E   0.00                           0.00
        #                           U   0.00                           0.00
        coord_comparison_parser = ParserDef(
            end_marker=lambda line, _ln, _n: line.startswith("1"),
            label=lambda line, _ln: (
                len(line) > 27                   # Length of line has to be larger than 27 characters
                and line[27] in ["N", "E", "U"]  # Coordinate flag ('N', 'E' or 'U')
                and line[31].isnumeric()         # RMS
            ),
            parser_def={
                True: {  
                    "parser": self._parse_coord_comparison,
                    "strip": "",
                    "fields": {
                        "station":       (6, 10),
                        "num_files":    (11, 25),
                        "flag_coord":   (26, 28),
                        "rms":          (29, 35),
                        "values":       (36, None),
                    },
                },
            },
        )


        #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----
        #
        # MEAN VALUES OF GEOCENTRIC X,Y,Z - COORDINATES
        # RMS1: RMS OF UNWEIGHTED AVERAGE OF EACH COORDINATE COMPONENT
        # RMS2: FORMAL ACCURACY OF EACH COORDINATE COMPONENT FROM COMBINED SOLUTION USING EQUAL WEIGHTS
        # ----------------------------------------------------------------------------------------------------------------------------
        #
        # NUM  STATION         #FIL FLG         X (M)      RMS1   RMS2          Y (M)      RMS1   RMS2        Z (M)     RMS1    RMS2 
        # ----------------------------------------------------------------------------------------------------------------------------
        #
        #   2  AASC               7  M    3172870.21703 0.00072 0.00144   604208.68041 0.00041 0.00144  5481574.63290 0.00101 0.00144
        #   3  ADAC               7  M    1916240.20525 0.00114 0.00144   963577.13113 0.00066 0.00144  5986596.69558 0.00330 0.00144
        coord_mean_parser = ParserDef(
            end_marker=lambda line, _ln, _n: line.startswith(">>> CPU"),
            label=lambda line, _ln: (
                len(line) > 100                     # Length of line has to be larger than 100 characters
                and line[0:4].strip().isnumeric()   # 1st column is a number
                and line[6:10].isalnum()            # Station name
            ), 
            parser_def={
                True: {  
                    "parser": self._parse_line,
                    "fields": {
                        "station":             (6, 10),
                        "num_files":          (12, 26),
                        "flag":               (27, 29),
                        "pos_mean_x":         (30, 46),
                        "pos_mean_x_rms1":    (47, 54),
                        "pos_mean_x_rms2":    (55, 62),
                        "pos_mean_y":         (62, 77),
                        "pos_mean_y_rms1":    (78, 85),
                        "pos_mean_y_rms2":    (86, 93),
                        "pos_mean_z":        (94, 108),
                        "pos_mean_z_rms1":  (109, 116),
                        "pos_mean_z_rms2":  (117, 124),
                    },
                },
            },
        )


        return itertools.chain([
            time_parser,
            skip_lines_parser, 
            num_coord_files_parser, 
            skip_lines_parser, 
            coord_comparison_parser,
            coord_mean_parser,
        ])
  

    #
    # PARSERS
    #
    def _parse_coord_comparison(self, line: Dict[str, str], cache: Dict[str, Any]) -> None:
        """Parse station coordinate comparison table
        """

        if line["station"].strip().lower():
            cache["station"] = line["station"].strip().lower()

        station = cache["station"]
        self.data.setdefault(station, dict())

        coord_def = {
            "N": "north",
            "E": "east",
            "U": "up",
        }
        coord_key = coord_def[line['flag_coord'].strip()]

        self.data[station][f"coord_comp_rms_{coord_key}"] = float(line["rms"]) * Unit.millimeter2meter

        if not f"coord_comp_rms_{coord_key}" in self.fields:
            self.fields.append(f"coord_comp_rms_{coord_key}")

        # Parse values line
        #----+----1----+----2----+----3----+----4----+-----
        #   1.21  -1.85 -0.41  0.90 -1.27  0.67  1.39  0.56
        #   5.03        -7.11 -1.71 -0.84        5.30  4.37
        #   0.00                           0.00
        if not "num_coord_files" in self.meta:
            log.warn("Number of coordinate files are unknown. Daily comparison values can not be read.")
            return

        len_values = self.meta["num_coord_files"] * 6  # length of line depends on number of files
        line_values = line["values"].ljust(len_values)
        values = [line_values[i:i+6] for i in range(0, len_values, 6)]

        for idx, value in enumerate(values):
            value = float("inf") if value.strip() == "******" else value.strip()
            if value:
                values[idx] = float(value) * Unit.millimeter2meter
            else:
                values[idx] = float('nan')

        self.data[station][f"coord_comp_{coord_key}"] = values

        if not f"coord_comp_{coord_key}" in self.fields:
            self.fields.append(f"coord_comp_{coord_key}")


    def _parse_time(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse date of analysis session
        """
        # Example to parse for getting date:
        #
        # Default session: 1690 year 2021
        #
        session, year = line["time"].split(":")[1].split("year")
        self.meta["time"] = datetime.strptime(session.strip()[:-1] + year.strip(), "%j%Y")


    def _parse_line(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse line
        """
        station = line["station"].lower()
        self.data.setdefault(station, dict())

        skip_fields = ["flag", "num_files", "station"]

        for key, value in line.items(): 
            if key in skip_fields:
                continue

            if not key in self.fields:
                self.fields.append(key)

            self.data[station][key] = float(value)


    def _parse_num_coord_files(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse number of coordinate files
        """
        # Example to parse for getting number of coordinate files:
        #
        # NUMBER OF COORDINATE FILES:     7
        #
        self.meta["num_coord_files"] = int(line["num_coord_files"].split(":")[1])



    #
    # GET DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            Midgard Dataset where station coordinates and belonging information are stored with following fields:

       |  Field                  | Type          | Description                                                       |
       |-------------------------|---------------|-------------------------------------------------------------------|
       | coord_comp_east_day<x>  | numpy.ndarray | Station coordinate comparison results for East component in [m]   |
       |                         |               | for day X (X=[1|2|...|7])                                         |
       | coord_comp_north_day<x> | numpy.ndarray | Station coordinate comparison results for North component in [m]  |
       |                         |               | for day X (X=[1|2|...|7])                                         |
       | coord_comp_up_day<x>    | numpy.ndarray | Station coordinate comparison results for Up component in [m]     |
       |                         |               | for day X (X=[1|2|...|7])                                         |
       | coord_comp_rms_east     | numpy.ndarray | List with daily station coordinate comparison results for East    |
       |                         |               | component in [m]                                                  |
       | coord_comp_rms_north    | numpy.ndarray | List with daily station coordinate comparison results for North   |
       |                         |               | component in [m]                                                  |
       | coord_comp_rms_up       | numpy.ndarray | List with daily station coordinate comparison results for Up      |
       |                         |               | component in [m]                                                  |
       | pos_mean_x              | numpy.ndarray | X-coordinate of mean station coordinate position in [m]           |
       | pos_mean_x_rms1         | numpy.ndarray | RMS1 of X-coordinate of mean station coordinate position in [m]   |
       | pos_mean_x_rms2         | numpy.ndarray | RMS2 of X-coordinate of mean station coordinate position in [m]   |
       | pos_mean_y              | numpy.ndarray | Y-coordinate of mean station coordinate position in [m]           |
       | pos_mean_y_rms1         | numpy.ndarray | RMS1 of Y-coordinate of mean station coordinate position in [m]   |
       | pos_mean_y_rms2         | numpy.ndarray | RMS2 of Y-coordinate of mean station coordinate position in [m]   |
       | pos_mean_z              | numpy.ndarray | Z-coordinate of mean station coordinate position in [m]           |
       | pos_mean_z_rms1         | numpy.ndarray | RMS1 of Z-coordinate of mean station coordinate position in [m]   |
       | pos_mean_z_rms2         | numpy.ndarray | RMS2 of Z-coordinate of mean station coordinate position in [m]   |
       | station                 | numpy.ndarray | Station names                                                     |
       | time                    | TimeTable     | Date of analysis session                                          |

            and following Dataset `meta` data:

       |  Entry              | Type  | Description                                                                    |
       |---------------------|-------|--------------------------------------------------------------------------------|
       | num_coord_files     | int   | Number of coordinate files used for analysis                                   | 
       | \__data_path__      | str   | File path                                                                      |
        """
        data = dict()
             
        # Generate dataset
        dset = dataset.Dataset(num_obs=len(self.data.keys()))
        dset.meta = self.meta.copy()

        # Remove unnecessary fields in meta
        for key in ["__parser_name__"]:
            del dset.meta[key]

        # Prepare data for adding to dataset
        for sta in sorted(self.data.keys()):
            for field in self.fields:

                if field in ["coord_comp_east", "coord_comp_north", "coord_comp_up"]:
                    for idx in range(0, self.meta["num_coord_files"]):
                        if field in self.data[sta]: 
                            data.setdefault(f"{field}_day{idx+1}", list()).append(self.data[sta][field][idx])
                        else:
                            data.setdefault(f"{field}_day{idx+1}", list()).append(float('nan'))
                    continue

                if field in self.data[sta]:
                    data.setdefault(field, list()).append(self.data[sta][field])
                else:
                    # Field does not exist for station 'sta', therefore it is initialized with NaN.
                    data.setdefault(field, list()).append(float('nan'))

        # Add fields to dataset
        dset.add_text("station", val=sorted(self.data.keys()))

        for field in data:
            dset.add_float(field, val=data[field], unit="meter")

        dset.add_time(
                "time",
                val=[dset.meta["time"] for ii in range(0, dset.num_obs)], 
                scale="utc", 
                fmt="datetime",
        )
                
        return dset
