"""A parser for reading Rinex navigation files
"""

# Standard library imports
from typing import Any

# Midgard imports
from midgard.dev import exceptions
from midgard.dev import plugins
from midgard import parsers


@plugins.register
def rinex_clk(**parser_args: Any) -> parsers.RinexParser:
    """Dispatch to correct subclass based on version in Rinex file"""

    # Import parsers locally to avoid circular imports
    from midgard.parsers import wip_rinex3_clk as rinex3_clk

    _PARSERS = {"3": rinex3_clk.Rinex3ClkParser}

    # Run a basic rinex parser to info from file
    parser = parsers.RinexParser(**parser_args)
    rinex_info = parser.get_rinex_version_type()

    if rinex_info["file_type"] != "C":
        raise exceptions.ParserError(f"File {parser.file_path} is a {rinex_info['file_type']!r} file, expected 'C'")

    version = rinex_info["rinex_version"][0]  # Major version

    try:
        return _PARSERS[version](**parser_args)
    except KeyError:
        raise exceptions.ParserError(
            f"File {parser.file_path} is version {rinex_info['rinex_version']}, " f"which is not supported"
        )


class RinexClkParser(parsers.RinexParser):
    """ Class for defining common methods for RINEX clock parsers.
    """

    pass
