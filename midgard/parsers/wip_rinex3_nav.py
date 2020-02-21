"""A parser for reading RINEX navigation files with version 3.xx
"""

# Midgard imports
from midgard.dev import plugins
from midgard.parsers.wip_rinex_nav import RinexNavParser
from midgard.parsers.wip_rinex3_nav_header import Rinex3NavHeaderMixin


@plugins.register
class Rinex3NavParser(Rinex3NavHeaderMixin, RinexNavParser):
    """A parser for reading RINEX navigation files with version 3.xx

    """

    pass
