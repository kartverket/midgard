"""A parser for reading data from TRF files in SSC format

Description:
------------

Reads station positions and velocities from TRF files in SSC format. The velocity model is a simple linear offset
based on the reference epoch.

"""

# Standard library imports
from datetime import datetime, timedelta
import itertools

# Midgard imports
from midgard.dev import plugins
from midgard.parsers._parser_chain import ParserDef, ChainParser


@plugins.register
class SscSiteParser(ChainParser):
    """A parser for reading data from TRF files in SSC format
    """

    #
    #                CLASS_A EPN STATION POSITIONS AND VELOCITIES
    #                REFERENCE FRAME:    IGb14    AT EPOCH OF 2010.0
    #                CUMULATIVE SOLUTION OF GPSWEEKS [ 0834 - 2145 ]
    #                RELEASE NAME:    EPN_A_IGb14_C2145
    #                RELEASED ON 11/04/2021 BY EPN REFERENCE FRAME COORDINATOR (Juliette LEGRAND, ROB, BELGIUM)
    # DOMES NB. SITE NAME        TECH. ID.       X/Vx         Y/Vy         Z/Vz.          Sigmas      SOLN  DATA_START     DATA_END   REF. EPOCH
    #               CLASS                   ----------------------------m/m/Y-------------------------
    # ------------------------------------------------------------------------------------------------------------------------------------------
    # 10001M007 SMNE              GPS SMNE  4201791.972   177945.561  4779286.951  0.001  0.001  0.001  1 00:322:00000 08:118:86370 10:001:00000
    # 10001M007                                  -.0130       0.0175       0.0106 0.0001 0.0001 0.0001
    # 10001M007 SMNE              GPS SMNE  4201791.982   177945.564  4779286.960  0.001  0.001  0.001  2 08:120:00000 09:069:86370 10:001:00000
    # 10001M007                                  -.0130       0.0175       0.0106 0.0001 0.0001 0.0001
    # 10001M007 SMNE              GPS SMNE  4201791.988   177945.558  4779286.960  0.001  0.001  0.001  3 09:071:00000 11:120:86370 10:001:00000
    # 10001M007                                  -.0130       0.0175       0.0106 0.0001 0.0001 0.0001
    # 10001M007 SMNE              GPS SMNE  4201791.977   177945.564  4779286.955  0.001  0.001  0.001  4 11:128:00000 15:272:86370 10:001:00000
    # 10001M007                                  -.0130       0.0175       0.0106 0.0001 0.0001 0.0001
    # 10001M007 SMNE              GPS SMNE  4201791.978   177945.564  4779286.955  0.001  0.001  0.001  5 15:274:00000 21:051:86370 10:001:00000
    # 10001M007                                  -.0130       0.0175       0.0106 0.0001 0.0001 0.0001
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----
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
                        "domes": (0, 5),
                        "marker": (5, 9),
                        "name": (10, 26),
                        "tech": (26, 32),
                        "site_id": (32, 37),
                        "data": (37, 200),  # Column numbers for data are inconsistent
                    },
                },
                False: {"parser": self.parse_velocity, "fields": {"data": (37, 200)}},
            },
        )

        return itertools.chain([header_parser], itertools.repeat(obs_parser))
    

    # 10001M007 SMNE              GPS SMNE  4201791.972   177945.561  4779286.951  0.001  0.001  0.001  1 00:322:00000 08:118:86370 10:001:00000
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----
    def parse_position(self, line, cache):
        """Parse the position line of TRF data

        This gives the position (x,y,z) of the station. Converting position float.

        Args:
            line (Dict):  The fields of a line.
            cache (Dict): Dict that persists information.
        """
        data_fields = ("STAX", "STAY", "STAZ", "sigma_x", "sigma_y", "sigma_z", "soln", "start", "end", "ref_epoch")
        data_values = line.pop("data")
        line.update({k: v for k, v in itertools.zip_longest(data_fields, data_values.split())})
        line["site_id"] = line["site_id"].lower()
        
        yydddsssss = lambda x : datetime.strptime(x[0:6], "%y:%j") + timedelta(seconds=int(x[7:]))
        
        cache["site_id"] = line["site_id"]
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

        self.data.setdefault(cache["site_id"], dict())
        self.data[cache["site_id"]].update(line)
        self.data[cache["site_id"]].setdefault("pos_vel", dict())
        self.data[cache["site_id"]]["pos_vel"][line["soln"]] = pos_vel


    # 10001M007                                  -.0130       0.0175       0.0106 0.0001 0.0001 0.0001
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+--
    def parse_velocity(self, line, cache):
        """Parsing the velocity line of TRF data

        This is given on the line below the line with the position.  Assume that the tech and site_id are the
        same as on the line above, so we don't parse this.

        Args:
            line (Dict):  The fields of a line.
            cache (Dict): Dict that persists information.
        """
        data_fields = ("VELX", "VELY", "VELZ", "sigma_vx", "sigma_vy", "sigma_vz")
        data = {k: float(v) for k, v in zip(data_fields, line["data"].split())}
        self.data[cache["site_id"]]["pos_vel"][cache["soln"]].update(data)
        
        