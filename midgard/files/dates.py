"""Convenience functions for working with dates

Description:
------------

Formats and converters that can be used for convenience and consistency.

"""

# Standard library imports
import datetime
from typing import Dict, Optional, Union

# Formats that can be passed to datetime.strftime, see http://strftime.org/
FMT_date = "%Y-%m-%d"
FMT_datetime = "%Y-%m-%d %H:%M:%S"
FMT_dt_file = "%Y%m%d-%H%M%S"


def date_vars(date: Optional[Union[datetime.date, datetime.datetime]]) -> Dict[str, str]:
    """Construct a dict of date variables

    From a given date, construct a dict containing all relevant date
    variables. This dict can be used to for instance replace variables in file
    names.

    Examples:

        >>> from datetime import date
        >>> date_vars(date(2009, 11, 2))  # doctest: +NORMALIZE_WHITESPACE
        {'yyyy': '2009', 'ce': '20', 'yy': '09', 'm': '11', 'mm': '11', 'mmm': 'nov', 'MMM': 'NOV', 'd': '2',
         'dd': '02', 'doy': '306', 'dow': '1', 'h': '0', 'hh': '00'}

        >>> date_vars(None)
        {}

    Args:
        date:  The given date.

    Returns:
        Dictionary with date variables for the given date.
    """
    if date is None:
        return dict()

    # Create the dict of date variables
    return dict(
        yyyy=date.strftime("%Y"),
        ce=date.strftime("%Y")[:2],
        yy=date.strftime("%y"),
        m=str(date.month),
        mm=date.strftime("%m"),
        mmm=date.strftime("%b").lower(),
        MMM=date.strftime("%b").upper(),
        d=str(date.day),
        dd=date.strftime("%d"),
        doy=date.strftime("%j"),
        dow=date.strftime("%w"),
        h=date.strftime("%-H"),
        hh=date.strftime("%H"),
    )
