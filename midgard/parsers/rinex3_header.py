"""A parser for reading IVS source names translation table
"""
# Standard library imports
from datetime import datetime
from typing import Any, Dict, Tuple

# Midgard imports
from midgard.dev import plugins
from midgard.parsers import RinexParser, RinexHeader


class Rinex3HeaderMixin:
    """A mixin defining which headers are mandatory and optional in Rinex 3"""

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
class Rinex3HeaderParser(RinexParser, Rinex3HeaderMixin):
    """A parser for reading just the Rinex3 header

    The data in the rinex file will not be parsed.
    """

    def read_epochs(self, fid) -> None:
        """Do not read data from Rinex file

        Skip reading of data.
        """
        pass
