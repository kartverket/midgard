"""Basic functionality for parsing Sinex datafiles

Description:
------------

This module contains functions and classes for parsing Sinex datafiles.


References:
-----------

* SINEX Format: https://www.iers.org/IERS/EN/Organization/AnalysisCoordinator/SinexFormat/sinex.html

"""

# Standard library imports
from datetime import datetime, timedelta
import itertools
import pathlib
from typing import cast, Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple, Union

# Third party imports
import numpy as np
import pandas as pd

# Midgard imports
from midgard.dev import log
from midgard.files import files
from midgard.parsers._parser import Parser
from midgard.math.unit import Unit


# A simple structure used to define a Sinex field
class SinexField(NamedTuple):
    """A convenience class for defining the fields in a Sinex block

    Args:
        name:       Name of field.
        start_col:  Starting column of field (First column is 0)
        dtype:      String, using numpy notation, defining type of field, use None to ignore field.
        converter:  Optional, name of converter to apply to field data.
    """

    name: str
    start_col: int
    dtype: Optional[str]
    converter: Optional[str] = None


# A simple structure used to define a Sinex block
class SinexBlock(NamedTuple):
    """A convenience class for defining a Sinex block

    Args:
        marker:  Sinex marker denoting the block.
        fields:  Fields in Sinex block.
        parser:  Function used to parse the data.
    """

    marker: str
    fields: Tuple[SinexField, ...]
    parser: Callable[[np.array, Tuple[str, ...]], Dict[str, Any]]


#
# FACTORY FUNCTIONS
#
def parsing_factory() -> Callable[..., Dict[str, Any]]:
    """Create a default parsing function for a Sinex block

    The default parsing function returns a dictionary containing all fields of
    the block as separated arrays. This will be stored in self.data['{marker}']
    with the {marker} of the current block.

    Returns:
        Simple parsing function for one Sinex block.
    """

    def parse_func(self: "SinexParser", data: np.array, *params: str) -> Dict[str, Any]:
        """Simple parser for Sinex data

        Converts the input data to a dictionary of numpy arrays and returns it
        in order to add it to self.data['{marker}']. Ignores any block title
        parameters.

        Args:
            data:    Input data, raw data for the block.
            params:  Tuple of strings with parameters given after the marker at the start of the block.

        Returns:
            Dictionary with each column in the Sinex file as a numpy array.
        """
        return {n: data[n] for n in data.dtype.names}

    return parse_func


def parsing_matrix_factory(marker: str, size_marker: str) -> Callable[..., Dict[str, Any]]:
    """Create a parsing function for parsing a matrix within a Sinex block

    The default parsing function converts data to a symmetric matrix and stores
    it inside `self.data[marker]`.

    The size of the matrix is set to equal the number of parameters in the
    `size_marker`-block. If that block is not parsed/found. The size is set to
    the last given row index. If some zero elements in the matrix are omitted
    this might be wrong.

    Args:
        marker:       Marker of Sinex block.
        size_marker:  Marker of a different Sinex block indicating the size of the matrix.

    Returns:
        Simple parsing function for one Sinex block.
    """

    def parse_matrix_func(self: "SinexParser", data: np.array, lower_upper: str, type: str = "") -> Dict[str, Any]:
        """Parser for {marker} data

        Converts the input data to a symmetric matrix and adds it to
        self.data['{marker}'].

        The NEQ-Matrix Row/Column Number correspond to the Estimated Parameters
        Index in the {size_marker} block.  Missing elements in the matrix are
        assumed to be zero (0); consequently, zero elements may be omitted to
        reduce the size of this block.

        Args:
            data:         Input data, raw data for {marker} block.
            lower_upper:  Either 'L' or 'U', indicating whether the matrix is given in lower or upper form.
            type:         Information about the type of matrix, optional.

        Returns:
            Dictionary with symmetric matrix as a numpy array.
        """
        # Size of matrix is given by {size_marker}-block, initialize to all zeros
        try:
            n = len(self._sinex[size_marker])
        except KeyError:
            n = max(data["row_idx"])
            log.warn(f"{size_marker!r}-block was not parsed. Guessing at size of normal equation matrix (n={n}).")
        matrix = np.zeros((n, n))

        # Loop through each line of values and put it in the correct place in the matrix (cannot simply reshape as
        # elements may have been omitted)
        values = np.stack((data["value_0"], data["value_1"], data["value_2"]), axis=1)
        for row, col, vals in zip(data["row_idx"], data["column_idx"], values):
            vals = vals[~np.isnan(vals)]
            idx = slice(row - 1, row), slice(col - 1, col - 1 + len(vals))
            matrix[idx] = vals

        # Add symmetrical elements, depending on whether the matrix being represented in lower or upper form
        if lower_upper.upper() == "L":
            matrix = np.tril(matrix) + np.tril(matrix, k=-1).T
        elif lower_upper.upper() == "U":
            matrix = np.triu(matrix) + np.triu(matrix, k=1).T
        else:
            log.warn(f"'L' or 'U' not specified for {marker}. Trying to create a symmetric matrix anyway.")
            matrix = matrix + matrix.T - np.diag(np.diag(matrix))

        return {"matrix": matrix, "type": type}

    # Add information to doc-string
    if parse_matrix_func.__doc__:
        parse_matrix_func.__doc__ = parse_matrix_func.__doc__.format(marker=marker, size_marker=size_marker)

    return parse_matrix_func


