"""A parser for reading data from events.snx in SINEX format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='events_snx', file_path='events_snx')
    data = p.as_dict()

Description:
------------

Reads events related to GNSS configuration, environment changes or station timeseries data problems in SINEX format .


"""
# External libray imports
import numpy as np

# Midgard imports
from midgard.dev import plugins

# Where imports
from midgard.parsers._parser_sinex import SinexParser


@plugins.register
class EventsSnxParser(SinexParser):
    """A parser for reading data from events.snx file in SINEX format

       The solution events dictionary has as keys the site identifiers and as value the 'solution_event'
       entry. The dictionary has following strucuture:

          self.data[site] = { 'solution_event':  [] }   # SOLUTION/EVENT SINEX block information

       with the 'solution_event' dictionary entries

          solution_event[ii]    = [ 'point_code':         point_code,
                                    'soln':               soln,
                                    'obs_code':           obs_code,
                                    'start_time':         start_time,
                                    'end_time':           end_time,
                                    'event_code':         event_code,
                                    'description':        description ]

       The counter 'ii' ranges from 0 to n and depends on how many events exists for a site. Note also, that 
       time entries (e.g. start_time, end_time) are given as 'datetime'. If the time is defined as 00:000:00000 in the
       SINEX file, then the value is saved as 'None' in the Sinex class.
    """

    def setup_parser(self):
        return (self.solution_event,)

    def parse_solution_event(self, data: np.ndarray):
        """Parse SOLUTION/EVENT SINEX block
        """
        for d in data:
            site_key = d["site_code"].lower()
            add_dict = {n: d[n] for n in d.dtype.names}  # Generate dictionary with all SINEX field entries
            del add_dict["site_code"]
            self.data.setdefault(site_key, dict())
            self.data[site_key].setdefault("solution_event", list())
            self.data[site_key]["solution_event"].append(add_dict)
