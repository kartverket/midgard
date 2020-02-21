"""RINEX observation header classes for file format version 3.xx
"""
# Standard library imports
from typing import Tuple

# Midgard imports
from midgard.dev import plugins
from midgard.parsers import RinexParser, RinexHeader
from midgard.parsers._parser_rinex import parser_cache, _FieldStr, _FieldVal


class Rinex3ObsHeaderMixin:
    """A mixin defining which RINEX observation headers are mandatory and optional in RINEX version 3.xx"""

    @property
    def mandatory_headers(self) -> Tuple[RinexHeader, ...]:
        return (
            self.rinex_version__type,
            self.pgm__run_by__date,
            self.marker_name,
            self.marker_type,
            self.observer__agency,
            self.rec_num__type__vers,
            self.ant_num__type,
            self.approx_position_xyz,
            self.antenna__delta_hen,
            self.sys__num__obs_types,
            self.time_of_first_obs,
            self.sys__phase_shift,
            self.glonass_slot__frq_num,
            self.glonass_cod__phs__bis,
        )

    @property
    def optional_headers(self) -> Tuple[RinexHeader, ...]:
        return (
            self.comment,
            self.marker_number,
            self.antenna__delta_xyz,
            # self.antenna__phasecenter,
            # self.antenna__bsight_xyz,
            # self.antenna__zerodir_azi,
            # self.antenna__zerodir_xyz,
            # self.center_of_mass__xyz,
            self.signal_strength_unit,
            self.interval,
            self.time_of_last_obs,
            self.rcv_clock_offs_appl,
            self.sys__dcbs_applied,
            self.sys__pcvs_applied,
            self.sys__scale_factor,
            self.leap_seconds,
            self.num_of_satellites,
            # self.prn__num_of_obs,
        )


@plugins.register
class Rinex3ObsHeaderParser(Rinex3ObsHeaderMixin, RinexParser):
    """A parser for reading just the RINEX version 3.xx observation header

    The data in the rinex file will not be parsed.
    """

    def read_epochs(self, fid) -> None:
        """Do not read data from Rinex file

        Skip reading of data.
        """
        pass
