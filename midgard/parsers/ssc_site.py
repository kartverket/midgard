"""A parser for reading data from TRF files in SSC format

Description:
------------

Reads station positions and velocities from TRF files in SSC format. The velocity model is a simple linear offset
based on the reference epoch.

"""

# Standard library imports
from datetime import datetime, timedelta
import itertools
import re

# Midgard imports
from midgard.dev import plugins
from midgard.parsers._parser_chain import ParserDef, ChainParser


@plugins.register
class SscSiteParser(ChainParser):
    """A parser for reading data from TRF files in SSC format
    """

    def setup_parser(self):

        # Ignore header
        header_parser = ParserDef(
            end_marker=lambda _l, _ln, nextline: nextline[0:5].isnumeric(), label=None, parser_def=None
        )

        # Every pair of lines contains information about one station
        obs_parser = ParserDef(
            end_marker=lambda line, _ln, _n: line[30:31] == " ",
            label=lambda line, _ln: not line[30:31] == " ",
            parser_def={
                True: {
                    "parser": self.parse_position,
                    "fields": {
                        "site_num": (0, 5),
                        "antenna_num": (5, 9),
                        "name": (10, 26),
                        "tech": (26, 32),
                        "antenna_id": (32, 37),
                        "data": (37, 200),  # Column numbers for data are inconsistent
                    },
                },
                False: {"parser": self.parse_velocity, "fields": {"data": (37, 200)}},
            },
        )

        return itertools.chain([header_parser], itertools.repeat(obs_parser))

    def parse_position(self, line, cache):
        """Parse the position line of TRF data

        This gives the position (x,y,z) of the station. Converting position float.

        Args:
            line (Dict):  The fields of a line.
            cache (Dict): Dict that persists information.
        """
        data_fields = ("STAX", "STAY", "STAZ", "sigma_X", "sigma_Y", "sigma_Z", "soln", "start", "end", "ref_epoch")
        data_values = line.pop("data")
        line.update({k: v for k, v in itertools.zip_longest(data_fields, data_values.split())})
        
        yydddsssss = lambda x : datetime.strptime(x[0:6], "%y:%j") + timedelta(seconds=int(x[7:]))
        
        cache["antenna_id"] = line["antenna_id"]
        line["soln"] = int(line["soln"]) if line["soln"] else 1
        cache["soln"] = line["soln"]
        pos_vel = dict()
        pos_vel.update({k: float(line.pop(k)) for k in list(line.keys()) if k.endswith(("X", "Y", "Z"))})
        line["ref_epoch"] = yydddsssss(line["ref_epoch"])
        pos_vel["ref_epoch"] = line.pop("ref_epoch")
        start = line.pop("start")
        if start and start[3:6] != "000":
            pos_vel["start"] = yydddsssss(start)
        else:
            pos_vel["start"] = datetime.min

        end = line.pop("end")
        if end and end[3:6] != "000":
            pos_vel["end"] = yydddsssss(end)
        else:
            pos_vel["end"] = datetime.max

        self.data.setdefault(cache["antenna_id"], dict())
        self.data[cache["antenna_id"]].update(line)
        self.data[cache["antenna_id"]].setdefault("pos_vel", dict())
        self.data[cache["antenna_id"]]["pos_vel"][line["soln"]] = pos_vel

    def parse_velocity(self, line, cache):
        """Parsing the velocity line of TRF data

        This is given on the line below the line with the position.  Assume that the tech and antenna_id are the
        same as on the line above, so we don't parse this.

        Args:
            line (Dict):  The fields of a line.
            cache (Dict): Dict that persists information.
        """
        data_fields = ("VELX", "VELY", "VELZ", "sigma_VX", "sigma_VY", "sigma_VZ")
        data = {k: float(v) for k, v in zip(data_fields, line["data"].split())}
        self.data[cache["antenna_id"]]["pos_vel"][cache["soln"]].update(data)
        
        