"""A parser for reading Galileo constellation info from a web page

See https://www.gsc-europa.eu/system-status/Constellation-Information for an example
"""
# Standard library imports
import pathlib
from typing import Any, Dict, Optional, Union
import warnings

# Third party imports
import pandas as pd
import pycurl

# Midgard imports
from midgard.dev import plugins
from midgard.parsers import Parser

# Midgard imports
from midgard.dev import log


@plugins.register
class GalileoConstellationHTMLParser(Parser):
    """A parser for reading Galileo constellation info from a web page

    See https://www.gsc-europa.eu/system-status/Constellation-Information for an example
    """

    URL = "https://www.gsc-europa.eu/system-status/Constellation-Information"

    def __init__(
        self, file_path: Union[str, pathlib.Path], encoding: Optional[str] = None, url: Optional[str] = None
    ) -> None:
        """Set up the basic information needed by the parser

        Args:
            file_path:    Path to file that will be read or downloaded.
            encoding:     Encoding of file that will be read.
            url:          Optional URL from where to download constellation file.
        """
        super().__init__(file_path, encoding)
        if not self.file_path.exists():
            self.download_html(url)
            self.data_available = self.file_path.exists()

    def download_html(self, url: Optional[str] = None) -> None:
        """Download html file from url

        TODO: Move this to files/url.py

        Args:
            url:  URL to download from, if None use self.URL instead.
        """
        url = self.URL if url is None else url
        log.debug(f"Downloading {url} to {self.file_path}")
        with open(self.file_path, mode="wb") as fid:
            c = pycurl.Curl()
            c.setopt(c.URL, url)
            c.setopt(c.WRITEDATA, fid)
            try:
                c.perform()
            finally:
                c.close()

        self.meta["__url__"] = url

    def read_data(self) -> None:
        """Read tables from the HTML file

        The satellite table is placed in self.data, while the NAGU events are placed in self.meta["events"].
        """
        html = self.file_path.read_text()
        dfs = pd.read_html(html)

        for df in dfs:
            df.columns = df.columns.str.strip().str.lower().str.replace("[^a-z ]", "").str.replace(" ", "_")
            if df.columns[0].startswith("satellite_name"):
                self.data = df.to_dict(orient="list")

            elif df.columns[0].startswith("nagu_type"):
                self.meta["events"] = df.to_dict("records")

            else:
                warnings.warn(f"Unhandled table with columns {', '.join(df.columns)}")

    def satellite_name(self, sat_name: str) -> Dict[str, Any]:
        """Get satellite info from name

        Args:
            sat_name:  Name of satellite, for example GSAT0101.

        Returns:
            Dictionary with satellite info.
        """
        return self._get_satellite_info("satellite_name", sat_name)

    def satellite_id(self, sat_id: str) -> Dict[str, Any]:
        """Get satellite info from satellite vehicle ID

        Args:
            sat_id:  ID of satellite, for example E01.

        Returns:
            Dictionary with satellite info.
        """
        return self._get_satellite_info("sv_id", sat_id)

    def _get_satellite_info(self, field: str, sat: str) -> Dict[str, Any]:
        """Get satellite info by filtering on field

        Args:
            field:  Field to filter on.
            sat:    Value to look for

        Returns:
            Dictionary with satellite info.
        """
        try:
            idx = self.data[field].index(sat)
        except ValueError:
            raise KeyError(f"Satellite {sat!r} not found") from None

        return {k: v[idx] for k, v in self.data.items()}
