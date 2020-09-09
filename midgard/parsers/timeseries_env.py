"""A parser for reading timeseries files in ENV format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='timeseries_env', file_path='stas.env')
    data = p.as_dict()

Description:
------------

Reads data from files timeseries files in ENV (east, north, vertical) format

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
    """A parser for reading timeseries files in ENV format

    Following **data** are available after reading timeseries ENV file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | date                 | Date in format yyMMMdd (e.g. 18MAY10).                                               |
    | year                 | Date in unit year.                                                                   |
    | east                 | East coordinate in [mm].                                                             |
    | east_sigma           | Standard devication of east coordinate in [mm].                                      |
    | north                | North coordinate in [mm].                                                            |
    | north_sigma          | Standard devication of north coordinate in [mm].                                     |
    | vertical             | Vertical coordinate in [mm].                                                         |
    | vertical_sigma       | Standard devication of vertical coordinate in [mm].                                  |

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

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+
        # STAS                    e (mm)      se (mm)       n (mm)      sn (mm)       v (mm)      sv (mm)
        # 14AUG31 2014.6639        33.79         0.53        33.13         0.72         7.95         2.17
        # 14SEP01 2014.6667        35.16         0.53        31.40         0.71         6.09         2.15
        # 14SEP02 2014.6694        33.87         0.53        33.65         0.71         2.46         2.14
        return dict(
            skip_header=1,
            names=("date", "year", "east", "east_sigma", "north", "north_sigma", "vertical", "vertical_sigma"),
            delimiter=(7, 10, 13, 13, 13, 13, 13, 13),
            dtype=("U20", "f8", "f8", "f8", "f8", "f8", "f8", "f8"),
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
        dset.num_obs = len(self.data["date"])

        # Add position
        ref_pos = position.Position(np.repeat(np.array([ref_pos]), dset.num_obs, axis=0), system="trs")
        dset.add_position_delta(
            name="pos",
            val=np.stack((self.data["east"], self.data["north"], self.data["vertical"]), axis=1)
            * Unit.millimeter2meter,
            system="enu",
            ref_pos=ref_pos,
        )

        # Add position sigma
        sigma = np.stack((self.data["east_sigma"], self.data["north_sigma"], self.data["vertical_sigma"]), axis=1)
        dset.add_sigma(name="pos_sigma", val=dset.pos.val, sigma=sigma * Unit.millimeter2meter, unit="meter")

        # Add time
        dset.add_time(name="time", val=self.data["year"], scale="utc", fmt="decimalyear", write_level="operational")

        return dset
