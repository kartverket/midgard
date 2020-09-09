"""A parser for reading timeseries files in RESIDUALS format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='timeseries_residuals', file_path='stas.residuals')
    data = p.as_dict()

Description:
------------

Reads data from files timeseries files in RESIDUALS format

"""
# Standard library imports
from typing import Any, Dict

# Midgard imports
from midgard.data import dataset
from midgard.dev import log
from midgard.dev import plugins
from midgard.math.unit import Unit
from midgard.parsers import LineParser


@plugins.register
class TimeseriesEnvParser(LineParser):
    """A parser for reading timeseries files in RESIDUALS format

    Following **data** are available after reading timeseries RESIDUALS file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | year                 | Date in unit year.                                                                   |
    | observed             | Observations in [mm].                                                                |
    | residual             | Residuals in [mm].                                                                   |
    | modeled              | Modeled values in  [mm].                                                             |
    | modeled_sigma        | Standard devication of modeled values in [mm].                                       |

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
        #  2010.0356              0.00       -0.39              0.39        1.00
        #  2010.0383              1.09        0.66              0.43        1.00
        #  2010.0411             -1.27       -1.74              0.47        1.00
        #  2010.0438             -2.65       -3.16              0.51        1.00
        return dict(
            skip_header=1,
            names=("year", "observed", "residual", "modeled", "modeled_sigma"),
            delimiter=(10, 18, 12, 18, 12),
            dtype=("f8", "f8", "f8", "f8", "f8"),
            autostrip=True,
        )

    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            A dataset containing the data.
        """

        # Initialize dataset
        dset = dataset.Dataset()
        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(self.data["year"])

        # Add float fields
        for field in ["observed", "residual", "modeled"]:
            dset.add_float(name=field, val=self.data[field] * Unit.millimeter2meter, unit="meter")
        
        # Add position sigma
        dset.add_sigma(
                name="modeled_sigma", 
                val=dset.modeled, 
                sigma=self.data["modeled_sigma"] * Unit.millimeter2meter, 
                unit="meter",
        )

        # Add time
        dset.add_time(name="time", val=self.data["year"], scale="utc", fmt="decimalyear", write_level="operational")

        return dset
