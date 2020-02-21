"""RINEX navigation header classes for file format version 2.xx
"""
# Standard library imports
from typing import Tuple

# Midgard imports
from midgard.dev import plugins
from midgard.parsers import RinexParser, RinexHeader
from midgard.parsers._parser_rinex import parser_cache, _FieldStr, _FieldVal


class Rinex2NavHeaderMixin:
    """A mixin defining which RINEX navigation headers are mandatory and optional in RINEX version 2.xx"""

    @property
    def mandatory_headers(self) -> Tuple[RinexHeader, ...]:
        return (self.rinex_version__type, self.pgm__run_by__date)

    @property
    def optional_headers(self) -> Tuple[RinexHeader, ...]:
        return (self.comment,)


@plugins.register
class Rinex2NavHeaderParser(Rinex2NavHeaderMixin, RinexParser):
    """A parser for reading just the RINEX version 2.xx navigation header

    The data in the rinex file will not be parsed.
    """

    def read_epochs(self, fid) -> None:
        """Do not read data from Rinex file

        Skip reading of data.
        """
        pass
