"""A parser for reading Bernese CRD file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnss_bernese_crd', file_path='W20216.CRD')
    data = p.as_dict()

Description:
------------

Reads data from files in Bernese CRD format.

"""
# Standard library imports
from typing import Any, Dict

# Midgard imports
from midgard.parsers import LineParser
from midgard.dev import plugins


@plugins.register
class GnssCrdParser(LineParser):
    """A parser for reading Bernese CRD file

    Following **data** are available after reading Bernese CRD file:

    | Parameter           | Description                                                                           |
    |---------------------|---------------------------------------------------------------------------------------|
    | num                 | Number of station coordinate solution                                                 |
    | station             | 4-digit station identifier                                                            |
    | domes               | Domes number                                                                          |
    | gpssec              | Seconds of GPS week                                                                   |
    | pos_x               | X-coordinate of station position                                                      |
    | pos_y               | Y-coordinate of station position                                                      |
    | pos_z               | Z-coordinate of station position                                                      |
    | flag                | Flag                                                                                  |

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

        # 20216 Week solution coordinates and sinex                        23-OCT-18 07:05
        # --------------------------------------------------------------------------------
        # LOCAL GEODETIC DATUM: IGS14             EPOCH: 2018-10-03 12:00:00
        #
        # NUM  STATION NAME           X (M)          Y (M)          Z (M)     FLAG
        #
        #   1  0ABI              2233557.47676   761080.39008  5906186.08412    A
        #   2  AASC              3172870.25685   604208.64396  5481574.60291    A
        #   3  ABMF 97103M001    2919785.71395 -5383745.04971  1774604.71351
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8--
        return dict(
            autostrip=True,
            comments="#",
            names=("num", "station", "domes", "pos_x", "pos_y", "pos_z", "flag"),
            delimiter=(3, 6, 10, 17, 15, 15, 5),
            dtype=("f8", "U4", "U10", "f8", "f8", "f8", "U1"),
            skip_header=6,
        )

    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        """Generate dictionary with station identifier as keys

        Returns:
            Dictionary with station identifiers as keys.
        """
        dict_ = dict()
        for idx, sta in enumerate(self.data["station"]):
            dict_.update(
                {
                    sta.lower(): {
                        "num": self.data["num"][idx],
                        "domes": self.data["domes"][idx],
                        "pos_x": self.data["pos_x"][idx],
                        "pos_y": self.data["pos_y"][idx],
                        "pos_z": self.data["pos_z"][idx],
                        "flag": self.data["flag"][idx],
                    }
                }
            )

        return dict_
