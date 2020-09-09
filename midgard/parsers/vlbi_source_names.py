"""A parser for reading IVS source names translation table
"""
# Standard library imports
from typing import Any, Dict

# Midgard imports
from midgard.dev import plugins
from midgard.parsers import LineParser


@plugins.register
class VlbiSourceNamesParser(LineParser):
    """A parser for reading IVS source names translation table

    See https://vlbi.gsfc.nasa.gov/output for an example of a IVS source name file
    """

    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Parameters needed by np.genfromtxt to parse the input file.
        """

        return dict(
            comments="#",
            delimiter=(8, 18, 12, 10, 14),
            dtype=("U8", "U18", "U12", "U10", "U14"),
            names=("ivs_name", "icrf_name_long", "icrf_name_short", "iers_name", "jpl_name"),
            usecols=(0, 1, 2, 3, 4),
            autostrip=True,
        )

    def structure_data(self) -> None:
        """Structure raw array data into the self.data dictionary

        Using the IVS name as key.
        """
        self.data = {
            src["ivs_name"]: dict(
                icrf_name_long=src["icrf_name_long"],
                icrf_name_short=src["icrf_name_short"],
                iers_name=src["iers_name"]
                if src["iers_name"] != "-" and src["iers_name"].strip()
                else src["ivs_name"],
                jpl_name=src["jpl_name"] if src["jpl_name"] != "-" else src["ivs_name"],
            )
            for src in self._array
        }
