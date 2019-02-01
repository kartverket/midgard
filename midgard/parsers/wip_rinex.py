"""A parser for reading Rinex files
"""

# Standard library imports
from typing import Any, Type

# Midgard imports
from midgard.dev import exceptions
from midgard.dev import plugins
from midgard import parsers
from midgard.parsers import wip_rinex_clk, wip_rinex_nav, wip_rinex_obs

_PARSERS = {"C": wip_rinex_clk.rinex_clk, "N": wip_rinex_nav.rinex_nav, "O": wip_rinex_obs.rinex_obs}


@plugins.register
def rinex(**parser_args: Any) -> parsers.RinexParser:
    """Dispatch to correct subclass based on Rinex file type"""
    parser = parsers.RinexParser(**parser_args)
    rinex_info = parser.get_rinex_version_type()

    if rinex_info["file_type"] not in _PARSERS.keys():
        raise exceptions.ParserError(
            f"File {parser.file_path} is a {rinex_info['file_type']!r} file, " f"expected {' '.join(_PARSERS.keys())}"
        )

    file_type = rinex_info["file_type"]

    try:
        return _PARSERS[file_type](**parser_args)
    except KeyError:
        raise exceptions.ParserError(
            f"File {parser.file_path} has file type {rinex_info['file_type']}, which is not supported"
        )
