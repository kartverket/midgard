"""Midgard, the Python Geodesy library

Midgard is a collection of useful Python utilities used by the Geodetic
institute at the Norwegian Mapping Authority (Kartverket). Although some of
these are geodesy-specific, many are also useful in more general settings.

Note: Midgard is still in pre-alpha status. Its functionality will change,
      and it should not be depended on in any production-like setting.

Midgard comes organized into different subpackages:

{list_subpackages}

Look for help inside each subpackage:

    >>> from midgard import subpackage
    >>> help(subpackage)


Authors:
--------

{list_authors}
"""

# Standard library imports
from datetime import date as _date
from collections import namedtuple as _namedtuple
from pathlib import Path as _Path

# Version of Midgard.
#
# This is automatically set using the bumpversion tool
__version__ = '0.1.1'


# Authors of Midgard.
_Author = _namedtuple('_Author', ['name', 'email', 'start', 'end'])
_Author.__new__.__defaults__ = ('', '', _date(2018, 4, 1), _date.max)

_AUTHORS = sorted([
    _Author('Geir Arne Hjelle', 'geir.arne.hjelle@kartverket.no'),
], key=lambda a: a.name.split()[-1])  # Sort on last name

__author__ = ', '.join(a.name for a in _AUTHORS if a.start < _date.today() < a.end)
__contact__ = ', '.join(a.email for a in _AUTHORS if a.start < _date.today() < a.end)


# Copyright of the library
__copyright__ = f'2018 - {_date.today().year} Norwegian Mapping Authority'


# Update doc with info about subpackages and authors
def _update_doc(doc):
    """Add information to module doc-string

    Args:
        doc (str):  The doc-string to format as the module doc-string.
    """
    # Subpackages
    subpackage_paths = _Path(__file__).parent.iterdir()
    subpackages = [p.name for p in subpackage_paths if p.is_dir() and not p.name.startswith('_')]
    list_subpackages = '\n'.join(f'+ {p}' for p in subpackages)

    # Authors
    authors = [f'+ {a.name} <{a.email}>' for a in _AUTHORS if a.start < _date.today() < a.end]
    list_authors = '\n'.join(authors)

    # Add to module doc-string
    return doc.format(list_subpackages=list_subpackages, list_authors=list_authors)


__doc__ = _update_doc(__doc__)
