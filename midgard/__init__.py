"""Midgard, the Python Geodesy library

Midgard is a collection of useful Python utilities used by the Geodetic
institute at the Norwegian Mapping Authority (Kartverket). Although some of
these are geodesy-specific, many are also useful in more general settings.

Midgard comes organized into different subpackages. To see info about the
different subpackages, use the Python help system:

    >>> import midgard
    >>> help(midgard)


"""
# Standard library imports
from datetime import date as _date
from collections import namedtuple as _namedtuple


# Version of Midgard.
#
# This is automatically set using the bumpversion tool
__version__ = '0.0.1'


# Authors of Midgard.
_Author = _namedtuple('_Author', ['name', 'email', 'start', 'end'])
_Author.__new__.__defaults__ = ('', '', _date(2018, 4, 1), _date.max)

_AUTHORS = sorted([
    _Author('Geir Arne Hjelle', 'geir.arne.hjelle@kartverket.no'),
], key=lambda a: a.name.split()[-1])  # Sort on last name

__author__ = ', '.join(a.name for a in _AUTHORS if a.start < _date.today() < a.end)
__contact__ = ', '.join(a.email for a in _AUTHORS if a.start < _date.today() < a.end)


# Copyright of the library
__copyright__ = f'2018 - {_date.today().year} Kartverket'
