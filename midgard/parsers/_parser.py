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
import warnings

# External library imports
import pandas as pd

# Midgard imports
from midgard.dev.timer import Timer


class Parser:
    """An abstract base class that has basic methods for parsing a datafile

    This class provides functionality for parsing a file. You should inherit from one of the specific parsers like for
    instance ChainParser, LineParser, SinexParser etc

    Attributes:
        file_path (Path):             Path to the datafile that will be read.
        file_encoding (String):       Encoding of the datafile.
        parser_name (String):         Name of the parser (as needed to call parsers.parse_...).
        data_available (Boolean):     Indicator of whether data are available.
        data (Dict):                  The (observation) data read from file.
        meta (Dict):                  Metainformation read from file.
    """

    def __init__(
        self,
        file_path: Union[str, pathlib.Path],
        encoding: Optional[str] = None,
        logger: Optional[Callable[[str], None]] = print,
    ) -> None:
        """Set up the basic information needed by the parser

        Args:
            file_path:    Path to file that will be read.
            encoding:     Encoding of file that will be read.
            logger:       Function that will be used for logging.
        """
        self.file_path = pathlib.Path(file_path)
        self.file_encoding = encoding
        self.parser_name = self.__module__.split(".")[-1]
        self.logger = logger

        # Initialize the data
        self.data_available = self.file_path.exists()
        self.meta: Dict[str, Any] = dict(__parser_name__=self.parser_name, __data_path__=self.file_path)
        self.data: Dict[str, Any] = dict()

    def setup_parser(self) -> Any:
        """Set up information needed for the parser"""
        pass

    def setup_calculators(self) -> List[Callable[[], None]]:
        """List calculators that should be called after parsing"""
        return list()

    def parse(self) -> "Parser":
        """Parse data

        This is a basic implementation that carries out the whole pipeline of reading and parsing datafiles including
        calculating secondary data.

        Subclasses should typically implement (at least) the `read_data`-method.
        """
        self.setup_parser()

        parser_package = self.__module__.rsplit(".", maxsplit=1)[0]
        with Timer(f"Finish {self.parser_name} ({parser_package}) - {self.file_path} in", logger=self.logger):
            if self.data_available:
                if self.logger:
                    self.logger(f"Reading data from {self.file_path} with {self.parser_name} parser")
                self.read_data()

            if not self.data_available:  # May have been set to False by self.read_data()
                warnings.warn(f"No data found by {self.__class__.__name__} in {self.file_path}")
                return self

            self.calculate_data()

        return self

    def read_data(self) -> None:
        """Read data from the data file

        Data should be read from `self.file_path` and stored in the dictionary `self.data`. A description of the data
        may be placed in the dictionary `self.meta`. If data are not available for some reason, `self.data_available`
        should be set to False.
        """
        raise NotImplementedError

    def calculate_data(self) -> None:
        """Do simple manipulations on the data after they are read

        Simple manipulations of data may be performed in calculators after they are read. They should be kept simple so
        that a parser returns as true representation of the data file as possible. Advanced calculations may be done
        inside apriori classes or similar.

        To add a calculator, define it in its own method, and override the `setup_calculators`-method to return a list
        of all calculators.
        """
        for calculator in self.setup_calculators():
            calculator()

    def as_dict(self, include_meta: bool = False) -> Dict[str, Any]:
        """Return the parsed data as a dictionary

        This is a basic implementation, simply returning a copy of self.data. More advanced parsers may need to
        reimplement this method.

        Args:
            include_meta:  Whether to include meta-data in the returned dictionary (default: False).

        Returns:
            Dictionary with the parsed data.
        """
        return dict(self.data, __meta__=self.meta) if include_meta else self.data.copy()

    def as_dataframe(self, index: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Return the parsed data as a Pandas DataFrame

        This is a basic implementation, assuming the `self.data`-dictionary has a simple structure. More advanced
        parsers may need to reimplement this method.

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

        This is a basic implementation, assuming the `self.data`-dictionary has a simple structure. More advanced
        parsers may need to reimplement this method.

        Returns:
            Dataset:  The parsed data.
        """
        # from midgard import data
        #
        # dset = data.Dataset.from_dict(self.data)
        #
        # return dset
        raise NotImplementedError

    def update_dataset(self, dset: Any) -> NoReturn:
        """Update the given dataset with the parsed data

        This is a basic implementation, assuming the `self.data`-dictionary has a simple structure. More advanced
        parsers may need to reimplement this method.

        Args:
            dset (Dataset):  The dataset to update with parsed data.
        """
        # parser_dset = self.as_dataset()
        # if new fields:
        #     dset.add ...
        # elif new epochs:
        #     dset.extend ...
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(file_path='{self.file_path}')"
