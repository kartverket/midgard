"""A parser for reading CSV output files

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='csv_', file_path='ADOP20473_0000.csv')
    data = p.as_dict()

Description:
------------

Reads data from files in CSV output format. The header information of the CSV file is not read (TODO).

"""
# External library imports
import numpy as np
import pandas as pd

# Midgard imports
from midgard.parsers import Parser
from midgard.dev import plugins


@plugins.register
class CsvParser(Parser):
    """A parser for reading CSV output files

    The CSV data header line is used to define the keys of the **data** dictionary. The values of the **data** 
    dictionary are represented by the CSV colum values.

    Following **meta**-data are available after reading of CSV file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |
    """

    def read_data(self) -> None:
        """Read data from the data file

        Uses the pd.read_csv-function to parse the file. 
        """
        # Note: C engine does not except regular expression for the separator option 'sep'. Disadvantage is that the
        #       Python engine is slower than the C engine by reading CSV files.
        df = pd.read_csv(
            self.file_path, engine="python", index_col=False, sep="[\;,\,]", comment="#", skip_blank_lines=True
        )
        df = df.dropna(axis="columns", how="all")  # drop 'NaN' columns
        self.data = {k: np.array(v) for k, v in df.to_dict(orient="list").items()}
