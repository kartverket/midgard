"""A parser for reading NASA JPL GipsyX timeseries file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_series', file_path='NYA1.series')
    data = p.as_dict()

Description:
------------

Reads data from files in GipsyX timeseries format.

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
from midgard.parsers import LineParser


@plugins.register
class GipsyxSeriesParser(LineParser):
    """A parser for reading GipsyX timeseries file

    Following **data** are available after reading GipsyX residual output file:


    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | corr_en              | Correlation East-North.                                                              |
    | corr_ev              | Correlation East-Vertical.                                                           |
    | corr_nv              | Correlation North-Vertical.                                                          |
    | day                  | Day                                                                                  |
    | decimalyear          | Date in unit year.                                                                   |
    | east                 | East coordinate in [m].                                                              |
    | east_sigma           | Standard devication of east coordinate in [m].                                       |
    | hour                 | Hour                                                                                 |
    | minute               | Minute                                                                               |
    | month                | Month                                                                                |
    | north                | North coordinate in [m].                                                             |
    | north_sigma          | Standard devication of north coordinate in [m].                                      |
    | second               | Second                                                                               |
    | time_past_j2000      | Time given in GPS seconds past J2000, whereby GipsyX uses following definition:      |
    |                      | J2000 is continuous seconds past Jan. 1, 2000 11:59:47 UTC.                          |
    | vertical             | Vertical coordinate in [m].                                                          |
    | vertical_sigma       | Standard devication of vertical coordinate in [m].                                   |
    | year                 | Year                                                                                 |

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

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----
        # 1997.41546410        -0.129049        -0.184509        -0.104704         0.000704         0.000885         0.004622         0.057219         0.479851         0.539105     -81561750.00  1997  6  1 11 57 30
        # 1997.41820195        -0.131761        -0.188031        -0.106736         0.000698         0.000846         0.004422         0.010166         0.229144         0.489866     -81475350.00  1997  6  2 11 57 30
        # 1997.42093981        -0.128925        -0.186854        -0.109757         0.000743         0.000918         0.004718         0.031938        -0.126787         0.490283     -81388950.00  1997  6  3 11 57 30
        return dict(
            skip_header=1,
            names=(
                "decimalyear",
                "east",
                "north",
                "vertical",
                "east_sigma",
                "north_sigma",
                "vertical_sigma",
                "corr_en",
                "corr_ev",
                "corr_nv",
                "time_past_j2000",
                "year",
                "month",
                "day",
                "hour",
                "minute",
                "second",
            ),
            delimiter=(13, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 6, 3, 3, 3, 3, 3),
            dtype=(
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
                "f8",
            ),
            autostrip=True,
        )

    #
    # WRITE DATA
    #
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
        dset.num_obs = len(self.data["decimalyear"])
        dset.meta.update(self.meta)

        # Add position
        ref_pos = position.Position(np.repeat(np.array([ref_pos]), dset.num_obs, axis=0), system="trs")
        dset.add_position_delta(
            name="pos",
            val=np.stack((self.data["east"], self.data["north"], self.data["vertical"]), axis=1),
            system="enu",
            ref_pos=ref_pos,
        )

        # TODO: sigma functionality has to be improved: pos_sigma.enu.east, pos_sigma.trs.x
        ## Add position sigma
        # sigma = np.stack((self.data["east_sigma"], self.data["north_sigma"], self.data["vertical_sigma"]), axis=1)
        # dset.add_sigma(name="pos_sigma", val=dset.pos.val, sigma=sigma, unit="meter")
        dset.add_float(name="pos_sigma_east", val=self.data["east_sigma"], unit="meter")
        dset.add_float(name="pos_sigma_north", val=self.data["north_sigma"], unit="meter")
        dset.add_float(name="pos_sigma_up", val=self.data["vertical_sigma"], unit="meter")

        # Add time
        dset.add_time(
            name="time", val=self.data["decimalyear"], scale="utc", fmt="decimalyear", write_level="operational"
        )

        return dset
