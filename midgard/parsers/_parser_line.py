"""Basic functionality for parsing datafiles line by line using Numpy

Description:
------------

This module contains functions and classes for parsing datafiles.


Example:
--------

    from midgard import parsers
    my_new_parser = parsers.parse_file('my_new_parser', 'file_name.txt', ...)
    my_data = my_new_parser.as_dict()

"""
# Standard library imports
from typing import Any

# Third party imports
import numpy as np

# Midgard imports
from midgard.parsers._parser import Parser


class LineParser(Parser):
    """An abstract base class that has basic methods for parsing a datafile

    This class provides functionality for using numpy to parse a file line by line. You should inherit from this one,
    and at least specify the necessary parameters in `setup_parser`.
    """

    def setup_parser(self) -> Any:
        """Set up information needed for the parser

        This method should return a dictionary which contains all parameters
        needed by np.genfromtxt to do the actual parsing.
        """
        raise NotImplementedError

    def read_data(self) -> None:
        """Read data from the data file

        Uses the np.genfromtxt-function to parse the file. Any necessary
        parameters should be set by `setup_parser`. Override
        `self.structure_data` if the self.data-dictionary needs to be
        structured in a particular way.
        """
        self.meta["__params__"] = self.setup_parser()
        self.meta["__params__"].setdefault("encoding", self.file_encoding or "bytes")  # TODO: Default to None instead?
        self._array = np.genfromtxt(self.file_path, **self.meta["__params__"])
        self.structure_data()

    def structure_data(self) -> None:
        """Structure raw array data into the self.data dictionary

        This simple implementation creates a dictionary with one item per column in the array. Override this method for
        more complex use cases.
        """
        for name in self._array.dtype.names:
            self.data[name] = self._array[name]
