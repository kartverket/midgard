"""A parser for reading data from discontinuities.snx in SINEX format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='discontinuities_snx', file_path='discontinuities_snx')
    data = p.as_dict()

Description:
------------

Reads discontinuities of GNSS station timeseries in SINEX format .


"""
# External libray imports
import numpy as np

# Midgard imports
from midgard.dev import plugins

# Where imports
from midgard.parsers._parser_sinex import SinexParser


@plugins.register
class DiscontinuitiesSnxParser(SinexParser):
    """A parser for reading data from discontinuties.snx file in SINEX format

       The solution discontinuity dictionary has as keys the site identifiers and as value the 'solution_discontinuity'
       entry. The dictionary has following strucuture:

          self.data[site] = { 'solution_discontinuity':  [] }   # SOLUTION/DISCONTINUITY SINEX block information

       with the 'solution_discontinuity' dictionary entries

          solution_discontinuity[ii]     = [ 'point_code':         point_code,
                                             'soln':               soln,
                                             'obs_code':           obs_code,
                                             'start_time':         start_time,
                                             'end_time':           end_time,
                                             'event_code':         event_code,
                                             'description':        description ]

       The counter 'ii' ranges from 0 to n and depends on how many discontinuities exists for a site. Note also, that 
       time entries (e.g. start_time, end_time) are given as 'datetime'. If the time is defined as 00:000:00000 in the
       SINEX file, then the value is saved as 'None' in the Sinex class.
    """

    def setup_parser(self):
        return (self.discontinuity,)

    def parse_discontinuity(self, data: np.ndarray):
        """Parse SOLUTION/DISCONTINUITY SINEX block
        """
        for d in data:
            site_key = d["site_code"].lower()
            add_dict = {n: d[n] for n in d.dtype.names}  # Generate dictionary with all SINEX field entries
            del add_dict["site_code"]
            self.data.setdefault(site_key, dict())
            self.data[site_key].setdefault("solution_discontinuity", list())
            self.data[site_key]["solution_discontinuity"].append(add_dict)
