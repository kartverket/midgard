"""A parser for reading Bernese SLR PLT file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='bernese_slr_plt', file_path='SLR_20232580.PLT')
    data = p.as_dict()

Description:
------------

Reads data from files in Bernese PLT format.

"""
# Standard library imports
from typing import Any, Dict

# Midgard imports
from midgard.parsers import LineParser
from midgard.dev import plugins


@plugins.register
class BerneseSlrPltParser(LineParser):
    """A parser for reading Bernese SLR PLT file

    Following **data** are available after reading Bernese PLT file:

    | Parameter          | Description                                                                    |
    |--------------------|--------------------------------------------------------------------------------|
    | station            | 4-digit station identifier                                                     |
    | domes              | domes number, e.g.  50107M001                                                  |
    | sat_prn            | satellite, e.g. E18
    | epoch              | mjd of observation                                                             |
    | residual           | observation residual (mm)                                                      |
    | azi                | azimuth (deg)                                                                  |
    | ele                | elevation (deg)


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

        # Parse data
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8--
        #
        # STATION ID       SAT   EPOCH             RESIDUAL    AZI     ELE
        #                  PRN   (mjd)             (mm)       (deg)   (deg)
        # -----------------------------------------------------------------
        # 7090 50107M001    E21   60127.5023495370      7.7     62.45   55.51
        # 7090 50107M001    E21   60127.5045601852      4.8     60.60   54.67
        # 7090 50107M001    E18   60127.5856944444    -10.6    183.52   65.48

        return dict(
            autostrip=True,
            comments="#",
            names=("station", "domes", "sat_prn", "epoch", "residual", "azi", "ele"),
            delimiter=(5, 10, 7, 19, 9, 10, 8),
            dtype=("U4", "U9", "U3", "f", "f", "f", "f"),
            skip_header=4,
        )

    #
    # GET DICTIONARY
    #
    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        """Generate dictionary with station identifier as keys

        Returns:
            Dictionary with satellite prn numbers as keys.
        """
        dict_ = {}
        for idx, sat_prn in enumerate(self.data["sat_prn"]):
            if sat_prn == "":
                continue  # Ignore empty lines
            for key in ["station", "domes"]:
                dict_.setdefault(sat_prn, {}).setdefault(key, []).append(
                    self.data[key][idx]
                )
            for key in ["epoch", "residual", "azi", "ele"]:
                dict_.setdefault(sat_prn, {}).setdefault(key, []).append(
                    float(self.data[key][idx])
                )
        return dict_
