"""Basic functionality for parsing datafiles, extended by individual parsers

Description:
------------

This module contains functions and classes for parsing datafiles. It should typically be used by calling
`parsers.parse_file`:

Example:
--------

    from midgard import parsers
    my_new_parser = parsers.parse_file('my_new_parser', 'file_name.txt', ...)
    my_data = my_new_parser.as_dict()

"""

# Standard library imports
import pathlib
from typing import Any, Callable, Dict, List, NoReturn, Optional, Union

# Third party imports
import pandas as pd

# Midgard imports
from midgard.dev import log


class Parser:
    """An abstract base class that has basic methods for parsing a datafile

    This class provides functionality for parsing a file. You should inherit from one of the specific parsers like for
    instance ChainParser, LineParser, SinexParser etc

    Attributes:
        data (Dict):                  The (observation) data read from file.
        data_available (Boolean):     Indicator of whether data are available.
        file_encoding (String):       Encoding of the datafile.
        file_path (Path):             Path to the datafile that will be read.
        meta (Dict):                  Metainformation read from file.
        parser_name (String):         Name of the parser (as needed to call parsers.parse_...).        
    """

    def __init__(self, file_path: Union[str, pathlib.Path], encoding: Optional[str] = None) -> None:
        """Set up the basic information needed by the parser

        Args:
            file_path:    Path to file that will be read.
            encoding:     Encoding of file that will be read.
        """
        self.file_path = pathlib.Path(file_path)
        self.file_encoding = encoding
        self.parser_name = self.__module__.split(".")[-1]

        # Initialize the data
        self.data_available = self.file_path.exists()
        self.meta: Dict[str, Any] = dict(__parser_name__=self.parser_name, __data_path__=str(self.file_path))
        self.data: Dict[str, Any] = dict()

    def setup_parser(self) -> Any:
        """Set up information needed for the parser"""
        pass

    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List postprocessors that should be called after parsing"""
        return list()

    def parse(self) -> "Parser":
        """Parse data

        This is a basic implementation that carries out the whole pipeline of
        reading and parsing datafiles including calculating secondary data.

        Subclasses should typically implement (at least) the `read_data`-method.
        """
        self.setup_parser()
        if self.data_available:
            self.read_data()

        if not self.data_available:  # May have been set to False by self.read_data()
            log.warn(f"No data found by {self.__class__.__name__} in {self.file_path}")
            return self

        self.postprocess_data()

        return self

    def read_data(self) -> None:
        """Read data from the data file

        Data should be read from `self.file_path` and stored in the dictionary
        `self.data`. A description of the data may be placed in the dictionary
        `self.meta`. If data are not available for some reason,
        `self.data_available` should be set to False.

        """
        raise NotImplementedError

    def postprocess_data(self) -> None:
        """Do simple manipulations on the data after they are read

        Simple manipulations of data may be performed in postprocessors after
        they are read. They should be kept simple so that a parser returns as
        true representation of the data file as possible. Advanced calculations
        may be done inside apriori classes or similar.

        To add a postprocessor, define it in its own method, and override the
        `setup_postprocessors`-method to return a list of all postprocessors.

        """
        for postprocessor in self.setup_postprocessors():
            postprocessor()

    def as_dict(self, include_meta: bool = False) -> Dict[str, Any]:
        """Return the parsed data as a dictionary

        This is a basic implementation, simply returning a copy of
        self.data. More advanced parsers may need to reimplement this method.

        Args:
            include_meta:  Whether to include meta-data in the returned dictionary (default: False).

        Returns:
            Dictionary with the parsed data.
        """
        return dict(self.data, __meta__=self.meta) if include_meta else self.data.copy()

    def as_dataframe(self, index: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Return the parsed data as a Pandas DataFrame

        This is a basic implementation, assuming the `self.data`-dictionary has
        a simple structure. More advanced parsers may need to reimplement this
        method.

        Args:
            index:  Optional name of field to use as index. May also be a list of strings.

        Returns:
            Pandas DataFrame with the parsed data.
        """
        df = pd.DataFrame.from_dict(self.data)
        if index is not None:
            df.set_index(index, drop=True, inplace=True)

        return df

    def as_dataset(self) -> NoReturn:
        """Return the parsed data as a Midgard Dataset

        This is a basic implementation, assuming the `self.data`-dictionary has
        a simple structure. More advanced parsers may need to reimplement this
        method.

        Returns:
            Dataset:  The parsed data.
        """
        from midgard.data import dataset

        dset = dataset.Dataset.from_dict(self.data)
        return dset

    def __repr__(self) -> str:
        """Simple string representation of the parser"""
        return f"{self.__class__.__name__}(file_path='{self.file_path}')"
