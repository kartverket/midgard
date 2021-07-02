"""A parser for reading Bernese CLU file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='bernese_clu', file_path='NOR_NKG.CLU')
    data = p.as_dict()

Description:
------------

Reads data from files in Bernese CLU format.

"""
# Standard library imports
from typing import Any, Dict

# Midgard imports
from midgard.parsers import LineParser
from midgard.dev import plugins


@plugins.register
class BerneseCluParser(LineParser):
    """A parser for reading Bernese CLU file

    Following **data** are available after reading Bernese CLU file:

    | Parameter           | Description                                                                           |
    |---------------------|---------------------------------------------------------------------------------------|
    | station             | 4-digit station identifier                                                            |
    | domes               | Domes number                                                                          |
    | cluster             | Cluster number                                                                        |

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

        # BSW 5.2: NORWAY NKG                                              10-JAN-12 06:07
        # --------------------------------------------------------------------------------
        #
        # STATION NAME      CLU
        # ****************  ***
        # ADAC 10337M001      1 
        # ALES 10336M001      1
        # ANDO 10333M001      1
        # ARGI 10117M002      1
        # BJOC 10339M001      1
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8--
        return dict(
            autostrip=True,
            names=("station", "domes", "cluster"), # white space are used as delimiter by default
            delimiter=(4, 10, 7),
            dtype=("U4", "U9", "f8"),
            skip_header=5,
        )

    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        """Generate dictionary with station identifier as keys

        Returns:
            Dictionary with station identifiers as keys.
        """
        dict_ = dict()
        for idx, sta in enumerate(self.data["station"]):
            if not sta: # Skip empty station name -> TODO: How should this be done with genfromtxt?
                continue
            dict_.update(
                {
                    sta.lower(): {
                        "domes": self.data["domes"][idx],
                        "cluster": self.data["cluster"][idx],
                    }
                }
            )

        return dict_
