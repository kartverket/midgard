"""A parser for reading Gipsy summary output file (*.sum)

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsy_sum', file_path='gipsy_sum')
    data = p.as_dict()

Description:
------------

Reads data from files in Gipsy summary output format.

"""

# Standard library import
from datetime import datetime
from typing import Any, Dict

# Midgard imports
from midgard.data import dataset
from midgard.dev import log
from midgard.dev import plugins
from midgard.math.unit import Unit
from midgard.parsers import LineParser


@plugins.register
class GipsySummary(LineParser):
    """A parser for reading Gipsy summary output file (*.sum)

    Gipsy summary file **data** are grouped as follows:

    | Key                   | Description                                                                          |
    |-----------------------|--------------------------------------------------------------------------------------|
    | date                  | Processing date                                                                      |
    | residual              | Dictionary with residual summary information                                         |
    | station               | Station name                                                                         |


    **residual** entries are:

    | Key                   | Description                                                                          |
    |-----------------------|--------------------------------------------------------------------------------------|
    | code_num              | Number of used pseudo-range observations                                             |
    | code_rms              | RMS of residuals from used pseudo-range observations in [m]                          |
    | code_outlier_num      | Number of rejected pseudo-range observations                                         |
    | phase_num             | Number of used phase observations                                                    |
    | phase_rms             | RMS of residuals from used phase observations in [m]                                 |
    | phase_outlier_num     | Number of rejected phase observations                                                |


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

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8----+----+----9----+----0----+----1---
        #    start time         stop time      type  user      postfit sigma npts outliers
        # 
        # 22DEC31 23:59:42   23JAN01 23:54:42   LC   ZIMM      8.1722E-06    2176      3
        # 22DEC31 23:59:42   23JAN01 23:54:42   PC   ZIMM      4.2938E-04    2179      0
        return dict(
            autostrip=True,
            names=("start_time", "stop_time", "type", "station", "residual", "num_obs", "outliers"),
            delimiter=(16, 19, 5, 7, 16, 8, 7),
            dtype=("U16", "U16", "U2", "U4", "f8", "f8", "f8"),
            skip_header=2,
        )


    #
    # GET DICTIONARY
    #
    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        """Generate dictionary with station identifier as keys

        Returns:
            Dictionary with station identifiers as keys.
        """
        dict_ = dict()
        dict_["date"] = datetime.strptime(self.data["stop_time"][0].split()[0], "%y%b%d")
        dict_["station"] = self.data["station"][0].lower()
        dict_.setdefault("residual", dict())

        # Fill residual dictionary
        for idx, type_ in enumerate(self.data["type"]):

            if type_ == "LC":
                dict_["residual"].update(
                    {
                        "phase_num": self.data["num_obs"][idx],
                        "phase_rms": self.data["residual"][idx] * Unit.km2m,
                        "phase_outlier_sum": self.data["outliers"][idx],
                    }
                )
            elif type_ == "PC":
                dict_["residual"].update(
                    {
                        "code_num": self.data["num_obs"][idx],
                        "code_rms": self.data["residual"][idx] * Unit.km2m,
                        "code_outlier_sum": self.data["outliers"][idx],
                    }
                )
            else:
                log.fatal(f"Gipsy summary type {type_} is not defined.")

        return dict_


    #
    # GET DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Gipsy summary results are added to Dataset 'meta' variable. 

        Args:
            dset: Dataset.

        Returns:
            A dataset containing the data.
        """
        dset = dataset.Dataset(num_obs=0)

        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset

        dset.meta["summary"] = self.as_dict()
        return dset
