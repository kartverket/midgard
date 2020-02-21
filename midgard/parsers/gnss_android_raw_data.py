"""A parser for reading GNSS raw data from `GnssLogger` Android App

Example:
--------
    
    from midgard import parsers
    
    # Parse data
    parser = parsers.parse_file(parser_name="gnss_android_raw_data", file_path=file_path)
    
    # Get Dataset with parsed data
    dset = parser.as_dataset()

Description:
------------

Reads raw data file from `GnssLogger` Android App.

"""

# Standard library imports
import itertools
from typing import Any, Callable, Dict, Iterable, List

# External library imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.data.position import Position
from midgard.data.time import Time
from midgard.dev import plugins
from midgard.dev import log
from midgard.math.constant import constant
from midgard.math.unit import Unit
from midgard.parsers import ChainParser, ParserDef


@plugins.register
class GnssAndroidRawDataParser(ChainParser):
    """
    """

    # MURKS  if station:
    #      self.vars["station"] = station.lower()
    #      self.vars["STATION"] = station.upper()

    #
    # PARSERS
    #
    def setup_parser(self) -> Iterable[ParserDef]:
        """Parsers defined for reading GNSS raw data file line by line.
        """
        file_parser = ParserDef(
            end_marker=lambda _l, _ln, _n: True,
            label=lambda line, _ln: line[0:3].strip(),
            parser_def={
                # # Fix,Provider,Latitude,Longitude,Altitude,Speed,Accuracy,(UTC)TimeInMs
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
                # Fix,gps,37.422541,-122.081659,-33.000000,0.000000,3.000000,1467321969000
                "Fix": {
                    "parser": self._parse_fix,
                    "delimiter": ",",
                    "fields": [
                        "dummy",
                        "provider",
                        "latitude",
                        "longitude",
                        "altitude",
                        "speed",
                        "accuracy",
                        "time_utc",
                    ],
                },
                # # Raw,ElapsedRealtimeMillis,TimeNanos,LeapSecond,TimeUncertaintyNanos,FullBiasNanos,BiasNanos, ...
                # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0
                # Raw,72065126,72076939000000,,,-1151285108458178048,0.0,26.542398700257763,-0.634638974724185, ...
                "Raw": {
                    "parser": self._parse_raw,
                    "delimiter": ",",
                    "fields": [
                        "dummy",
                        "ElapsedRealtimeMillis",
                        "TimeNanos",
                        "LeapSecond",
                        "TimeUncertaintyNanos",
                        "FullBiasNanos",
                        "BiasNanos",
                        "BiasUncertaintyNanos",
                        "DriftNanosPerSecond",
                        "DriftUncertaintyNanosPerSecond",
                        "HardwareClockDiscontinuityCount",
                        "Svid",
                        "TimeOffsetNanos",
                        "State",
                        "ReceivedSvTimeNanos",
                        "ReceivedSvTimeUncertaintyNanos",
                        "Cn0DbHz",
                        "PseudorangeRateMetersPerSecond",
                        "PseudorangeRateUncertaintyMetersPerSecond",
                        "AccumulatedDeltaRangeState",
                        "AccumulatedDeltaRangeMeters",
                        "AccumulatedDeltaRangeUncertaintyMeters",
                        "CarrierFrequencyHz",
                        "CarrierCycles",
                        "CarrierPhase",
                        "CarrierPhaseUncertainty",
                        "MultipathIndicator",
                        "SnrInDb",
                        "ConstellationType",
                    ],
                },
            },
        )

        return itertools.repeat(file_parser)

    def _parse_fix(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse 'Fix' entries of GNSS raw data file to instance variable 'data'.
        """
        for k, v in line.items():
            if k == "dummy":
                continue
            if k == "provider":
                self.data.setdefault(k, list()).append(v)
                continue

            self.data.setdefault(k, list()).append(float(v))

    def _parse_raw(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        """Parse 'Raw' entries of GNSS raw data file to instance variable 'data'.
        """
        # TODO: Make parsing depending of 'State' value. What do the 'State' numbers mean?
        constellationType = {"0": None, "1": "G", "2": "S", "3": "R", "4": "J", "5": "C", "6": "E"}

        for k, v in line.items():
            if k == "dummy":
                continue
            if k == "Svid":
                system = constellationType[line["ConstellationType"]]
                if system == None:
                    log.warn("GNSS is unknown.")
                    continue
                self.data.setdefault("system", list()).append(system)
                self.data.setdefault("satellite", list()).append(system + str(v).zfill(2))
            if v == "":
                v = float("nan")

            self.data.setdefault(k, list()).append(float(v))

    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        """
        return [self._determine_pseudorange, self._get_sitepos]

    def _determine_pseudorange(self) -> None:
        """Determine pseudorange based on ION 2016 tutorial "Raw GNSS Measurements from Android Phones".
        """

        # Determine GPS week
        week = np.floor(-np.array(self.data["FullBiasNanos"]) * Unit.nanosecond2second / 604800)

        # GNSS signal arriving time at measurement time (GPS time) referenced to GPS week
        tRxNanos = (
            (np.array(self.data["TimeNanos"], dtype=float) + np.array(self.data["TimeOffsetNanos"], dtype=float))
            - (np.array(self.data["FullBiasNanos"], dtype=float) + np.array(self.data["BiasNanos"], dtype=float))
            - (week * 604800e9)
        )

        if np.all(tRxNanos >= 604800e9):
            log.fatal("tRxNanos should be <= GPS nanoseconds.")
        if np.all(tRxNanos <= 0.0):
            log.fatal("tRxNanos should be >= 0.")

        self.data["week"] = week
        self.data["tRxNanos"] = tRxNanos
        self.data["time"] = Time(val=week, val2=tRxNanos * Unit.nanosecond2second, fmt="gps_ws", scale="gps")

        # GNSS satellite transmission time at measurement time (GPS time) referenced to GPS week
        tTxNanos = np.array(self.data["ReceivedSvTimeNanos"], dtype=float)

        self.data["sat_time"] = Time(val=week, val2=tTxNanos * Unit.nanosecond2second, fmt="gps_ws", scale="gps")
        # TODO: Check GPS week rollover (see ProcessGnssMeas.m)

        self.data["pseudorange"] = (tRxNanos - tTxNanos) * Unit.nanosecond2second * constant.c  # in meters

    def _get_sitepos(self) -> None:
        """Determine site position by converting given longitude, latitude and height for a station to geocentric
           cartesian coordinates
        """
        if "latitude" in self.data.keys():
            x = self.data["latitude"][0] * Unit.deg2rad
            y = self.data["longitude"][0] * Unit.deg2rad
            z = self.data["altitude"][0]
            system = "llh"
        else:
            x = y = z = 0
            system = "trs"

        self.data["site_pos"] = Position(
            val=np.repeat(np.array([x, y, z])[None, :], len(self.data["pseudorange"]), axis=0), system=system
        )

    #
    # WRITE DATA
    #
    def as_dataset(self):
        """Store GNSS data in a dataset

        Returns:
            Midgard Dataset where data are stored.
        """
        dset = dataset.Dataset(num_obs=len(self.data["pseudorange"]))

        dset.add_float("C1C", val=self.data["pseudorange"])

        import IPython

        IPython.embed()
        # TODO: why does dset.add_time("time", val=self.data["time"]) not work?
        dset.add_time("time", val=self.data["time"].gps.datetime, scale="gps", fmt="datetime")
        # dset.add_time('sat_time', val=self.data["sat_time"].gps.datetime, scale="gps", fmt="datetime")

        dset.add_text("station", val=np.full(dset.num_obs, "android", dtype=str))
        dset.add_text("satellite", val=self.data["satellite"])
        dset.add_text("satnum", val=self.data["Svid"])
        dset.add_text("system", val=self.data["system"])
        dset.add_position("site_pos", time=dset.time, val=self.data["site_pos"])

        return dset
