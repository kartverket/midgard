""" Tests for the midgard.gnss.gnss module"""


# Midgard imports
from midgard.gnss import gnss


def test_obstype_to_freq():
    freq = gnss.obstype_to_freq("E", "C1C")
    assert freq == 1575.42e6
