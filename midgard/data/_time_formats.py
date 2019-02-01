"""Array with time epochs
"""
# Standard library imports
from calendar import isleap
from datetime import datetime, timedelta
from typing import Callable, Dict

# Third party imports
import numpy as np

# Midgard imports
from midgard.math.unit import Unit


_FORMATS: Dict[str, "TimeFormat"] = dict()  # Populated by register_format()
_FORMAT_UNITS: Dict[str, str] = dict()  # Populated by register_format()


def register_format(cls: Callable) -> Callable:
    """Decorator used to register new time formats

    The format name is read from the .format attribute of the TimeFormat class.
    """
    name = cls.format
    _FORMATS[name] = cls
    _FORMAT_UNITS[name] = cls.unit

    return cls


#
# Time formats
#
class TimeFormat:

    format = None
    unit = None
    day2seconds = Unit.day2seconds
    week2days = Unit.week2days

    def __init__(self, val, val2=None):
        """Convert val and val2 to Julian days"""
        self.jd1, self.jd2 = self.to_jds(val, val2)

    @classmethod
    def to_jds(cls, val, val2):
        """Convert val and val2 to Julian days and set the .jd1 and .jd2 attributes"""
        raise NotImplementedError

    @classmethod
    def from_jds(cls, jd1, jd2):
        """Convert Julian days to the right format"""
        raise NotImplementedError

    @property
    def value(self):
        """Convert Julian days to the right format"""
        return self.from_jds(self.jd1, self.jd2)


@register_format
class TimeJD(TimeFormat):

    format = "jd"
    unit = ("day",)

    @classmethod
    def to_jds(cls, val, val2):
        if val2 is None:
            val2 = np.zeros(val.shape)

        _delta = val - (np.floor(val + val2 - 0.5) + 0.5)
        jd1 = val - _delta
        jd2 = val2 + _delta
        return jd1, jd2

    @classmethod
    def from_jds(cls, jd1, jd2):
        return jd1 + jd2


@register_format
class TimeMJD(TimeFormat):
    """Modified Julian Date time format.

    This represents the number of days since midnight on November 17, 1858.
    For example, 51544.0 in MJD is midnight on January 1, 2000.
    """

    format = "mjd"
    unit = ("day",)
    _mjd0 = 2400000.5

    @classmethod
    def to_jds(cls, val, val2):
        if val2 is None:
            val2 = np.zeros(val.shape)

        _delta = val - (np.floor(val + val2 - 0.5) + 0.5)
        jd1 = cls._mjd0 + val - _delta
        jd2 = val2 + _delta
        return jd1, jd2

    @classmethod
    def from_jds(cls, jd1, jd2):
        return jd1 - cls._mjd0 + jd2


@register_format
class TimeDateTime(TimeFormat):

    format = "datetime"
    unit = None
    _jd2000 = 2451544.5
    _dt2000 = datetime(2000, 1, 1)

    @classmethod
    def to_jds(cls, val, val2=None):
        if val2 is not None:
            raise

        jd1, jd2 = np.array([cls._dt2jd(dt) for dt in val]).T
        return jd1, jd2

    @classmethod
    def _dt2jd(cls, dt):
        """Convert one datetime to one Julian date pair"""
        delta = dt - cls._dt2000
        jd1 = cls._jd2000 + delta.days

        delta -= timedelta(days=delta.days)
        jd2 = delta.total_seconds() / cls.day2seconds

        return jd1, jd2

    @classmethod
    def from_jds(cls, jd1, jd2):
        return np.array([cls._jd2dt(j1, j2) for j1, j2 in zip(jd1, jd2)])

    @classmethod
    def _jd2dt(cls, jd1, jd2):
        """Convert one Julian date to a datetime"""
        return cls._dt2000 + timedelta(days=jd1 - cls._jd2000) + timedelta(days=jd2)


@register_format
class TimeGPSWeekSec(TimeFormat):
    """GPS weeks and seconds.

    """

    format = "gps_ws"
    unit = ("week", "second")
    _jd19800106 = 2444244.5

    @classmethod
    def to_jds(cls, wwww, sec):

        # .. Determine GPS day
        wd = np.floor((sec + 0.5 * cls.day2seconds) / cls.day2seconds)  # 0.5 d = 43200.0 s

        # .. Determine remainder
        fracSec = sec + 0.5 * cls.day2seconds - wd * cls.day2seconds

        # .. Conversion GPS week and day to from Julian Date (JD)
        jd_day = wwww * Unit.week2days + wd + cls._jd19800106 - 0.5
        jd_frac = fracSec / cls.day2seconds

        return jd_day, jd_frac

    @classmethod
    def from_jds(cls, jd1, jd2):
        if np.any(jd1 + jd2 < cls._jd19800106):
            raise ValueError(f"Julian Day exceeds the GPS time start date of 6-Jan-1980 (JD {cls._jd19800106})")

        # See Time.jd_int for explanation
        _delta = jd1 - (np.floor(jd1 + jd2 - 0.5) + 0.5)
        jd_int = jd1 - _delta
        jd_frac = jd2 + _delta

        # .. Conversion from Julian Date (JD) to GPS week and day
        wwww = np.floor((jd_int - cls._jd19800106) / cls.week2days)
        wd = np.floor(jd_int - cls._jd19800106 - wwww * cls.week2days)
        gpssec = (jd_frac + wd) * cls.day2seconds

        return wwww, gpssec


@register_format
class TimeYear(TimeFormat):
    """Year.

    # TODO: conversion is not correct!!!
    """

    format = "decimalyear"
    unit = ("common_year",)  # TODO: Check this

    @classmethod
    def to_jds(cls, val, val2=None):
        if val2 is not None:
            raise

        jd1, jd2 = np.array([TimeDateTime._dt2jd(cls._yr2dt(yr)) for yr in val]).T
        return jd1, jd2

    @classmethod
    def _yr2dt(cls, year):
        year_int = int(year)
        year_frac = year - year_int
        days_of_year = 366 if isleap(year_int) else 365  # accounting for leap year
        seconds_of_year = year_frac * days_of_year * Unit.day2seconds

        return datetime(year_int, 1, 1) + timedelta(seconds=float(seconds_of_year))

    @classmethod
    def from_jds(cls, jds1, jds2):

        year = list()
        for jd1, jd2 in zip(jds1, jds2):
            dt = TimeDateTime._jd2dt(jd1, jd2)
            days_of_year = 366 if isleap(dt.year) else 365  # accounting for leap year
            day_frac = (
                dt.hour * Unit.hour2day
                + dt.minute * Unit.minute2day
                + dt.second * Unit.second2day
                + dt.microsecond * Unit.microsecond2days
            )
            # day_frac = dt.hour /24 + dt.minute /1440 + dt.second /86400 + dt.microsecond / 86400000000
            year.append(dt.year + (dt.timetuple().tm_yday + day_frac) / days_of_year)

        return np.array(year)
