"""A parser for reading NASA JPL GipsyX `gdcov` format file

`gdcov` format file includes GipsyX estimates and covariance information. 

NOTE: At the moment this parser can only read station estimate and covariance information, that means STA.X, STA.Y 
      and STA.Z parameters.

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_gdcov', file_path='smoothFinal.gdcov')
    data = p.as_dict()

Description:
------------

Reads data from files in GipsyX `gdcov` format.

"""
# Standard library imports
import itertools
import re
from typing import Any, Callable, Dict, Iterable, List

# External library imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.data.time import Time
from midgard.dev import plugins
from midgard.math.unit import Unit
from midgard.parsers import ChainParser, ParserDef


@plugins.register
class GipsyxGdcovParser(ChainParser):
    """A parser for reading GipsyX `gdcov` format file

    Following **data** are available after reading GipsyX `gdcov` output file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | column               | Column number of correlations                                                        |
    | correlation          | Correlation values                                                                   |
    | parameter            | Parameter name. An arbitrary sequence of letters [A-Z,a-z], digits[0-9], and "."     |
    |                      | without spaces.                                                                      |
    | row                  | Row number of correlations                                                           |
    | station              | Station name.                                                                        |    
    | sigma                | Standard deviation of the parameter.                                                 |
    | time_past_j2000      | Time given in GPS seconds past J2000, whereby GipsyX uses following definition:      |
    |                      | J2000 is continuous seconds past Jan. 1, 2000 11:59:47 UTC.                          |
    | estimate             | Parameter estimate at the given time                                                 |


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
        # Parser estimation part of `gdcov` file

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----
        # 3 PARAMETERS
        # 1 USN3.STA.X 376018350 1.112162030692846e+06 6.422311946865588e-04
        # 2 USN3.STA.Y 376018350 -4.842853530993107e+06 1.555844558128825e-03
        # 3 USN3.STA.Z 376018350 3.985496029611300e+06 1.247592374291492e-03
        # 2 1 -5.741554474985751e-01
        # 3 1 5.007734002791966e-01
        # 3 2 -8.214416655688096e-01
        data_parser = ParserDef(
            end_marker=lambda line, _ln, _n: False,
            end_callback=lambda line: self._parse_correlation,
            label=lambda line, _ln: not re.match("^\d+ \d+", line),
            skip_line=lambda line: "PARAMETERS" in line,
            parser_def={
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+--
                # 1 USN3.STA.X 376018350 1.112162030692846e+06 6.422311946865588e-04
                True: {
                    "parser": self._parse_estimate,
                    "delimiter": " ",
                    "fields": ["_", "name", "time_past_j2000", "estimate", "sigma"],
                },
                # ----+----1----+----2----+---
                # 2 1 -5.741554474985751e-01
                False: {
                    "parser": self._parse_correlation,
                    "delimiter": " ",
                    "fields": ["row", "column", "correlation"],
                },
            },
        )

        return itertools.repeat(data_parser)

    def _parse_estimate(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse estimate lines
        """
        self.data.setdefault("time_past_j2000", list()).append(float(line["time_past_j2000"]))
        self.data.setdefault("estimate", list()).append(float(line["estimate"]))
        self.data.setdefault("sigma", list()).append(float(line["sigma"]))

        station, parameter = line["name"].split(".", maxsplit=1)
        self.data.setdefault("station", list()).append(station)
        self.data.setdefault("parameter", list()).append(parameter)

    def _parse_correlation(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse correlation lines
        """
        self.data.setdefault("row", list()).append(int(line["row"]))
        self.data.setdefault("column", list()).append(int(line["column"]))
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
    def as_dataset(self) -> "Dataset":
        """Store Gipsy time dependent parameter data in a dataset

        Returns:
            Midgard Dataset where time dependent parameter data are stored with following fields:


       | Field               | Type              | Description                                                        |
       |---------------------|-------------------|--------------------------------------------------------------------|
       | correlation_x       | numpy.ndarray     | Correlation for x station coordinate                               |
       | correlation_y       | numpy.ndarray     | Correlation for y station coordinate                               |
       | correlation_z       | numpy.ndarray     | Correlation for z station coordinate                               |
       | sigma_x             | numpy.ndarray     | Standard deviation for x station coordinate                        |
       | sigma_y             | numpy.ndarray     | Standard deviation for y station coordinate                        |
       | sigma_z             | numpy.ndarray     | Standard deviation for z station coordinate                        |
       | site_pos            | Position          | x, y and z station coordinates                                     |
       | station             | numpy.ndarray     | Station name list                                                  |
       | time                | Time              | Parameter time given as TimeTable object                           |
       
       The fields above are given for 'apriori', 'value' and 'sigma' Dataset collections.
        
        """
        idx_x = "STA.X" == self.data["parameter"]
        idx_y = "STA.Y" == self.data["parameter"]
        idx_z = "STA.Z" == self.data["parameter"]
        dset = dataset.Dataset(num_obs=len(self.data["time_past_j2000"][idx_x]))
        dset.meta.update(self.meta)

        # Note: GipsyX uses continuous seconds past Jan. 1, 2000 11:59:47 UTC time format in TDP files. That means,
        #       GipsyX does not follow convention of J2000:
        #           1.01.2000 12:00:00     TT  (TT = GipsyX(t) + 13s)
        #           1.01.2000 11:59:27.816 TAI (TAI = TT - 32.184s)
        #           1.01.2000 11:58:55.816 UTC (UTC = TAI + leap_seconds = TAI - 32s)
        #           1.01.2000 11:59:08.816 GPS (GPS = TAI - 19s)
        #
        #       Therefore Time object initialized with TT time scale has to be corrected about 13 seconds.
        #
        dset.add_time(
            "time",
            val=Time(
                (np.array(self.data["time_past_j2000"][idx_x]) + 13.0) * Unit.second2day + 2451545.0,
                scale="tt",
                fmt="jd",
            ).gps,
        )

        dset.add_text("station", val=self.data["station"][idx_x])
        dset.add_float("sigma_x", val=self.data["sigma"][idx_x], unit="meter")
        dset.add_float("sigma_y", val=self.data["sigma"][idx_y], unit="meter")
        dset.add_float("sigma_z", val=self.data["sigma"][idx_z], unit="meter")
        dset.add_position(
            "site_pos",
            time=dset.time,
            system="trs",
            val=np.vstack(
                (self.data["estimate"][idx_x], self.data["estimate"][idx_y], self.data["estimate"][idx_z])
            ).T,
        )
        # TODO: how to use dset.add_sigma? how to save correlation?
        # tmp = dict()
        # for num_sta, station in enumerate(self.data["station"]):
        #    tmp.setdefault("correlation_x", list()).append()
        #    tmp.setdefault("correlation_y", list()).append()
        #    tmp.setdefault("correlation_z", list()).append()

        #   |1
        #   |2  3
        #   ------
        #    4  5  6
        #    7  8  9 |10
        #   11 12 13 |14 15
        #            --------
        #   16 17 18  19 20 21
        #   22 23 24  25 26 27 |28
        #   29 30 31  32 33 34 |35 36
        #                      -------

        return dset
