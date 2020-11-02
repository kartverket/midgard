"""Midgard library module, defining a URL class that mirrors Pathlib.Path

Warning: There are many intricacies of URLs that are not handled by this class at the moment.

"""
# Standard library imports
import pathlib
from typing import Union

# Third party imports
import pycurl


class URL(str):
    """Simple wrapper around String to have URLs work similar to pathlib.Path
    """

    @property
    def name(self) -> str:
        """Part of URL after the last /"""
        return self.split("/")[-1]

    @property
    def base(self) -> str:
        """Part of URL before the last /"""
        return self.rsplit("/", maxsplit=1)[0]

    def with_name(self, name: str) -> "URL":
        """Replace part of URL after the last / with a new name

        Args:
            name:  New name.

        Return:
            URL with part after the last / replaced with the new name.
        """
        base_url, slash, _ = self.rpartition("/")
        return self.__class__(f"{base_url}{slash}{name}")

    def exists(self) -> bool:
        """Check whether the given URL returns a valid document

        Try to download the first byte of the document (avoid downloading a big file if it exists).

        Warning: Because of network latency, this will be a slow operation.

        Return:
            True if URL leads to a valid document, False otherwise.
        """
        c = pycurl.Curl()
        c.setopt(c.URL, self)
        c.setopt(c.RANGE, "0-0")
        try:
            c.perform()
        except pycurl.error:
            return False
        return True

    def download_to(self, path: Union[str, pathlib.Path]) -> None:
        """Download the URL to path

        Args:
            path:  Path to save the URL.
        """
        raise NotImplementedError
