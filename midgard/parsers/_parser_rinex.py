"""Basic functionality for parsing Rinex files

Description:
------------

This module contains functions and classes for parsing Rinex files.

This file defines the general structure shared by most types of Rinex files, including header information. More
specific format details are implemented in subclasses. When calling the parser, you should call the apropriate parser
for a given Rinex format.

"""
# Standard library imports
from datetime import datetime
import functools
import itertools
import pathlib
from typing import Any, Callable, cast, Dict, List, NamedTuple, Optional, Tuple, Union

import numpy as np

# Midgard imports
from midgard.dev import exceptions
from midgard.dev import log
from midgard.parsers._parser import Parser

# Custom types
_FieldDef = Dict[str, Tuple[int, int]]
_FieldStr = Dict[str, str]
_FieldVal = Dict[str, Any]
_FieldCache = List[_FieldStr]


# A simple structure used to define the necessary fields of a parser
class RinexHeader(NamedTuple):
    """A convenience class for defining how a Rinex header is parsed

    Args:
        marker:  Marker of header (as defined in columns 60 and onward).
        fields:  Dictionary with field names as keys, tuple of start- and end-columns as value.
        parser:  Function that will parse the fields.
    """

    marker: str
    fields: _FieldDef
    parser: Callable[[_FieldStr], _FieldVal]


def parser_cache(
    func: Callable[["RinexParser", _FieldStr, _FieldCache], _FieldVal],
) -> Callable[["RinexParser", _FieldStr], _FieldVal]:
    """Decorator for adding a cache to parser functions"""
    func.cache = list()  # type: ignore  # mypy is not picking up .cache

    @functools.wraps(func)
    def wrapper_parser_cache(self: "RinexParser", fields: _FieldStr) -> _FieldVal:
        value = func(self, fields, func.cache)  # type: ignore
        func.cache.append(fields)  # type: ignore
        return value

    return wrapper_parser_cache


