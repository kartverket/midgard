"""A parser for reading timeseries files in TSVIEW format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='timeseries_tsview', file_path='stas.enu')
    data = p.as_dict()

Description:
------------

Reads data from files timeseries files in TSVIEW (east, north, up) format

"""
# Standard library imports
from typing import Any, Dict, List, Union

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
    | mjd                  | Modified Julian Date.                                                                |
    | east                 | East coordinate in [mm].                                                             |
    | north                | North coordinate in [mm].                                                            |
    | up                   | Up coordinate in [mm].                                                               |

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

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8-
        # 51055.5       -130.33   -151.74     -2.17
        # 51058.5       -130.37   -152.28     -5.10
        # 51059.5       -131.43   -152.52     -3.75
        return dict(
            skip_header=1,
            names=("mjd", "east", "north", "up"),
            delimiter=(7, 14, 10, 10),
            dtype=("f8", "f8", "f8", "f8"),
            autostrip=True,
        )

    def as_dataset(self, ref_pos: Union[np.ndarray, List[float]]) -> "Dataset":
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
        dset.num_obs = len(self.data["mjd"])

        # Add position
        ref_pos = position.Position(np.repeat(np.array([ref_pos]), dset.num_obs, axis=0), system="trs")
        dset.add_position_delta(
            name="pos",
            val=np.stack((self.data["east"], self.data["north"], self.data["up"]), axis=1) * Unit.millimeter2meter,
            system="enu",
            ref_pos=ref_pos,
        )

        # Add time
        dset.add_time(name="time", val=self.data["mjd"], scale="utc", fmt="mjd", write_level="operational")

        return dset
