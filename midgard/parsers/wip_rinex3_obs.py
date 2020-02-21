"""A parser for reading RINEX observation files with version 3.xx
"""
# Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Third party imports
import numpy as np
import pandas as pd

# Midgard imports
from midgard.dev import plugins
from midgard.parsers.wip_rinex_obs import RinexObsParser
from midgard.parsers.wip_rinex3_obs_header import Rinex3ObsHeaderMixin


@plugins.register
class Rinex3ObsParser(Rinex3ObsHeaderMixin, RinexObsParser):
    """A parser for reading RINEX observation files with version 3.xx

    """

    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
    # > 2018  2  1  0  0  0.0000000  0 30

    EPOCH_FIELDS = {
        "identifier": (0, 1),
        "year": (2, 6),
        "month": (7, 9),
        "day": (10, 12),
        "hour": (13, 15),
        "minute": (16, 18),
        "second": (19, 21),
        "frac_sec": (21, 29),
        "epoch_flag": (30, 32),
        "num_data_lines": (33, 35),
    }

    @property
    def systems(self):
        return sorted(self.data.keys())

    def parse_epoch_line(self, line) -> Dict[str, Any]:
        """Read data from Rinex file

        Add data to self.data
        """
        print(f"parse_epoch_line({line})")
        fields = {k: line[slice(*v)].strip() for k, v in self.EPOCH_FIELDS.items()}
        if fields["identifier"] != ">":
            self.error(f"Line {line.strip()!r} is not an epoch line as expected")

        epoch = datetime(
            int(fields["year"]),
            int(fields["month"]),
            int(fields["day"]),
            int(fields["hour"]),
            int(fields["minute"]),
            int(fields["second"]),
            round(float(fields["frac_sec"]) * 1e6),  # microseconds
        )
        num_data_lines = int(fields["num_data_lines"])

        return num_data_lines, dict(epoch=epoch, epoch_flag=fields["epoch_flag"])

    def parse_data_lines(self, lines, epoch_info) -> Dict[str, Any]:
        """Read one section of data lines
        """
        obs_types = self.header["obs_types"]
        for line in lines:
            system, satellite, data = line[:1], line[:3], line[3:].strip("\n")
            if system not in obs_types:
                self.error(f"Unknown system {system!r} for satellite {satellite!r}")
            if system not in self.data:
                self.data[system] = {k: list() for k in ["satellite", "epoch"] + obs_types[system]}
            system_data = self.data[system]

            system_data["satellite"].append(satellite)
            system_data["epoch"].append(epoch_info["epoch"])
            data_fields = [data[i : i + 16] for i in range(0, len(data), 16)]
            for field, value in zip(obs_types[system], data_fields):
                try:
                    system_data[field].append(float(value[:14]))
                except ValueError:
                    system_data[field].append(np.nan)

    def as_dataframe(self, system: str, index: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Return the parsed data as a Pandas DataFrame

        This is a basic implementation, assuming the `self.data`-dictionary has
        a simple structure. More advanced parsers may need to reimplement this
        method.

        Args:
            sys:    Which system to create a datafrom for.
            index:  Optional name of field to use as index. May also be a list of strings.

        Returns:
            Pandas DataFrame with the parsed data.
        """
        df = pd.DataFrame.from_dict(self.data[system])
        if index is not None:
            df.set_index(index, drop=True, inplace=True)

        return df