class RinexParser(Parser):
    """An abstract base class that has basic methods for parsing a datafile

    This class provides functionality for reading Rinex header data. You should inherit from this one,
    and at least implement `parse_epochs`.
    """

    name = "Rinex"

    def __init__(
        self,
        file_path: Union[str, pathlib.Path],
        encoding: Optional[str] = None,
        logger=print,
        sampling_rate: Optional[int] = None,
        strict: bool = False,
    ) -> None:
        """Set up the basic information needed by the parser

        Args:
            file_path:      Path to file that will be read.
            encoding:       Encoding of file that will be read.
            sampling_rate:  If given, decimate the file to sampling_rate.
            strict:         Raise error if file does not conform with format.
        """
        super().__init__(file_path, encoding)
        self.meta["__kwargs__"] = dict(
            file_path=file_path, encoding=encoding, sampling_rate=sampling_rate, strict=strict
        )
        self.header: Dict[str, Any] = dict()
        self.samling_rate = sampling_rate
        self.error = cast(Callable[[str], None], self._raise_error if strict else log.warn)

    def _raise_error(self, text: str) -> None:
        """Raise a parser error"""
        raise exceptions.ParserError(text)

    def get_rinex_version_type(self) -> Dict[str, str]:
        """Get version and type of Rinex file"""
        header_def = self.rinex_version__type

        with open(self.file_path, mode="r", encoding=self.file_encoding) as fid:
            for line in fid:
                marker = line[60:80].strip()
                if marker != header_def.marker:
                    self.error(f"Wrong marker {marker!r} before version information")
                    continue
                return {k: line[slice(*v)].strip() for k, v in header_def.fields.items()}

        raise exceptions.ParserError(f"No information about Rinex version found in {self.file_path}")

    @property
    def mandatory_headers(self) -> Tuple[RinexHeader, ...]:
        raise NotImplementedError

    @property
    def optional_headers(self) -> Tuple[RinexHeader, ...]:
        raise NotImplementedError

    def read_data(self) -> None:
        """Read data from the data file

        """
        with open(self.file_path, mode="r", encoding=self.file_encoding) as fid:
            self.read_header(fid)
            self.read_epochs(fid)

        self.structure_data()

    def read_header(self, fid) -> None:
        """Read header from the rinex file

        Add header information to self.header
        """
        headers = {h.marker: h for h in self.mandatory_headers + self.optional_headers}
        mandatory_markers = {h.marker for h in self.mandatory_headers}

        # Read header lines
        for line in fid:
            marker = line[60:80].strip()
            if marker == "END OF HEADER":
                break
            if marker in headers:
                header_def = headers[marker]
                fields = {k: line[slice(*v)].strip() for k, v in header_def.fields.items()}
                self.header.update(header_def.parser(fields))
                if marker in mandatory_markers:
                    mandatory_markers.remove(marker)
            else:
                self.error(f"Unknown {self.name} header {marker!r}")

        # Warn if any mandatory markers are not present
        for marker in mandatory_markers:
            self.error(f"Mandatory {self.name} header {marker!r} not found")

    def read_epochs(self, fid) -> None:
        """Read data from Rinex file

        Add data to self.data
        """
        sampling_rate = 400  # TODO: Why does not self.sampling_rate work?
        prev_epoch = datetime.min
        for epoch_line in fid:
            num_data_lines, epoch_info = self.parse_epoch_line(epoch_line)
            data_lines = itertools.islice(fid, num_data_lines)

            if sampling_rate is not None:
                epoch = epoch_info["epoch"]
                if (epoch - prev_epoch).total_seconds() < sampling_rate:
                    for line in data_lines:
                        pass  # Consume lines  # TODO: Better way for this?
                    continue
                prev_epoch = epoch

            data_info = self.parse_data_lines(data_lines, epoch_info)

    def parse_epoch_line(self, line):
        raise NotImplementedError

    def parse_data_lines(self, lines, epoch_info):
        raise NotImplementedError

    def structure_data(self) -> None:
        """Convert lists of data to numpy arrays
        """
        for system, sys_data in self.data.items():
            self.data[system] = {k: np.array(v) for k, v in sys_data.items()}

    #
    # HEADER PARSERS
    #
    def parse_approx_position(self, fields: _FieldStr) -> _FieldVal:
        """Parse station coordinates defined in RINEX header to instance variable `data`
        """
        pos = np.array((float(fields["pos_x"]), float(fields["pos_y"]), float(fields["pos_z"])))
        return dict(pos=pos)

    def parse_comment(self, fields: _FieldStr) -> _FieldVal:
        """Parse comment lines in RINEX header to instance variable `header['comment']`
        """
        comment = self.header.setdefault("comment", [])
        comment.append(fields["comment"])
        return dict(comment=comment)

    def parse_float(self, fields: _FieldStr) -> _FieldVal:
        """Parse float entries of RINEX header to instance variable `header`
        """
        return {k: float(v) for k, v in fields.items() if v}

    def parse_glonass_code_phase_bias(self, fields: _FieldStr) -> _FieldVal:
        """Parse GLONASS phase correction in RINEX header to instance variable `header['glonass_bias']`

            self.header['glonass_bias'] = { <obstype>: <bias in meters>}
        """
        glonass_bias = self.header.setdefault("glonass_bias", {})
        for field in fields.values():
            if field:  # Check if field is not empty.
                type_, bias = field.split()[0:2]
                glonass_bias.update({type_: float(bias)})
        return glonass_bias

    def parse_glonass_slot(self, fields: _FieldStr) -> _FieldVal:
        """Parse GLONASS slot and frequency numbers given in RINEX header to instance variable `header['glonass_slot']`

            self.header['glonass_slot'] = { <slot>: <frequency number>}
        """
        glonass_slot = self.header.setdefault("glonass_slot", {})

        if "num_satellite" in fields:
            num_sat = fields["num_satellite"]
            del fields["num_satellite"]

        for field in fields.values():
            if field:  # Check if field is not empty.
                slot, freq = field.split()[0:2]
                glonass_slot.update({slot: int(freq)})

        # TODO: How can that be checked after all lines are read?
        # lines = cache + [fields]
        # lines
        # int(lines[0]["num_satellite"])
        # " ".join(s["satellites"] for s in lines)
        # " ".join(d["satellites"] for d in lines)
        # (" ".join(d["satellites"] for d in lines)).split()
        # len((" ".join(d["satellites"] for d in lines)).split())
        # if num_sat != len(glonass_slot):
        #    #TODO: How to define a warning?
        #    raise exceptions.ParserError(f"Listed number of GLONASS satellites ({len(glonass_slot)}) is not as expected (number of satellites {num_sat}).")
        return glonass_slot

    def parse_integer(self, fields: _FieldStr) -> _FieldVal:
        """Parse integer entries of RINEX header to instance variable `header`
        """
        return {k: int(v) for k, v in fields.items() if v}

    def parse_leap_seconds(self, fields: _FieldStr) -> _FieldVal:
        """Parse entries of RINEX header `LEAP SECONDS` to instance variable `header`

            self.header['leap_seconds'] = { 'leap_seconds': <value>,
                                            'future_past_leap_seconds': <value>,
                                            'week': <value>,
                                            'week_day': <value>,
                                            'time_sys': <system> }
        """
        return dict(leap_seconds={k: v for k, v in fields.items() if v})

    @parser_cache
    def parse_phase_shift(self, fields: _FieldStr, cache: _FieldCache) -> _FieldVal:
        """Parse entries of RINEX header `SYS / PHASE SHIFT` to instance variable `header`

            self.header['phase_shift'] = { <sat_sys>: { <obs_type>: { corr: <correction>,
                                                                    sat: <[satellite list]>}}}

        Example of `phase_shift` header entry:

            self.header['phase_shift'] =  {'G': {'L1C': {'corr': '0.00000',
                                                       'sat': ['G01', 'G02', 'G03', ...]},
                                                 'L1W': {'corr': '0.00000',
                                                       'sat': []}},
                                          'R': {'L1C': {'corr': '0.00000',
                                                       'sat': ['R01', 'R02', 'R07', 'R08']}}}

        TODO: Maybe better to add information to header['obstypes']?
        TODO: Check of number of satellites
        """
        phase_shift = self.header.setdefault("phase_shift", {})

        if fields["sat_sys"]:
            sat_sys = fields["sat_sys"]
            obs_type = fields["obs_type"]
            phase_shift.setdefault(sat_sys, {}).update({obs_type: {}})
        else:
            sat_sys, obs_type = next((c["sat_sys"], c["obs_type"]) for c in cache[::-1] if c["sat_sys"])

        if fields["correction"]:
            phase_shift[sat_sys][obs_type].update(
                {"corr": float(fields["correction"]), "sat": fields["satellites"].split()}
            )
            return phase_shift

        if fields["satellites"]:
            phase_shift[sat_sys][obs_type]["sat"].extend(fields["satellites"].split())

        return phase_shift

    def parse_scale_factor(self, fields: _FieldStr) -> _FieldVal:
        """Parse entries of RINEX header `SYS / SCALE FACTOR` to instance variable `header`
        """
        return NotImplementedError

    def parse_string(self, fields: _FieldStr) -> _FieldVal:
        """Parse string entries of RINEX header to instance variable 'header'
        """
        return {k: v for k, v in fields.items() if v}

    def parse_sys_dcbs_applied(self, fields: _FieldStr) -> _FieldVal:
        """Parse entries of RINEX header `SYS / DCBS APPLIED` to instance variable `header`

            self.header['dcbs_applied'] = { <sat_sys>: { prg: <used program>,
                                                         url: <source url>}}
        """
        # self.header.setdefault("leap_seconds", {}).update({k: v for k, v in fields.items() if v})
        return fields
        # self.header.setdefault("dcbs_applied", {}).update(
        #    {line["sat_sys"]: {"prg": line["program"], "url": line["source"]}}
        # )

    @parser_cache
    def parse_sys_obs_types(self, fields: _FieldStr, cache: _FieldCache) -> _FieldVal:
        """Parse observation types given in RINEX header to instance variable `header['obstypes']` and data

        The data dictionaries `obs`, `cycle_slip` and `signal_strength` are initialized based on the given observation
        type in the RINEX header.

            self.header['obstypes'] = { <sat_sys>: [<ordered list with given observation types>]}
        """
        satellite_sys = fields["satellite_sys"]
        prev_idx = -1
        while not satellite_sys:
            satellite_sys = cache[prev_idx]["satellite_sys"]
            prev_idx -= 1

        obs_types = self.header.get("obs_types", dict())
        obs_list = obs_types.setdefault(satellite_sys, list())
        for field in sorted([f for f in fields if f.startswith("type_")]):
            if fields[field]:
                obs_list.append(fields[field])

        return dict(obs_types=obs_types)

    def parse_sys_pcvs_applied(self, fields: _FieldStr) -> _FieldVal:
        """Parse entries of RINEX header `SYS / PCVS APPLIED` to instance variable `header`

            self.header['pcvs_applied'] = { <sat_sys>: { prg: <used program>,
                                                       url: <source url>}}
        """
        return fields
        # self.header.setdefault("pcvs_applied", {}).update(
        #    {line["sat_sys"]: {"prg": line["program"], "url": line["source"]}}
        # )

    def parse_time_of_first_obs(self, fields: _FieldStr) -> _FieldVal:
        """Parse time of first observation given in RINEX header to instance variable `header`
        """
        return fields
        # if line["time_sys"] != "GPS":
        #    log.fatal("Time system {} is not handled so far in Where.", line["time_sys"])

        # if line["time_sys"] not in self.header:
        #    self.header["time_sys"] = line["time_sys"]
        # else:
        #    if line["time_sys"] != self.header["time_sys"]:
        #        log.fatal(
        #            "Time system definition in 'TIME OF FIRST OBS' ({}) and 'TIME OF LAST OBS' ({}) are not"
        #            "identical.",
        #            line["time_sys"],
        #            self.header["time_sys"],
        #        )

        # if line["year"]:
        #    self.header["time_first_obs"] = (
        #        "{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:010.7f}"
        #        "".format(
        #            year=int(line["year"]),
        #            month=int(line["month"]),
        #            day=int(line["day"]),
        #            hour=int(line["hour"]),
        #            minute=int(line["minute"]),
        #            second=float(line["second"]),
        #        )
        #    )

    def parse_time_of_last_obs(self, fields: _FieldStr) -> _FieldVal:
        """Parse time of last observation given in RINEX header to instance variable `header`
        """
        return fields
        # if line["time_sys"] != "GPS":
        #    log.fatal("Time system {} is not handled so far in Where.", line["time_sys"])

        # if line["time_sys"]:
        #    if line["time_sys"] not in self.header:
        #        self.header["time_sys"] = line["time_sys"]
        #    else:
        #        if line["time_sys"] != self.header["time_sys"]:
        #            log.fatal(
        #                "Time system definition in 'TIME OF FIRST OBS' ({}) and 'TIME OF LAST OBS' ({}) are"
        #                "not identical.",
        #                self.header["time_sys"],
        #                line["time_sys"],
        #            )

        # if line["year"]:
        #    self.header["time_last_obs"] = (
        #        "{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:010.7f}"
        #        "".format(
        #            year=int(line["year"]),
        #            month=int(line["month"]),
        #            day=int(line["day"]),
        #            hour=int(line["hour"]),
        #            minute=int(line["minute"]),
        #            second=float(line["second"]),
        #        )
        #    )

    #
    # HEADER DEFINITIONS
    #
    @property
    def rinex_version__type(self) -> RinexHeader:
        """Parser definition for RINEX header label 'RINEX VERSION / TYPE'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
                 3.02           OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
        """
        return RinexHeader(
            marker="RINEX VERSION / TYPE",
            fields={"rinex_version": (0, 20), "file_type": (20, 21), "sat_sys": (40, 41)},
            parser=self.parse_string,
        )

    @property
    def pgm__run_by__date(self) -> RinexHeader:
        """Parser definition for RINEX header label 'PGM / RUN BY / DATE'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            MAKERINEX 2.0.20023 BKG/GOWETTZELL      2016-03-02 00:20    PGM / RUN BY / DATE
        """
        return RinexHeader(
            marker="PGM / RUN BY / DATE",
            fields={"program": (0, 20), "run_by": (20, 40), "file_created": (40, 60)},
            parser=self.parse_string,
        )

    @property
    def comment(self) -> RinexHeader:
        """Parser definition for RINEX header label 'COMMENT'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            G = GPS R = GLONASS E = GALILEO S = GEO M = MIXED           COMMENT
        """
        return RinexHeader(marker="COMMENT", fields={"comment": (0, 60)}, parser=self.parse_comment)

    @property
    def marker_name(self) -> RinexHeader:
        """Parser definition for RINEX header label 'MARKER NAME'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            stas                                                        MARKER NAME
        """
        return RinexHeader(marker="MARKER NAME", fields={"marker_name": (0, 60)}, parser=self.parse_string)

    @property
    def marker_number(self) -> RinexHeader:
        """Parser definition for RINEX header label 'MARKER NUMBER'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            66008M005                                                   MARKER NUMBER
        """
        return RinexHeader(marker="MARKER NUMBER", fields={"marker_number": (0, 20)}, parser=self.parse_string)

    @property
    def marker_type(self) -> RinexHeader:
        """Parser definition for RINEX header label ''
        """
        return RinexHeader(marker="MARKER TYPE", fields={"marker_type": (0, 20)}, parser=self.parse_string)

    @property
    def observer__agency(self) -> RinexHeader:
        """Parser definition for RINEX header label 'OBSERVER / AGENCY'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            SATREF              Norwegian Mapping Authority             OBSERVER / AGENCY
        """
        return RinexHeader(
            marker="OBSERVER / AGENCY", fields={"observer": (0, 20), "agency": (20, 60)}, parser=self.parse_string
        )

    @property
    def rec_num__type__vers(self) -> RinexHeader:
        """Parser definition for RINEX header label 'REC # / TYPE / VERS'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            3008040             SEPT POLARX4        2.9.0               REC # / TYPE / VERS
        """
        return RinexHeader(
            marker="REC # / TYPE / VERS",
            fields={"receiver_number": (0, 20), "receiver_type": (20, 40), "receiver_version": (40, 60)},
            parser=self.parse_string,
        )

    @property
    def ant_num__type(self) -> RinexHeader:
        """Parser definition for RINEX header label 'ANT # / TYPE'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            CR620012101         ASH701945C_M    SCIS                    ANT # / TYPE
        """
        return RinexHeader(
            marker="ANT # / TYPE",
            fields={"antenna_number": (0, 20), "antenna_type": (20, 40)},
            parser=self.parse_string,
        )

    @property
    def approx_position_xyz(self) -> RinexHeader:
        """Parser definition for RINEX header label 'APPROX POSITION XYZ'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
              3275756.7623   321111.1395  5445046.6477                  APPROX POSITION XYZ
        """
        return RinexHeader(
            marker="APPROX POSITION XYZ",
            fields={"pos_x": (0, 14), "pos_y": (14, 28), "pos_z": (28, 42)},
            parser=self.parse_approx_position,
        )

    @property
    def antenna__delta_hen(self) -> RinexHeader:
        """Parser definition for RINEX header label 'ANTENNA: DELTA H/E/N'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
                    0.0000        0.0000        0.0000                  ANTENNA: DELTA H/E/N
        """
        return RinexHeader(
            marker="ANTENNA: DELTA H/E/N",
            fields={"antenna_height": (0, 14), "antenna_east": (14, 28), "antenna_north": (28, 42)},
            parser=self.parse_float,
        )

    @property
    def antenna__delta_xyz(self) -> RinexHeader:
        """Parser definition for RINEX header label 'ANTENNA: DELTA X/Y/Z'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
                    0.0000        0.0000        0.0000                  ANTENNA: DELTA X/Y/Z
        """
        return RinexHeader(
            marker="ANTENNA: DELTA X/Y/Z",
            fields={"ant_vehicle_x": (0, 14), "ant_vehicle_y": (14, 28), "ant_vehicle_z": (28, 42)},
            parser=self.parse_float,
        )

    # TODO: 'ANTENNA:PHASECENTER'
    # TODO: 'ANTENNA:B.SIGHT XYZ'
    # TODO: 'ANTENNA:ZERODIR AZI'
    # TODO: 'ANTENNA:ZERODIR XYZ'
    # TODO: 'CENTER OF MASS: XYZ'

    @property
    def sys__num__obs_types(self) -> RinexHeader:
        """Parser definition for RINEX header label 'SYS / # / OBS TYPES'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            G   26 C1C C1P L1C L1P D1C D1P S1C S1P C2P C2W C2S C2L C2X  SYS / # / OBS TYPES
                   L2P L2W L2S L2L L2X D2P D2W D2S D2L D2X S2P S2W S2S  SYS / # / OBS TYPES
            R   16 C1C C1P L1C L1P D1C D1P S1C S1P C2C C2P L2C L2P D2C  SYS / # / OBS TYPES
                   D2P S2C S2P                                          SYS / # / OBS TYPES
        """
        return RinexHeader(
            marker="SYS / # / OBS TYPES",
            fields={
                "satellite_sys": (0, 1),
                "num_obstypes": (3, 6),
                "type_01": (7, 10),
                "type_02": (11, 14),
                "type_03": (15, 18),
                "type_04": (19, 22),
                "type_05": (23, 26),
                "type_06": (27, 30),
                "type_07": (31, 34),
                "type_08": (35, 38),
                "type_09": (39, 42),
                "type_10": (43, 46),
                "type_11": (47, 50),
                "type_12": (51, 54),
                "type_13": (55, 58),
            },
            parser=self.parse_sys_obs_types,
        )

    @property
    def signal_strength_unit(self) -> RinexHeader:
        """Parser definition for RINEX header label 'SIGNAL STRENGTH UNIT'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            DBHZ                                                        SIGNAL STRENGTH UNIT
        """
        return RinexHeader(
            marker="SIGNAL STRENGTH UNIT", fields={"signal_strength_unit": (0, 20)}, parser=self.parse_string
        )

    @property
    def interval(self) -> RinexHeader:
        """Parser definition for RINEX header label 'INTERVAL'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
                 1.000                                                  INTERVAL
        """
        return RinexHeader(marker="INTERVAL", fields={"interval": (0, 10)}, parser=self.parse_float)

    @property
    def time_of_first_obs(self) -> RinexHeader:
        """Parser definition for RINEX header label 'TIME OF FIRST OBS'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
              2016    03    01    00    00   00.0000000     GPS         TIME OF FIRST OBS
        """
        return RinexHeader(
            marker="TIME OF FIRST OBS",
            fields={
                "year": (0, 6),
                "month": (6, 12),
                "day": (12, 18),
                "hour": (18, 24),
                "minute": (24, 30),
                "second": (30, 43),
                "time_sys": (48, 51),
            },
            parser=self.parse_time_of_first_obs,
        )

    @property
    def time_of_last_obs(self) -> RinexHeader:
        """Parser definition for RINEX header label 'TIME OF LAST OBS'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
              2016    03    01    23    59   59.0000000     GPS         TIME OF LAST OBS
        """
        return RinexHeader(
            marker="TIME OF LAST OBS",
            fields={
                "year": (0, 6),
                "month": (6, 12),
                "day": (12, 18),
                "hour": (18, 24),
                "minute": (24, 30),
                "second": (30, 43),
                "time_sys": (48, 51),
            },
            parser=self.parse_time_of_last_obs,
        )

    @property
    def rcv_clock_offs_appl(self) -> RinexHeader:
        """Parser definition for RINEX header label 'RCV CLOCK OFFS APPL'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
                 0                                                      RCV CLOCK OFFS APPL
        """
        return RinexHeader(
            marker="RCV CLOCK OFFS APPL", fields={"rcv_clk_offset_flag": (0, 6)}, parser=self.parse_string
        )

    @property
    def sys__dcbs_applied(self) -> RinexHeader:
        """Parser definition for RINEX header label 'SYS / DCBS APPLIED'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            G APPL_DCB          xyz.uvw.abc//pub/dcb_gps.dat            SYS / DCBS APPLIED
        """
        return RinexHeader(
            marker="SYS / DCBS APPLIED",
            fields={"sat_sys": (0, 1), "program": (2, 19), "source": (20, 60)},
            parser=self.parse_sys_dcbs_applied,
        )

    @property
    def sys__pcvs_applied(self) -> RinexHeader:
        """Parser definition for RINEX header label 'SYS / PCVS APPLIED'
        """
        return RinexHeader(
            marker="SYS / PCVS APPLIED",
            fields={"sat_sys": (0, 1), "program": (2, 19), "source": (20, 60)},
            parser=self.parse_sys_pcvs_applied,
        )

    @property
    def sys__scale_factor(self) -> RinexHeader:
        """Parser definition for RINEX header label 'SYS / SCALE FACTOR'
        """
        return RinexHeader(
            marker="SYS / SCALE FACTOR",
            fields={"sat_sys": (0, 1), "factor": (2, 6), "num_obstypes": (8, 10)},
            parser=self.parse_scale_factor,  # TODO: not implemented
        )

    @property
    def sys__phase_shift(self) -> RinexHeader:
        """Parser definition for RINEX header label 'SYS / PHASE SHIFT'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
            G L1C  0.00000  12 G01 G02 G03 G04 G05 G06 G07 G08 G09 G10  SYS / PHASE SHIFT
                               G11 G12                                  SYS / PHASE SHIFT
            G L1W  0.00000                                              SYS / PHASE SHIFT
        """
        return RinexHeader(
            marker="SYS / PHASE SHIFT",
            fields={
                "sat_sys": (0, 1),
                "obs_type": (2, 5),
                "correction": (6, 14),
                "num_satellite": (16, 18),
                "satellites": (19, 59),
            },
            parser=self.parse_phase_shift,
        )

    @property
    def glonass_slot__frq_num(self) -> RinexHeader:
        """Parser definition for RINEX header label 'GLONASS SLOT / FRQ #'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
             22 R01  1 R02 -4 R03  5 R04  6 R05  1 R06 -4 R07  5 R08  6 GLONASS SLOT / FRQ #
                R09 -6 R10 -7 R11  0 R13 -2 R14 -7 R15  0 R17  4 R18 -3 GLONASS SLOT / FRQ #
                R19  3 R20  2 R21  4 R22 -3 R23  3 R24  2               GLONASS SLOT / FRQ #
        """
        return RinexHeader(
            marker="GLONASS SLOT / FRQ #",
            fields={
                "num_satellite": (0, 3),
                "slot_01": (4, 11),
                "slot_02": (11, 18),
                "slot_03": (18, 25),
                "slot_04": (25, 32),
                "slot_05": (32, 39),
                "slot_06": (39, 46),
                "slot_07": (46, 53),
                "slot_08": (53, 60),
            },
            parser=self.parse_glonass_slot,
        )

    @property
    def glonass_cod__phs__bis(self) -> RinexHeader:
        """Parser definition for RINEX header label 'GLONASS COD/PHS/BIS'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
             C1C  -10.000 C1P  -10.123 C2C  -10.432 C2P  -10.634        GLONASS COD/PHS/BIS
        """
        return RinexHeader(
            marker="GLONASS COD/PHS/BIS",
            fields={"type_01": (1, 13), "type_02": (14, 26), "type_03": (27, 39), "type_04": (40, 52)},
            parser=self.parse_glonass_code_phase_bias,
        )

    @property
    def leap_seconds(self) -> RinexHeader:
        """Parser definition for RINEX header label 'LEAP SECONDS'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
                16    17  1851     3                                    LEAP SECONDS
        """
        return RinexHeader(
            marker="LEAP SECONDS",
            fields={
                "leap_seconds": (0, 6),
                "future_past_leap_seconds": (6, 12),
                "week": (12, 18),
                "week_day": (18, 24),
                "time_sys": (24, 27),
            },
            parser=self.parse_leap_seconds,
        )

    @property
    def num_of_satellites(self) -> RinexHeader:
        """Parser definition for RINEX header label '# OF SATELLITES'

        Example:
            ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8
                71                                                      # OF SATELLITES
        """
        return RinexHeader(marker="# OF SATELLITES", fields={"num_satellites": (0, 6)}, parser=self.parse_integer)


# TODO: 'PRN / # OF OBS'

#         return RinexHeader(
#             marker=,
#             fields=,
#             parser=,
#         )
