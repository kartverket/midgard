"""A parser for reading RINEX clock files with version 3.xx
"""

# Midgard imports
from midgard.dev import plugins
from midgard.parsers.wip_rinex_clk import RinexClkParser
from midgard.parsers.wip_rinex3_clk_header import Rinex3ClkHeaderMixin


@plugins.register
class Rinex3ClkParser(Rinex3ClkHeaderMixin, RinexClkParser):
    """A parser for reading RINEX clock files with version 3.xx
    """

    pass
