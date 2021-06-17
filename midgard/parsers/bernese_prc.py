"""A parser for reading protocol file in Bernese PRC format


Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='bernese_prc', file_path='RES211670.PRC')
    data = p.as_dict()

Description:
------------

Reads data from files in PRC format

"""
# Standard library imports
from datetime import datetime
import itertools
from textwrap import wrap
from typing import Any, Callable, Dict, Iterable, List

# Midgard imports
from midgard.data import dataset
from midgard.dev import plugins
from midgard.files import files
from midgard.math.unit import Unit
from midgard.parsers import ChainParser, ParserDef


@plugins.register
class BernesePrcPaser(ChainParser):
    """A parser for reading protocol file in Bernese PRC format


    Following **data** can be available after reading protocol file in Bernese PRC format:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | TODO                 |                                                                                      |

    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | TODO                 |                                                                                      |
    | \__data_path__       | File path                                                                            |
    | \__params__          | np.genfromtxt parameters                                                             |
    | \__parser_name__     | Parser name                                                                          |
    """
    

        
    def setup_parser(self) -> Iterable[ParserDef]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """


        # Skip lines until 'Verification of fiducial stations' section
        skip_lines_parser = ParserDef(
            end_marker=lambda line, _ln, _n: (
                "Verification of fiducial stations" in line                                # Start of residuals_parser
                or "PART 9: SLIDING 7-SESSION COMPARISON OF STATION COORDINATES" in line   # Start of repeatability_parser
                or "COMPARISON OF COORDINATES" in line                                     # Start of coord_comp_parser
            ),
            label= lambda line, _ln: line,
            parser_def = {},
        )

        
        #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
        #
        # RNX2SNX_211660: Verification of fiducial stations
        # -------------------------------------------------------------------------------
        #
        #
        # FILE 1: APR211660.CRD: EXTRAPOLATE                                             
        # FILE 2: F1_211660.CRD: RNX2SNX_211660: Final coordinate/troposphere results
        #
        # LOCAL GEODETIC DATUM: IGb14           
        # RESIDUALS IN LOCAL SYSTEM (NORTH, EAST, UP)
        #
        #
        #
        # ---------------------------------------------------------------------
        # | NUM |      NAME        | FLG |     RESIDUALS IN MILLIMETERS   |   |
        # ---------------------------------------------------------------------
        # |     |                  |     |                                |   |
        # |   1 | 0ABI             | P A |      -1.03      3.41     14.57 | M |
        # |   2 | AASC             | P A |       0.01      1.26      4.53 | M |
        # |     |                  |     |                                |   |
        # ---------------------------------------------------------------------
        # |     | RMS / COMPONENT  |     |       2.76      2.65      6.33 |   |
        # |     | MEAN             |     |      -0.00     -0.00     -0.00 |   |
        # |     | MIN              |     |      -5.85     -8.09    -11.93 |   |
        # |     | MAX              |     |       5.35      3.83     10.56 |   |
        # ---------------------------------------------------------------------
        residuals_parser = ParserDef(
            end_marker=lambda line, _ln, _n: line.strip().startswith("========="),
            label=lambda line, _ln: (
                line.strip().startswith("|")       # Line starts with sign "|" 
                and line[2:6].strip().isnumeric()  # 1st column is a number
            ),
            parser_def={
                True: {   
                    "parser": self._parse_line,
                    "fields": {
                        "station":          (9, 26),
                        "flag":            (28, 32),
                        "residual_north":  (34, 44),
                        "residual_east":   (45, 54),
                        "residual_up":     (55, 64),
                    },
                },
            },
        )


        #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
        #
        # RNX2SNX_211660: Coordinate repeatability for verificati
        # -------------------------------------------------------------------------------
        # Total number of stations:   316
        # -------------------------------------------------------------------------------
        #                       Weekday  Repeatability (mm)
        # Station        #Days  0123456     N     E     U
        # -------------------------------------------------------------------------------
        # 0ABI               1        A    0.00  0.00  0.00
        # AASC               7  AAAAAAA    1.21  0.98  3.09
        # -------------------------------------------------------------------------------
        # # Coordinate estimates:  2176    1.38  1.47  5.75
        repeatability_parser = ParserDef(
            end_marker=lambda line, _ln, _n: line.strip().startswith("# Coordinate estimates"),
            label=lambda line, _ln: (
                len(line) > 49           # Length of line has to be larger than 49 characters
                and line[1:4].isalpha()  # Station name
                and line[20].isnumeric() # Number of days
            ),
            parser_def={
                True: {  
                    "parser": self._parse_line,
                    "fields": {
                        "station":                     (1,  5),
                        "num_of_days":                (15, 21),
                        "weekday":                    (22, 30),
                        "repeatability_north":        (31, 38),
                        "repeatability_east":         (39, 44),
                        "repeatability_up":           (45, 50),
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
        #----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8-
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
                and line[6:10].isalpha()            # Station name
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
            skip_lines_parser, 
            residuals_parser, 
            skip_lines_parser, 
            repeatability_parser, 
            skip_lines_parser, 
            coord_comparison_parser,
            coord_mean_parser,
        ])
  

    def _parse_coord_comparison(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse station coordinate comparison table
        """
        station = line["station"].strip()
        self.data.setdefault(station, dict())

        coord_def = {
            "N": "north",
            "E": "east",
            "U": "up",
        }
        coord_key = coord_def[line['flag_coord'].strip()]

        self.data[station][f"coord_comp_rms_{coord_key}"] = line["rms"].strip()
        return

        #+MURKS
        # Parse values line
        #----+----1----+----2----+----3----+----4----+----
        #  -1.85 -0.41  0.90 -1.27  0.67  1.39  0.56
        #   5.03        -7.11 -1.71 -0.84        5.30  4.37
        #   0.00                           0.00
        len_values = int(line["num_files"]) * 6  # length of line depends on number of files
        values = wrap(line["values"].ljust(len_values), 6)

        #TODO: Does not work
        #len_values = int(line["num_files"]) * 6  # length of line depends on number of files
        #line_values = line["values"].ljust(len_values)
        #[line_values[i:i+6] for i in range(0, len_values, 6)]

        for idx, value in enumerate(values):
            if value.strip():
                values[idx] = float(value)
            else:
                values[idx] = None
        #-MURKS


    def _parse_line(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse line
        """
        station = line["station"]
        self.data.setdefault(station, dict())

        skip_fields = ["flag", "num_files", "station", "weekday"]
        unit_millimeter = [
                "repeatability_east", 
                "repeatability_north", 
                "repeatability_up"
                "residual_east", 
                "residual_north", 
                "residual_up",
        ]

        for key, value in line.items(): 
            if key in skip_fields:
                continue

            if key in unit_millimeter:
                self.data[station][key] = float(value) * Unit.millimeter2meter
            else:
                self.data[station][key] = float(value)
        


