"""A parser for reading GNSS RINEX navigation files

Example:
--------

    from midgard.data import dataset
    from midgard import parsers

    # Parse data
    parser = parsers.parse(file_path=file_path)

    # Create a empty Dataset
    dset = data.Dataset()

    # Fill Dataset with parsed data
    parser.write_to_dataset(dset)


Description:
------------

Reads GNSS ephemeris data from RINEX navigation file in format 2.11 (see :cite:`rinex2`) or 3.03 (see :cite:`rinex3`).

"""
# Standard library imports
import pathlib

# Midgard imports
from midgard import parsers
from midgard.dev import log
from midgard.dev import plugins
from midgard.gnss import gnss


@plugins.register
def get_rinex2_or_rinex3(file_path: pathlib.PosixPath) -> "TODO":
    """Use either Rinex2NavParser or Rinex3NavParser for reading orbit files in format 2.11 or 3.03.

    Firstly the RINEX file version is read. Based on the read version number it is decided, which Parser should be
    used.

    Args:
        file_path (pathlib.PosixPath):  File path to broadcast orbit file.
    """
    version = gnss.get_rinex_file_version(file_path=file_path)
    if version.startswith("2"):
        parser_name = "rinex212_nav" if version == "2.12" else "rinex2_nav"
    elif version.startswith("3"):
        parser_name = "rinex3_nav"
    else:
        log.fatal(f"Unknown RINEX format {version} is used in file {file_path}")

    return parsers.parse_file(parser_name=parser_name, file_path=file_path, use_cache=True)
