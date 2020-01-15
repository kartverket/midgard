"""Midgard library module for handling Earth ellipsoids

Description:
------------

"""

# Standard library imports
from dataclasses import dataclass  # pip install dataclasses on Python 3.6
import math
from typing import Dict

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import exceptions


_ELLIPSOIDS: Dict[str, "Ellipsoid"] = dict()


def get(ellipsoid: str) -> "Ellipsoid":
    """Get an ellipsoid by name"""
    try:
        return _ELLIPSOIDS[ellipsoid]
    except KeyError:
        ellipsoids = ", ".join(sorted(_ELLIPSOIDS))
        raise exceptions.UnknownSystemError(f"Ellipsoid {ellipsoid!r} unknown. Use one of {ellipsoids}")


@dataclass(eq=True, frozen=True)
class Ellipsoid:
    name: str
    a: float
    f_inv: float
    description: str

    def __post_init__(self) -> None:
        """Simple registration of Ellipsoids"""
        _ELLIPSOIDS[self.name] = self

    @property
    def b(self) -> float:
        """Semi-minor axis"""
        return self.a * (1 - self.f)

    @property
    def f(self) -> float:
        """Flattening"""
        return 1 / self.f_inv

    @property
    def e(self) -> float:
        """Eccentricity"""
        return np.sqrt(self.e2)

    @property
    def e2(self) -> float:
        """Eccentricity squared"""
        return 1 - self.b ** 2 / self.a ** 2

    @property
    def eps(self) -> float:
        return self.e2 / (1 - self.e2)


#
# Ellipsoids, see https://en.wikipedia.org/wiki/Earth_ellipsoid
#
sphere = Ellipsoid("sphere", a=6_371_008.8, f_inv=math.inf, description="Regular sphere, mean radius")
WGS72 = Ellipsoid("WGS72", a=6_378_135, f_inv=298.26, description="WGS72")
GRS80 = Ellipsoid("GRS80", a=6_378_137, f_inv=298.257_222_101, description="Used by ITRS")
WGS84 = Ellipsoid("WGS84", a=6_378_137, f_inv=298.257_223_563, description="Used by GPS")
IERS2003 = Ellipsoid("IERS2003", a=6_378_136.6, f_inv=298.25642, description="IERS conventions 2003, p. 12")
IERS2010 = Ellipsoid("IERS2010", a=6_378_136.6, f_inv=298.25642, description="IERS conventions 2010, p. 18")
