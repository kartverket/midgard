"""A parser for reading Rinex navigation files
"""

# Standard library imports
from typing import Any, Type

# Midgard imports
from midgard.dev import exceptions
from midgard.dev import plugins
from midgard import parsers


@plugins.register
def rinex_nav(**parser_args: Any) -> parsers.RinexParser:
    """Dispatch to correct subclass based on version in Rinex file"""

    # Import parsers locally to avoid circular imports
    from midgard.parsers import wip_rinex2_nav as rinex2_nav, wip_rinex3_nav as rinex3_nav

    _PARSERS = {"2": rinex2_nav.Rinex2NavParser, "3": rinex3_nav.Rinex3NavParser}

    # Run a basic rinex parser to info from file
    parser = parsers.RinexParser(**parser_args)
    rinex_info = parser.get_rinex_version_type()

    if rinex_info["file_type"] != "N":
        raise exceptions.ParserError(f"File {parser.file_path} is a {rinex_info['file_type']!r} file, expected 'N'")

    version = rinex_info["rinex_version"][0]  # Major version

    try:
        return _PARSERS[version](**parser_args)
    except KeyError:
        raise exceptions.ParserError(
            f"File {parser.file_path} is version {rinex_info['rinex_version']}, " f"which is not supported"
        )


class RinexNavParser(parsers.RinexParser):
    """ Class for defining common methods for RINEX navigation parsers.
    """

    pass
