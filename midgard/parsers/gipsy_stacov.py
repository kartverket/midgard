"""A parser for reading NASA JPL Gipsy `stacov` format file

`stacov` format file includes Gipsy estimates and covariance information. 

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsy_stacov', file_path='stacov_final')
    data = p.as_dict()

Description:
------------

Reads data from files in Gipsy `stacov` format.

"""
# Standard library imports
from datetime import datetime
import itertools
import re
from typing import Any, Callable, Dict, Iterable, List, Union

# External library imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.data.time import Time
from midgard.dev import plugins
from midgard.parsers import ChainParser, ParserDef


@plugins.register
class GipsyStacovParser(ChainParser):
    """A parser for reading Gipsy `stacov` format file

    Following **data** are available after reading Gipsy `stacov` output file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | correlation          | Correlation values                                                                   |
    | correlation_index1   | Correlation index (1st column)                                                       |
    | correlation_index2   | Correlation index (2nd column)                                                       |
    | estimate             | Parameter estimate at the given time                                                 |
    | estimate_index       | Estimate index                                                                       |
    | parameter            | Parameter name. An arbitrary sequence of letters [A-Z,a-z], digits[0-9], and "."     |
    |                      | without spaces.                                                                      |
    | row                  | Row number of correlations                                                           |
    | station              | Station name.                                                                        |    
    | sigma                | Standard deviation of the parameter.                                                 |
    | time_past_j2000      | Time given in GPS seconds past J2000, whereby GipsyX uses following definition:      |
    |                      | J2000 is continuous seconds past Jan. 1, 2000 11:59:47 UTC.                          |



    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |
    """

    def setup_parser(self) -> Iterable[ParserDef]:
        """Set up information needed for the parser

        Returns:
            Iterable of ParserDef's that describe the structure of the file that will be parsed
        """
        # Parser estimation part of `stacov` file

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----
        #    3 PARAMETERS ON 22NOV25.
        #    1  MLGA STA X         0.510513494339477E+07  +-  0.405932080367999E+00
        #    2  MLGA STA Y        -0.403080372901720E+06  +-  0.104684918929456E+00
        #    3  MLGA STA Z         0.378942696768336E+07  +-  0.312113648323525E+00
        #    2     1  -0.332009585488013E+00
        #    3     1   0.957159590610951E+00
        #    3     2  -0.350912604742732E+00
        # MLGA ANTENNA LC    0.0000      0.0000      0.0000    !up north east (m)
        data_parser = ParserDef(
            end_marker=lambda line, _ln, _n: False,
            end_callback=lambda line: self._parse_correlation,
            label=lambda line, _ln: bool(re.match("^\d+\s+[A-Za-z0-9]+ [A-Za-z0-9]+", line.strip())),
            skip_line=lambda line: "PARAMETERS" in line or "ANTENNA" in line or "transformed" in line,
            parser_def={
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----
                #     1  MLGA STA X         0.510513494339477E+07  +-  0.405932080367999E+00
                True: {
                    "parser": self._parse_estimate,
                    "fields": {
                        "estimate_index":   (0, 5),
                        "station": (6, 11),
                        "parameter": (12, 25),
                        "estimate": (26, 47),
                        "sigma": (53, 74),
                    },
                },
                # ----+----1----+----2----+----3----+
                #     2     1  -0.332009585488013E+00
                False: {
                    "parser": self._parse_correlation,
                    "delimiter": "\s+",
                    "strip": " \t\n",
                    "fields": ["correlation_index1", "correlation_index2", "correlation"],
                },
            },
        )

        return itertools.repeat(data_parser)

    def _parse_estimate(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse estimate lines
        """
        self.data.setdefault("estimate_index", list()).append(int(line["estimate_index"]))
        self.data.setdefault("station", list()).append(line["station"])
        self.data.setdefault("parameter", list()).append(line["parameter"])
        self.data.setdefault("estimate", list()).append(float(line["estimate"]))
        self.data.setdefault("sigma", list()).append(float(line["sigma"]))


    def _parse_correlation(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse correlation lines
        """
        self.data.setdefault("correlation_index1", list()).append(int(line["correlation_index1"]))
        self.data.setdefault("correlation_index2", list()).append(int(line["correlation_index2"]))
        self.data.setdefault("correlation", list()).append(float(line["correlation"]))

    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        
        Returns:
            List with postprocessor function calls
        """
        return [self._numpy_array]

    def _numpy_array(self) -> None:
        """Convert data list to numpy_array
        """
        for name in self.data.keys():
            self.data[name] = np.array(self.data[name])

    #
    # GENERATE DATASET
    #
    def as_dataset(self, time: Union[datetime, None] = None) -> "Dataset":
        """Store GipsyX estimates and covariance information in a dataset
        
        Args:
            time: Time (epoch) of station coordinates as Midgard Time object

        Returns:
            Midgard Dataset where time dependent parameter data are stored with following fields:


       | Field                    | Type              | Description                                                   |
       | :----------------------- | :---------------- | :------------------------------------------------------------ |
       | site_pos                 | Position          | x, y and z station coordinates                                |
       | site_pos_xy_correlation  | numpy.ndarray     | Correlation between x and y station coordinate                |
       | site_pos_xz_correlation  | numpy.ndarray     | Correlation between x and z station coordinate                |
       | site_pos_yz_correlation  | numpy.ndarray     | Correlation between y and z station coordinate                |
       | site_pos_x_sigma         | numpy.ndarray     | Standard deviation for x station coordinate                   |
       | site_pos_y_sigma         | numpy.ndarray     | Standard deviation for y station coordinate                   |
       | site_pos_z_sigma         | numpy.ndarray     | Standard deviation for z station coordinate                   |
       | station                  | numpy.ndarray     | Station name list                                             |
       | time                     | Time              | Parameter time given as TimeTable object                      |
       
       The fields above are given for 'apriori', 'value' and 'sigma' Dataset collections.
        
        """
        idx_x = "STA X" == self.data["parameter"]
        idx_y = "STA Y" == self.data["parameter"]
        idx_z = "STA Z" == self.data["parameter"]
        dset = dataset.Dataset(num_obs=len(self.data["station"][idx_x]))
        dset.meta.update(self.meta)
        
        # Note: Time is unknown for STACOV files, therefore in case of time is not given as argument the current date
        #       is used for initializing position field.
        if not time:
            time = Time(datetime.utcnow(), scale="utc", fmt="datetime")
        else:
            time = Time(time, scale="utc", fmt="datetime")
            
        dset.add_time("time", time)

        dset.add_text("station", val=self.data["station"][idx_x])
        dset.add_float("site_pos_x_sigma", val=self.data["sigma"][idx_x], unit="meter")
        dset.add_float("site_pos_y_sigma", val=self.data["sigma"][idx_y], unit="meter")
        dset.add_float("site_pos_z_sigma", val=self.data["sigma"][idx_z], unit="meter")
        dset.add_position(
            "site_pos",
            time=dset.time,
            system="trs",
            val=np.vstack(
                        (self.data["estimate"][idx_x], self.data["estimate"][idx_y], self.data["estimate"][idx_z])
            ).T
        )

        # Extract correlation coefficients of each station coordinate solution
        #   |0          <- idx_xy = 0
        #   |1  2       <- idx_xz = idx_xy + 0 + 1 = 1
        #   ------
        #    3  4  5
        #    6  7  8 |9            <- idx_xy = idx_yz + 1 * 6 + 1 = 9
        #   10 11 12 |13 14        <- idx_xz = idx_xy + 3 + 1 = 13
        #            --------
        #   15 16 17  18 19 20
        #   21 22 23  24 25 26 |27         <- idx_xy = idx_yz + 2 * 6 + 1 = 27
        #   28 29 30  31 32 33 |34 35      <- idx_xz = idx_xy + 6 + 1 = 34
        #                      -------
        #
        #   36 37 38  39 40 41  42 43 44
        #   45 46 47  48 49 50  51 52 53 |54        <- idx_xy = idx_yz + 3 * 6 + 1 = 54
        #   55 56 57  58 59 60  61 62 63 |64 65     <- idx_xz = idx_xy + 9 + 1 = 64
        #                                -------
        #
        #   66 67 68  69 70 71  72 73 74  75  76  77
        #   78 79 80  81 82 83  84 85 86  87  88  89  | 90         <- idx_xy = idx_yz + 4 * 6 + 1 = 90
        #   91 92 93  94 95 96  97 98 99  100 101 102 |103 104     <- idx_xz = idx_xy + 12 + 1 = 103
        #                                               ---------
        #    
        tmp = dict()
        addend = 0
        idx_xy = 0
        for ii in range(0, dset.num_obs):

            idx_xz = idx_xy + addend + 1
            idx_yz = idx_xz + 1
            tmp.setdefault("site_pos_xy_correlation", list()).append(self.data["correlation"][idx_xy])
            tmp.setdefault("site_pos_xz_correlation", list()).append(self.data["correlation"][idx_xz])
            tmp.setdefault("site_pos_yz_correlation", list()).append(self.data["correlation"][idx_yz])
            addend = addend + 3
            idx_xy = idx_yz + (ii + 1) * 6 + 1
            
        # Add correlation coefficient to dataset
        for suffix in ["xy", "xz", "yz"]:
            field = f"site_pos_{suffix}_correlation"
            dset.add_float(field, tmp[field]) # unitless

        return dset