#
# SINEXPARSER CLASS
#
class SinexParser(Parser):
    """An abstract base class that has basic methods for parsing a Sinex file

    This class provides functionality for parsing a sinex file with chained
    groups of information. You should inherit from this one, and at least
    specify which Sinex blocks you are interested in by implementing
    `setup_parser`, as well as implement methods that parse each block if
    needed.
    """

    _TECH = {"C": "comb", "D": "doris", "L": "slr", "M": "llr", "P": "gnss", "R": "vlbi"}

    def __init__(
        self, file_path: Union[str, pathlib.Path], encoding: Optional[str] = None, header: bool = True
    ) -> None:
        """Set up the basic information needed by the parser

        Add a self._sinex dictionary for the raw Sinex data and read which
        blocks to read from self.setup_parser().

        Args:
            file_path:  Path to file that will be read.
            encoding:   Encoding of file that will be read.
            header:     Whether to parse the header.
        """
        super().__init__(file_path, encoding=encoding)
        self._header = header
        self._sinex: Dict[str, Any] = dict()
        self.sinex_blocks = cast(Iterable[SinexBlock], self.setup_parser())

    def setup_parser(self) -> Any:
        """Set up information needed for the parser

        Each individual Sinex-parser should at least implement this method.

        If the order the blocks are parsed is not important, the information
        should be returned as a set for optimal performance. If the parsing
        order is important, a tuple of SinexBlock-objects may be returned
        instead.

        Returns:
            Iterable of blocks in the Sinex file that should be parsed.
        """
        raise NotImplementedError

    def read_data(self) -> None:
        """Read data from a Sinex file and parse the contents

        First the whole Sinex file is read and the requested blocks are stored
        in self._sinex. After the file has been read, a parser is called on
        each block so that self.data is properly populated.
        """
        # Read raw sinex data to self._sinex from file
        with files.open(self.file_path, mode="rb") as fid:
            if self._header:
                self.parse_header_line(next(fid))  # Header must be first line
            self.parse_blocks(fid)

        # Apply parsers to raw sinex data, the information returned by parsers is stored in self.data
        for sinex_block in self.sinex_blocks:
            if sinex_block.parser and sinex_block.marker in self._sinex:
                params = self._sinex.get("__params__", dict()).get(sinex_block.marker, ())
                data = sinex_block.parser(self._sinex.get(sinex_block.marker), *params)
                if data is not None:
                    self.data[sinex_block.marker] = data

    def parse_blocks(self, fid: Iterable[bytes]) -> None:
        """Parse contents of Sinex blocks

        Contents of Sinex blocks are stored as separate numpy-arrays in
        self._sinex

        Args:
            fid:  Pointer to file being read.
        """
        # Get set of interesting Sinex blocks, index them by marker
        sinex_blocks = {b.marker: b for b in self.sinex_blocks}

        # Iterate until all interesting Sinex blocks have been found or whole file is read
        try:
            while sinex_blocks:
                # Find next block (line that starts with +)
                fid = itertools.dropwhile(lambda ln: not ln.startswith(b"+"), fid)
                block_header = next(fid).decode(self.file_encoding or "utf-8")
                marker, *params = block_header[1:].strip().split()
                if marker not in sinex_blocks:
                    continue

                # Find lines in block, remove comments and parse lines, store parameters for later
                lines = [
                    ln for ln in itertools.takewhile(lambda ln: not ln.startswith(b"-"), fid) if ln.startswith(b" ")
                ]
                self._sinex[marker] = self.parse_lines(lines, sinex_blocks[marker].fields)
                if params:
                    self._sinex.setdefault("__params__", dict())[marker] = params
                del sinex_blocks[marker]

        except StopIteration:  # File ended without reading all sinex_blocks
            missing = ", ".join(sinex_blocks)
            log.warn(f"SinexParser {self.parser_name!r} did not find Sinex blocks {missing} in file {self.file_path}")

    def parse_lines(self, lines: List[bytes], fields: Tuple[SinexField, ...]) -> np.array:
        """Parse lines in a Sinex file

        Args:
            lines:   Lines to parse.
            fields:  Definition of sinex fields in lines.

        Returns:
            Data contained in lines.
        """
        # Set up for np.genfromtxt to parse the Sinex block
        delimiter = np.diff(np.array([0] + [f.start_col for f in fields] + [81]))  # Length of each field
        names = [f.name for f in fields if f.dtype]  # Names, only fields with dtype set
        usecols = [i for i, f in enumerate(fields, start=1) if f.dtype]  # Skip 0th and fields without dtype
        dtype = [f.dtype for f in fields if f.dtype]  # Types of fields
        converters = {
            i: getattr(self, "_convert_{}".format(f.converter))  # Converters
            for i, f in enumerate(fields, start=1)
            if f.converter
        }

        return np.genfromtxt(
            lines,
            names=names,
            delimiter=delimiter,
            dtype=dtype,
            usecols=usecols,
            converters=converters,
            autostrip=True,
            encoding=self.file_encoding or "bytes",  # TODO: Use None instead
        )

    def as_dataframe(
        self, index: Optional[Union[str, List[str]]] = None, marker: Optional[str] = None
    ) -> pd.DataFrame:
        """Return the parsed data as a Pandas DataFrame

        This is a basic implementation, assuming the `self.data`-dictionary has
        a simple structure. More advanced parsers may need to reimplement this
        method.

        Args:
            marker:  Only return data from this marker in the DataFrame.
            index:   Name of field to use as index. May also be a list of strings.

        Returns:
            Pandas DataFrame with the parsed data.
        """
        if marker and marker in self.data:
            df = pd.DataFrame.from_dict(self.data[marker])
        else:
            df = pd.DataFrame.from_dict(self.data)

        if index is not None:
            df.set_index(index, drop=True, inplace=True)

        return df

    #
    # CONVERTERS
    #
    def _convert_dms2deg(self, field: bytes) -> float:
        """Convert DMS (degrees, minutes, seconds) to degrees

        Args:
            field:   Original field with degrees, minutes, seconds separated by whitespace.

        Returns:
            Field converted to degrees.
        """
        degrees, minutes, seconds = [float(f) for f in field.split()]
        return Unit.dms_to_rad(degrees, minutes, seconds) * Unit.radians2degrees

    def _convert_dms2rad(self, field: bytes) -> float:
        """Convert DMS (degrees, minutes, seconds) to radians

        Args:
            field:  Original field with degrees, minutes, seconds separated by whitespace.

        Returns:
            Field converted to radians.
        """
        degrees, minutes, seconds = [float(f) for f in field.split()]
        return Unit.dms_to_rad(degrees, minutes, seconds)

    def _convert_epoch(self, field: bytes) -> datetime:
        """Convert epoch field to datetime value

        The epoch is given in YY:DDD:SSSSS format with::

            YY    = last 2 digits of the year,
                      if YY <= 50 implies 21-st century,
                      if YY > 50 implies 20-th century,
            DDD   = 3-digit day of year,
            SSSSS = 5-digit seconds of day.

        Args:
            field:  Original field with time epoch in YY:DDD:SSSSS format.

        Returns:
            Field converted to datetime object.
        """
        ce = "19" if int(field[:2]) > 50 else "20"
        date = datetime.strptime(ce + field[:6].decode(self.file_encoding or "utf-8"), "%Y:%j")
        time = timedelta(seconds=int(field[7:]))
        return date + time

    def _convert_exponent(self, field: bytes) -> float:
        """Convert scientific notation number field to float

        A number in scientific notation. Some programs write use the letter D
        as exponent in scientific notation.  Python does not recognize this
        letter and it needs to be changed to E.

        Args:
            field: Original field with a number using scientific notation.

        Returns:
            Field converted to floating point number.
        """
        return float(field.decode(self.file_encoding or "utf-8").replace("D", "E"))

    def _convert_list(self, field: bytes) -> List[str]:
        """Convert field to list

        Args:
            field):  Original field with elements split by whitespace.

        Returns:
            Field converted to list of strings.
        """
        return field.decode(self.file_encoding or "utf-8").split()

    def _convert_tuple(self, field: bytes) -> Tuple[str, ...]:
        """Convert field to tuple

        Args:
            field:  Original field with elements split by whitespace.

        Returns:
            Field converted to tuple of strings.
        """
        return tuple(field.decode(self.file_encoding or "utf-8").split())

    def _convert_utf8(self, field: bytes) -> str:
        """Decode field using utf-8

        Args:
            field:  Original field.

        Returns:
            Field decoded using utf-8.
        """
        return field.decode(self.file_encoding or "utf-8")

    #
    # HEADER
    #
    @property
    def header_fields(self) -> Tuple[SinexField, ...]:
        """Fields in header line of Sinex file

        The header line is the first line of the file, and not a proper Sinex
        block. It must start with the 5 characters `%=SNX`.

        Example:
            %=SNX 2.02 IGN 15:314:37740 IGN 00:000:00000 00:000:00000 R   142 2 S
                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789
        """
        return (
            SinexField("snx_version", 5, "f8"),
            SinexField("create_agency", 10, "U3"),
            SinexField("create_epoch", 14, "O", "epoch"),
            SinexField("data_agency", 27, "U3"),
            SinexField("start_epoch", 31, "O", "epoch"),
            SinexField("end_epoch", 44, "O", "epoch"),
            SinexField("obs_code", 57, "U1"),
            SinexField("num_param", 59, "i8"),
            SinexField("constraint_code", 65, "U1"),
            SinexField("solution_contents", 67, "O", "tuple"),
        )

    def parse_header_line(self, header_line: bytes) -> None:
        """Parse header of Sinex file

        Header information is stored in `self.meta`.

        Args:
            header_line:  First line of Sinex file.
        """
        if not header_line.startswith(b"%=SNX"):
            log.warn(
                f"The file '{self.file_path}' does not contain a valid SINEX header: {header_line.decode().strip()!r}"
            )
            return

        # Add header information to self.meta
        header_data = self.parse_lines([header_line], self.header_fields)
        self.meta.update({n: header_data[n][()] for n in header_data.dtype.names})

    #
    # SINEX BLOCKS
    #
    @property
    def file_reference(self) -> SinexBlock:
        """Information about how the Sinex file was created

        Provides information on the Organization, point of contact, the
        software and hardware involved in the creation of the file.
        """
        return SinexBlock(
            marker="FILE/REFERENCE",
            fields=(SinexField("info_type", 1, "U18"), SinexField("info", 20, "U60")),
            parser=self.parse_file_reference,
        )

    parse_file_reference = parsing_factory()

    @property
    def file_comment(self) -> SinexBlock:
        """General comments about the Sinex data file
        """
        return SinexBlock(
            marker="FILE/COMMENT", fields=(SinexField("comment", 1, "U79"),), parser=self.parse_file_comment
        )

    parse_file_comment = parsing_factory()

    @property
    def input_history(self) -> SinexBlock:
        """Information about the source of the information used to create the current Sinex file
        """
        return SinexBlock(
            marker="INPUT/HISTORY",
            fields=(
                SinexField("file_code", 1, "U1"),
                SinexField("doc_type", 2, "U3"),
                SinexField("snx_version", 6, "f8"),
                SinexField("create_agency", 11, "U3"),
                SinexField("create_epoch", 15, "O", "epoch"),
                SinexField("data_agency", 28, "U3"),
                SinexField("start_epoch", 32, "O", "epoch"),
                SinexField("end_epoch", 45, "O", "epoch"),
                SinexField("obs_code", 58, "U1"),
                SinexField("num_param", 60, "i8"),
                SinexField("constraint_code", 66, "U1"),
                SinexField("solution_contents", 68, "U12"),
            ),
            parser=self.parse_input_history,
        )

    parse_input_history = parsing_factory()

    @property
    def input_files(self) -> SinexBlock:
        """Identify the input files

        This block identify the input files (and the current SINEX file) and
        allow for a short comment to be added to describe those files.
        """
        return SinexBlock(
            marker="INPUT/FILES",
            fields=(
                SinexField("create_agency", 1, "U3"),
                SinexField("create_time", 5, "O", "epoch"),
                SinexField("filename", 18, "U29"),
                SinexField("description", 48, "U32"),
            ),
            parser=self.parse_input_files,
        )

    parse_input_files = parsing_factory()

    @property
    def input_acknowledgements(self) -> SinexBlock:
        """Information about who contributed to the solution
        """
        return SinexBlock(
            marker="INPUT/ACKNOWLEDGEMENTS",
            fields=(SinexField("agency", 1, "U3"), SinexField("description", 5, "U75")),
            parser=self.parse_input_acknowledgements,
        )

    parse_input_acknowledgements = parsing_factory()

    @property
    def nutation_data(self) -> SinexBlock:
        """Information about nutation model used in the analysis
        """
        return SinexBlock(
            marker="NUTATION/DATA",
            fields=(SinexField("nutation_code", 1, "U8"), SinexField("comments", 10, "U70")),
            parser=self.parse_nutation_data,
        )

    parse_nutation_data = parsing_factory()

    @property
    def precession_data(self) -> SinexBlock:
        """Information about the precession model used in the analysis
        """
        return SinexBlock(
            marker="PRECESSION/DATA",
            fields=(SinexField("precession_code", 1, "U8"), SinexField("comments", 10, "U70")),
            parser=self.parse_precession_data,
        )

    parse_precession_data = parsing_factory()

    @property
    def source_id(self) -> SinexBlock:
        """Information about radio sources
        """
        return SinexBlock(
            marker="SOURCE/ID",
            fields=(
                SinexField("source_code", 1, "U4"),
                SinexField("iers_designation", 6, "U8"),
                SinexField("icrf_designation", 15, "U18"),
                SinexField("comments", 32, "U68"),
            ),
            parser=self.parse_source_id,
        )

    parse_source_id = parsing_factory()

    @property
    def site_id(self) -> SinexBlock:
        """General information for each site containing estimated parameters.

        Example:
            *CODE PT __DOMES__ T _STATION DESCRIPTION__ _LONGITUDE_ _LATITUDE__ HEIGHT_
             1515  A 40405S019 R DSS15    34-m HEF at G 243 06 46.0  35 25 18.6   973.2
                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789
        """
        return SinexBlock(
            marker="SITE/ID",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("point_code", 6, "U2"),
                SinexField("domes", 9, "U5"),
                SinexField("marker", 14, "U4"),
                SinexField("obs_code", 19, "U1"),
                SinexField("description", 21, "U22", "utf8"),
                SinexField("approx_lon", 44, "f8", "dms2deg"),
                SinexField("approx_lat", 56, "f8", "dms2deg"),
                SinexField("approx_height", 68, "f8"),
            ),
            parser=self.parse_site_id,
        )

    parse_site_id = parsing_factory()

    @property
    def site_data(self) -> SinexBlock:
        """The relationship between the estimated station parameters in the SINEX file and in the input files
        """
        return SinexBlock(
            marker="SITE/DATA",
            fields=(
                SinexField("solved_site_code", 1, "U4"),
                SinexField("solved_point_code", 6, "U2"),
                SinexField("solved_soln", 9, "U4"),
                SinexField("input_site_code", 14, "U4"),
                SinexField("input_point_code", 19, "U2"),
                SinexField("input_soln", 22, "U4"),
                SinexField("input_obs_code", 26, "U1"),
                SinexField("input_start_time", 28, "O", "epoch"),
                SinexField("input_end_time", 41, "O", "epoch"),
                SinexField("input_agency", 54, "U3"),
                SinexField("input_create_time", 58, "O", "epoch"),
            ),
            parser=self.parse_site_data,
        )

    parse_site_data = parsing_factory()

    @property
    def site_receiver(self) -> SinexBlock:
        """Information about receivers used for the observations
        """
        return SinexBlock(
            marker="SITE/RECEIVER",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("point_code", 6, "U2"),
                SinexField("soln", 9, "U4"),
                SinexField("obs_code", 14, "U1"),
                SinexField("start_time", 16, "O", "epoch"),
                SinexField("end_time", 29, "O", "epoch"),
                SinexField("receiver_type", 42, "U20"),
                SinexField("serial_number", 63, "U5"),
                SinexField("firmware", 69, "U11"),
            ),
            parser=self.parse_site_receiver,
        )

    parse_site_receiver = parsing_factory()

    @property
    def site_antenna(self) -> SinexBlock:
        """Information about antennas at the sites
        """
        return SinexBlock(
            marker="SITE/ANTENNA",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("point_code", 6, "U2"),
                SinexField("soln", 9, "U4"),
                SinexField("obs_code", 14, "U1"),
                SinexField("start_time", 16, "O", "epoch"),
                SinexField("end_time", 29, "O", "epoch"),
                SinexField("antenna_type", 42, "U20"),
                SinexField("serial_number", 63, "U5"),
            ),
            parser=self.parse_site_antenna,
        )

    parse_site_antenna = parsing_factory()

    @property
    def site_gps_phase_center(self) -> SinexBlock:
        """Information about GPS antenna phase centers
        """
        return SinexBlock(
            marker="SITE/GPS_PHASE_CENTER",
            fields=(
                SinexField("antenna_type", 1, "U20"),
                SinexField("serial_number", 22, "U5"),
                SinexField("L1_up_offset", 28, "f8"),
                SinexField("L1_north_offset", 35, "f8"),
                SinexField("L1_east_offset", 42, "f8"),
                SinexField("L2_up_offset", 49, "f8"),
                SinexField("L2_north_offset", 56, "f8"),
                SinexField("L2_east_offset", 63, "f8"),
                SinexField("calibration_model", 70, "U10"),
            ),
            parser=self.parse_site_gps_phase_center,
        )

    parse_site_gps_phase_center = parsing_factory()

    @property
    def site_gal_phase_center(self) -> SinexBlock:
        """Information about Galileo antenna phase centers

        #TODO from old sinex_blocks:
                (True, 1): {'parser': self.parse_site_gal_phase_center,
                            'fields': {'antenna_type':          (1, 21),
                                       'serial_number':        (22, 27),
                                       'L1_up_offset':         (28, 34),
                                       'L1_north_offset':      (35, 41),
                                       'L1_east_offset':       (42, 48),
                                       'L2_up_offset':         (49, 55),
                                       'L2_north_offset':      (56, 62),
                                       'L2_east_offset':       (63, 69),
                                       'calibration_model':    (70, 80),
                                       },
                            },
                (True, 2): {'parser': self.parse_site_gal_phase_center,
                            'fields': {'antenna_type':          (1, 21),
                                       'serial_number':        (22, 27),
                                       'L6_up_offset':         (28, 34),
                                       'L6_north_offset':      (35, 41),
                                       'L6_east_offset':       (42, 48),
                                       'L7_up_offset':         (49, 55),
                                       'L7_north_offset':      (56, 62),
                                       'L7_east_offset':       (63, 69),
                                       'calibration_model':    (70, 80),
                                       },
                            },
                (True, 3): {'parser': self.parse_site_gal_phase_center,
                            'fields': {'antenna_type':          (1, 21),
                                       'serial_number':        (22, 27),
                                       'L8_up_offset':         (28, 34),
                                       'L8_north_offset':      (35, 41),
                                       'L8_east_offset':       (42, 48),
                                       'future_up':            (49, 55),
                                       'future_north':         (56, 62),
                                       'future_east':          (63, 69),
                                       'calibration_model':    (70, 80),
                                       },
        """
        return SinexBlock(marker="SITE/GAL_PHASE_CENTER", fields=(), parser=self.parse_site_gal_phase_center)  # TODO

    parse_site_gal_phase_center = parsing_factory()

    @property
    def site_eccentricity(self) -> SinexBlock:
        """List of antenna eccentricities

        Antenna eccentricities from the Marker to the Antenna Reference Point
        (ARP) or to the intersection of axis.
        """
        return SinexBlock(
            marker="SITE/ECCENTRICITY",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("point_code", 6, "U2"),
                SinexField("soln", 9, "U4"),
                SinexField("obs_code", 14, "U1"),
                SinexField("start_time", 16, "O", "epoch"),
                SinexField("end_time", 29, "O", "epoch"),
                SinexField("vector_type", 42, "U3"),
                SinexField("vector_1", 46, "f8"),
                SinexField("vector_2", 55, "f8"),
                SinexField("vector_3", 64, "f8"),
            ),
            parser=self.parse_site_eccentricity,
        )

    parse_site_eccentricity = parsing_factory()

    @property
    def satellite_id(self) -> SinexBlock:
        """Information about GNSS satellites used in the solution
        """
        return SinexBlock(
            marker="SATELLITE/ID",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("prn", 6, "U2"),
                SinexField("cospar_id", 9, "U9"),
                SinexField("obs_code", 19, "U1"),
                SinexField("start_time", 21, "O", "epoch"),
                SinexField("end_time", 34, "O", "epoch"),
                SinexField("antenna_type", 47, "U20"),
            ),
            parser=self.parse_satellite_id,
        )

    parse_satellite_id = parsing_factory()

    @property
    def satellite_phase_center(self) -> SinexBlock:
        """Information about GNSS satellite antenna phase centers
        """
        return SinexBlock(
            marker="SATELLITE/PHASE_CENTER",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("frequency_code_1", 6, "U1"),
                SinexField("z_offset_1", 8, "f8"),
                SinexField("x_offset_1", 15, "f8"),
                SinexField("y_offset_1", 22, "f8"),
                SinexField("frequency_code_2", 29, "U1"),
                SinexField("z_offset_2", 31, "f8"),
                SinexField("x_offset_2", 38, "f8"),
                SinexField("y_offset_2", 45, "f8"),
                SinexField("calibration_model", 52, "U10"),
                SinexField("pvc_type", 63, "U1"),
                SinexField("pvc_application", 65, "U1"),
            ),
            parser=self.parse_satellite_phase_center,
        )

    parse_satellite_phase_center = parsing_factory()

    @property
    def solution_epochs(self) -> SinexBlock:
        """List of solution epoch for each Site Code/Point Code/Solution Number/Observation Code (SPNO) combination

        Example:
            *Code PT SOLN T Data_start__ Data_end____ Mean_epoch__
             7207  A    1 C 79:216:00540 88:315:57656 84:083:28558
                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789
        """
        return SinexBlock(
            marker="SOLUTION/EPOCHS",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("point_code", 6, "U2"),
                SinexField("soln", 9, "U4"),
                SinexField("obs_code", 14, "U1"),
                SinexField("start_epoch", 16, "O", "epoch"),
                SinexField("end_epoch", 29, "O", "epoch"),
                SinexField("mean_epoch", 42, "O", "epoch"),
            ),
            parser=self.parse_solution_epochs,
        )

    parse_solution_epochs = parsing_factory()

    @property
    def bias_epochs(self) -> SinexBlock:
        """List of epochs of bias parameters for each Site Code/Point Code/Solution Number/Bias Type (SPNB) combination
        """
        return SinexBlock(
            marker="BIAS/EPOCHS",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("point_code", 6, "U2"),
                SinexField("soln", 9, "U4"),
                SinexField("bias_type", 14, "U1"),
                SinexField("start_epoch", 16, "O", "epoch"),
                SinexField("end_epoch", 29, "O", "epoch"),
                SinexField("weighted_mean_epoch", 42, "O", "epoch"),
            ),
            parser=self.parse_bias_epochs,
        )

    parse_bias_epochs = parsing_factory()

    @property
    def solution_statistics(self) -> SinexBlock:
        """Statistical information about the solution
        """
        return SinexBlock(
            marker="SOLUTION/STATISTICS",
            fields=(SinexField("info_type", 1, "U30"), SinexField("info", 32, "f8")),
            parser=self.parse_solution_statistics,
        )

    parse_solution_statistics = parsing_factory()

    @property
    def solution_estimate(self) -> SinexBlock:
        """Estimated parameters

        Example:
            *INDEX TYPE__ CODE PT SOLN _REF_EPOCH__ UNIT S __ESTIMATED VALUE____ _STD_DEV___
                 1 STAX   7207  A    1 10:001:00000 m    2 -.240960109141758E+07 0.12784E-02
                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789
        """
        return SinexBlock(
            marker="SOLUTION/ESTIMATE",
            fields=(
                SinexField("param_idx", 1, "i8"),
                SinexField("param_name", 7, "U6"),
                SinexField("site_code", 14, "U4"),
                SinexField("point_code", 19, "U2"),
                SinexField("soln", 22, "U4"),
                SinexField("ref_epoch", 27, "O", "epoch"),
                SinexField("unit", 40, "U4"),
                SinexField("constraint", 45, "U1"),
                SinexField("estimate", 47, "f8", "exponent"),
                SinexField("estimate_std", 69, "f8", "exponent"),
            ),
            parser=self.parse_solution_estimate,
        )

    parse_solution_estimate = parsing_factory()

    @property
    def solution_apriori(self) -> SinexBlock:
        """Apriori parameters

        Example:
            *Index Type__ CODE PT SOLN Ref_epoch___ Unit S Apriori_value________ _Std_dev___
                 1 UT     ---- --    1 15:217:19127 ms   2  2.96943971326695e+02 0.00000e+00
                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789
        """
        return SinexBlock(
            marker="SOLUTION/APRIORI",
            fields=(
                SinexField("param_idx", 1, "i8"),
                SinexField("param_name", 7, "U6"),
                SinexField("site_code", 14, "U4"),
                SinexField("point_code", 19, "U2"),
                SinexField("soln", 22, "U4"),
                SinexField("ref_epoch", 27, "O", "epoch"),
                SinexField("unit", 40, "U4"),
                SinexField("constraint", 45, "U1"),
                SinexField("apriori", 47, "f8", "exponent"),
                SinexField("apriori_std", 69, "f8", "exponent"),
            ),
            parser=self.parse_solution_apriori,
        )

    parse_solution_apriori = parsing_factory()

    @property
    def solution_matrix_estimate(self) -> SinexBlock:
        """Matrix estimate block.

        The estimate matrix can be stored in an Upper or Lower triangular
        form. Only the Upper or Lower portion needs to be stored because the
        matrix is always symmetrical. The distinction between the forms is
        given by the title block which must take one of the following forms:

            SOLUTION/MATRIX_ESTIMATE L CORR
            SOLUTION/MATRIX_ESTIMATE U CORR
            SOLUTION/MATRIX_ESTIMATE L COVA
            SOLUTION/MATRIX_ESTIMATE U COVA
            SOLUTION/MATRIX_ESTIMATE L INFO
            SOLUTION/MATRIX_ESTIMATE U INFO
        """
        return SinexBlock(
            marker="SOLUTION/MATRIX_ESTIMATE",
            fields=(
                SinexField("row_idx", 1, "i8"),
                SinexField("column_idx", 7, "i8"),
                SinexField("value_0", 13, "f8"),
                SinexField("value_1", 35, "f8"),
                SinexField("value_2", 57, "f8"),
            ),
            parser=self.parse_solution_matrix_estimate,
        )

    parse_solution_matrix_estimate = parsing_matrix_factory(
        "SOLUTION/MATRIX_ESTIMATE", size_marker="SOLUTION/ESTIMATE"
    )

    @property
    def solution_matrix_apriori(self) -> SinexBlock:
        """Matrix apriori block.

        The estimate matrix can be stored in an Upper or Lower triangular
        form. Only the Upper or Lower portion needs to be stored because the
        matrix is always symmetrical. The distinction between the forms is
        given by the title block which must take one of the following forms:

            SOLUTION/MATRIX_APRIORI L CORR
            SOLUTION/MATRIX_APRIORI U CORR
            SOLUTION/MATRIX_APRIORI L COVA
            SOLUTION/MATRIX_APRIORI U COVA
            SOLUTION/MATRIX_APRIORI L INFO
            SOLUTION/MATRIX_APRIORI U INFO
        """
        return SinexBlock(
            marker="SOLUTION/MATRIX_APRIORI",
            fields=(
                SinexField("row_idx", 1, "i8"),
                SinexField("column_idx", 7, "i8"),
                SinexField("value_0", 13, "f8"),
                SinexField("value_1", 35, "f8"),
                SinexField("value_2", 57, "f8"),
            ),
            parser=self.parse_solution_matrix_apriori,
        )

    parse_solution_matrix_apriori = parsing_matrix_factory("SOLUTION/MATRIX_APRIORI", size_marker="SOLUTION/ESTIMATE")

    @property
    def solution_normal_equation_vector(self) -> SinexBlock:
        """Right hand side of the unconstrained (reduced) normal equation.
        """
        return SinexBlock(
            marker="SOLUTION/NORMAL_EQUATION_VECTOR",
            fields=(
                SinexField("param_idx", 1, "i5"),
                SinexField("param_type", 7, "U6"),
                SinexField("site_code", 14, "U4"),
                SinexField("point code", 19, "U2"),
                SinexField("soln", 22, "U4"),
                SinexField("ref_epoch", 27, "O", "epoch"),
                SinexField("unit", 40, "U4"),
                SinexField("constraint", 45, "U1"),
                SinexField("value", 47, "f8"),
            ),
            parser=self.parse_solution_normal_equation_vector,
        )

    parse_solution_normal_equation_vector = parsing_factory()

    @property
    def solution_normal_equation_matrix(self) -> SinexBlock:
        """The original (reduced) normal equation matrix without constraints

        This block is mandatory if the normal equation is to be provided
        directly in the SINEX file.  The block should contain the original
        (reduced) normal equation matrix (i.e., without constraints).  The
        normal equation matrix can be stored in an Upper or Lower triangular
        form. Only the Upper or Lower portion needs to be stored because the
        matrix is always symmetrical. The distinction between the forms is
        given by the title block which must take one of the following forms:

            SOLUTION/NORMAL_EQUATION_MATRIX L
            SOLUTION/NORMAL_EQUATION_MATRIX U

        Example:
            *Para1 Para2 Para2+0______________ Para2+1______________ Para2+2______________
                 1     1  1.76801358863522e+05 -4.25992161422579e+03  4.74965662312563e+02
                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789

        """
        return SinexBlock(
            marker="SOLUTION/NORMAL_EQUATION_MATRIX",
            fields=(
                SinexField("row_idx", 1, "i8"),
                SinexField("column_idx", 7, "i8"),
                SinexField("value_0", 13, "f8"),
                SinexField("value_1", 35, "f8"),
                SinexField("value_2", 57, "f8"),
            ),
            parser=self.parse_solution_normal_equation_matrix,
        )

    parse_solution_normal_equation_matrix = parsing_matrix_factory(
        "SOLUTION/NORMAL_EQUATION_MATRIX", size_marker="SOLUTION/ESTIMATE"
    )

    @property
    def discontinuity(self) -> SinexBlock:
        """Station discontinuities.

        Example:
            *CODE PT SOLN O __START_TIME __END_TIME__ E __DESCRIPTION
             0194  A    1 P 00:000:00000 03:160:00000 P - antenna change
                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789
        """
        return SinexBlock(
            marker="SOLUTION/DISCONTINUITY",
            fields=(
                SinexField("site_code", 1, "U4"),
                SinexField("point_code", 6, "U2"),
                SinexField("soln", 9, "U4"),
                SinexField("obs_code", 14, "U1"),
                SinexField("start_time", 16, "O", "epoch"),
                SinexField("end_time", 29, "O", "epoch"),
                SinexField("event_code", 42, "U1"),
                SinexField("description", 44, "U120"),
            ),
            parser=self.parse_discontinuity,
        )

    parse_discontinuity = parsing_factory()
