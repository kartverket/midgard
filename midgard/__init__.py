"""Midgard, the Python Geodesy library

Midgard is a collection of useful Python utilities used by the Geodetic
institute at the Norwegian Mapping Authority (Kartverket). Although some of
these are geodesy-specific, many are also useful in more general settings.

Note: Midgard is still in pre-alpha status. Its functionality will change,
      and it should not be depended on in any production-like setting.

Midgard comes organized into different subpackages:

{subpackages}

Look for help inside each subpackage:

    >>> from midgard import subpackage  # doctest: +SKIP
    >>> help(subpackage)  # doctest: +SKIP


Current maintainers:
--------------------

{maintainers}
"""

# Standard library imports
from datetime import date as _date
from collections import namedtuple as _namedtuple
from pathlib import Path as _Path


# Version of Midgard.
#
# This is automatically set using the bumpversion tool
__version__ = "1.1.2"


# Authors of Midgard.
_Author = _namedtuple("_Author", ["name", "email", "start", "end"])
_AUTHORS = [
    _Author("Michael Dähnn", "michael.daehnn@kartverket.no", _date.min, _date.max),
    _Author("Ingrid Fausk", "ingrid.fausk@kartverket.no", _date.min, _date.max),
    _Author("Ann-Silje Kirkvik", "ann-silje.kirkvik@kartverket.no", _date.min, _date.max),
    _Author("Mohammed Ouassou", "mohammed.ouassou@kartverket.no", _date(2018, 9, 1), _date.max),
    _Author("Hans Sverre Smalø", "hans.sverre.smalo@kartverket.no", _date(2018, 12, 1), _date.max),
    _Author("Geir Arne Hjelle", "geirarne@gmail.com", _date(2019, 2, 1), _date.max),
    # Hall of Fame
    _Author("Geir Arne Hjelle", "geir.arne.hjelle@kartverket.no", _date.min, _date(2019, 2, 1)),
]

__author__ = ", ".join(a.name for a in _AUTHORS if a.start < _date.today() < a.end)
__contact__ = ", ".join(a.email for a in _AUTHORS if a.start < _date.today() < a.end)


# Copyleft of the library
__copyright__ = f"2018 - {_date.today().year} Norwegian Mapping Authority"


# Update doc with info about subpackages and maintainers
def _update_doc(doc: str) -> str:
    """Add information to doc-string

    Args:
        doc:  The doc-string to update.

    Returns:
        The updated doc-string.
    """
    # Subpackages
    subpackage_paths = _Path(__file__).parent.iterdir()
    subpackage_list = [p.name for p in subpackage_paths if p.is_dir() and not p.name.startswith("_")]
    subpackages = "\n".join(f"+ {p}" for p in subpackage_list)

    # Maintainers
    maintainer_list = [f"+ {a.name} <{a.email}>" for a in _AUTHORS if a.start < _date.today() < a.end]
    maintainers = "\n".join(maintainer_list)

    # Add to doc-string
    return doc.format(subpackages=subpackages, maintainers=maintainers)


__doc__ = _update_doc(__doc__)
