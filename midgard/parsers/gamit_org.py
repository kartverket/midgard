"""A parser for reading Gamit ORG files

Example:
--------

    from midgard import parsers

    # Parse data
    parser = parsers.parse_file(parser_name="gamit_org", file_path=file_path)

    # Get Dataset with parsed data
    dset = parser.as_dataset()

Description:
------------

Reads the output file of Gamit.

Example header from wich the time information is read from the .org file

---------------------------------------------------------
 GLOBK Ver 5.34, Global solution
---------------------------------------------------------

 Solution commenced with: 2022/ 6/22  0: 0    (2022.4712)
 Solution ended with    : 2022/ 6/22 23:59    (2022.4740)
 Solution refers to     : 2022/ 6/22 11:59    (2022.4726) [Seconds tag  45.000]
 Satellite IC epoch     : 2022/ 6/22 12: 0  0.00


Example lines to be read from the .org file

    REYK_JPS X coordinate  (m)          2587383.93370     -0.01703      0.00446

    REYK_JPS Y coordinate  (m)         -1043033.57942     -0.04451      0.00404

    REYK_JPS Z coordinate  (m)          5716564.17515      0.00474      0.00947
"""

# Standard library imports
import itertools
from typing import Any, Dict, Iterable

# External library imports
from datetime import datetime
import numpy as np

# Midgard imports
from midgard.parsers import ChainParser, ParserDef
from midgard.data import dataset
from midgard.dev import plugins


@plugins.register
class GamitOrgParser(ChainParser):
    """A parser for reading gamit org file

    Attributes:
        data (Dict):                  The (observation) data read from file.
        file_path (Path):             Path to the datafile that will be read.
        meta (Dict):                  Metainformation read from file.
        parser_name (String):         Name of the parser (as needed to call parsers.parse_...).
        system (String):              GNSS identifier.

    Methods:
        as_dataset()                  Return the parsed data as a Midgard Dataset
        parse()                       Parse data
        setup_parser()                Set up information needed for the parser

        _parse_time()                 Parse a line of time information
        _parse_station()              Parse a line of station information
    """

    #
    # PARSERS
    #
    def setup_parser(self) -> Iterable[ParserDef]:
        """Parser defined for reading .org file line by line

        First the header information are read and afterwards the data block.
        """
        header_parser = ParserDef(
            end_marker=lambda line, _ln, nextline: line[0:8] == " Summary",
            label=lambda line, _ln: line[1:19],
            parser_def={
                "Solution refers to": {
                    "parser": self._parse_time,
                    "fields": {
                        "year": (26, 30),
                        "month": (31, 33),
                        "day": (34, 36),
                        "hours": (37, 39),
                        "minutes": (40, 42),
                        "decimaldate": (47, 56),
                    },
                },
            },
        )

        data_parser = ParserDef(
            end_marker=lambda line, _ln, _n: line[0:9] == "IERS  MJD",
            label=lambda line, _ln: line[18:33],
            parser_def={
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8--
                #     1. REYK_JPS X coordinate  (m)          2587383.93370     -0.01703      0.00446
                "coordinate  (m)": {
                    "parser": self._parse_station,
                    "fields": {
                        "station": (7, 15),
                        "coordinate": (16, 33),
                        "Estimate": (42, 56),
                        "Adjustment": (59, 69),
                        "Sigma": (72, 82),
                    },
                },
            },
        )
        return itertools.chain([header_parser], itertools.repeat(data_parser))

    def _parse_station(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse a line with station coordinates, and add a dictionary structure to dset.meta"""
        station = line["station"]
        coordinate = line["coordinate"][0]

        if not line["Estimate"] == "":
            self.meta.setdefault("station", {}).setdefault(station, {}).setdefault(
                coordinate, {}
            ).setdefault("Estimate", float(line["Estimate"]))
            self.meta.setdefault("station", {}).setdefault(station, {}).setdefault(
                coordinate, {}
            ).setdefault("Sigma", float(line["Sigma"]))

    def _parse_time(self, line: Dict[str, str], _: Dict) -> None:
        """Parse time information"""
        # Create Time object
        year = int(line["year"])
        month = int(line["month"])
        day = int(line["day"])
        hours = int(line["hours"])
        minutes = int(line["minutes"])

        time = datetime(year, month, day, hours, minutes)

        # Fill temporary Dataset
        self.data.setdefault("time", []).append(time)

    #
    # WRITE DATA
    #
    def as_dataset(self) -> "Dataset":
        """Store output of GLOBK in a dataset

        Returns:
            Midgard Dataset containing the following information

        | Field            | Type          | Description |
        | :--------------- | :------------ | :------------------------------------------ |
        | site_pos         | Position      | x, y and z station coordinates              |
        | site_pos_x_sigma | numpy.ndarray | Standard deviation for x station coordinate |
        | site_pos_y_sigma | numpy.ndarray | Standard deviation for y station coordinate |
        | site_pos_z_sigma | numpy.ndarray | Standard deviation for z station coordinate |
        | station          | numpy.ndarray | Station name list                           |
        | time             | Time          | Parameter time given as TimeTable object    |
        """
        num_stations = len(self.meta["station"])
        dset = dataset.Dataset(num_obs=num_stations)

        # Same epoch for all stations
        time_array = np.repeat(self.data["time"], num_stations)
        dset.add_time("time", time_array, scale="utc", fmt="datetime")

        pos_array = []
        sigma_x_array = []
        sigma_y_array = []
        sigma_z_array = []
        stations = []
        for station in self.meta["station"]:
            pos_station = np.array(
                (
                    self.meta["station"][station]["X"]["Estimate"],
                    self.meta["station"][station]["Y"]["Estimate"],
                    self.meta["station"][station]["Z"]["Estimate"],
                )
            )
            pos_array.append(pos_station)
            sigma_x = self.meta["station"][station]["X"]["Sigma"]
            sigma_y = self.meta["station"][station]["Y"]["Sigma"]
            sigma_z = self.meta["station"][station]["Z"]["Sigma"]
            sigma_x_array.append(sigma_x)
            sigma_y_array.append(sigma_y)
            sigma_z_array.append(sigma_z)
            stations.append(station)

        # Add position information
        dset.add_position("site_pos", pos_array, system="trs")
        dset.add_float("site_pos_x_sigma", sigma_x_array)
        dset.add_float("site_pos_y_sigma", sigma_y_array)
        dset.add_float("site_pos_z_sigma", sigma_z_array)
        dset.add_text("station", stations)
        return dset
