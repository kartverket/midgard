"""A parser for reading RINEX navigation files with version 2.xx
"""

# Midgard imports
from midgard.dev import plugins
from midgard.parsers.wip_rinex_nav import RinexNavParser
from midgard.parsers.wip_rinex2_nav_header import Rinex2NavHeaderMixin


@plugins.register
class Rinex2NavParser(Rinex2NavHeaderMixin, RinexNavParser):
    """A parser for reading RINEX navigation files with version 2.xx

    """

    pass
