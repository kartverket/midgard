"""Dataclass for handling tectonic plate motion models

Description:
------------

You can add your own tectonic plate motion models via adding at the end of file:
    
    <model name> = PlateMotionModel(
                    name: <model name>
                    description: <model description>
                    pole: <List with rotation pole definitions for different tectonics plate>
    )


Example:
--------

import numpy as np
from midgard.collections import plate_motion_models

# Get list with available plate models
models = 


# Get PlateMotionModel instance for a given tectonic name
model = plate_motion_models.get("itrf2014")

# Get RotationPole object for Eurasian tectonic plate
pole = model.get_pole("eura", unit="radian per year")

# Determine station velocity for given station position
pos = np.array([2102928.189605, 721619.617278, 5958196.398820])
pole_vec = [pole.wx, pole.wy, pole.wz]
vel = np.cross(pole_vec, pos)
"""


# Standard library imports
from dataclasses import dataclass, replace  # pip install dataclasses on Python 3.6
from typing import Dict, List, Union

# Midgard imports
from midgard.dev import exceptions
from midgard.math.unit import Unit


_PLATE_MOTION_MODELS: Dict[str, "PlateMotionModel"] = dict()


def get(model: str) -> "PlateMotionModel":
    """Get a tectonic plate motion model by name
    
    Args:
        model: Plate motion model name
        
    Returns:
        Instance of PlateMotionModel dataclass
    """
    try:
        return replace(_PLATE_MOTION_MODELS[model])   # Make a copy of PlateMotionModel object
    except KeyError:
        models = ", ".join(sorted(_PLATE_MOTION_MODELS))
        raise exceptions.UnknownSystemError(f"Tectonic plate model {model!r} unknown. Use one of {models}")
        
        
def models() -> List[str]:
    """Get a list of available tectonic plate motion models
        
    Returns:
        List of available tectonic plate motion models
    
    """
    return list(_PLATE_MOTION_MODELS.keys())


@dataclass(eq=True, frozen=True)
class PlateMotionModel:
    """Dataclass for plate motion model
    
    Attributes:
        name:        Name of plate motion model
        description: Description of plate motion model
        poles:       Dictionary with rotation pole definition for defined tectonic plates
    """
    __slots__ = ["name", "description", "poles"]
    
    name: str
    description: str
    poles: Dict[str, object]

    def __post_init__(self) -> None:
        """Simple registration of Plate models"""
        _PLATE_MOTION_MODELS[self.name] = self
        
    @property
    def plates(self) -> List[str]:
        """Get a list of available tectonic plates of plate motion model
            
        Returns:
            List of available tectonic plates of plate motion model
        
        """
        return list(self.poles.keys())
    
    
    def to_unit(self, unit: str) -> None:
        """Change rotation pole unit for all tectonic plates
        
        Args:
            unit:  Define unit of rotation pole (e.g. 'radian per year', 'milliarcsecond per year')
        """
        for plate, pole in self.poles.items():
            for entry in ["wx", "wy", "wz", "dwx", "dwy", "dwz"]:
                setattr(pole, entry, getattr(pole, entry) * Unit(pole.unit).to(unit).m)
            pole.unit = unit
            self.poles[plate] = replace(pole) # Make a copy of RotationPole object
    
    
    def get_pole(self, plate: str, unit: Union[None, str] = None ) -> "RotationPole":
        """Get rotation pole object for given tectonic plate
        
        Args:
            plate: Name of tectonic plate (e.g. eura)
            model: Plate motion model name
            unit:  Define unit of rotation pole (e.g. 'radian per year', 'milliarcsecond per year')
            
        Returns:
            Instance of RotationPole dataclass for chosen tectonic plate
        """
        try:
            pole = replace(self.poles[plate])  # Make a copy of RotationPole object
        except KeyError:
            plates = ", ".join(sorted(self.poles.keys()))
            raise exceptions.UnknownSystemError(f"Tectonic plate {plate!r} unknown in plate motion model {self.name}. Use one of {plates}")

        if unit:
            for entry in ["wx", "wy", "wz", "dwx", "dwy", "dwz"]:
                setattr(pole, entry, getattr(pole, entry) * Unit(pole.unit).to(unit).m)
            pole.unit = unit
            
        return pole


@dataclass(eq=True, frozen=False)
class RotationPole:
    """Dataclass for plate motion model
    
    Attributes:
        name:           Name of tectonic plate
        wx, wy, wx:     Rotation pole (angular velocity) components
        dwx, dwy, dwz:  Standard deviation of rotation pole components
        unit:           Unit of rotation pole entries
        description:    Description of tectonic plate
    """
    __slots__ = ["name", "wx", "wy", "wz", "dwx", "dwy", "dwz", "unit", "description"]
    
    name: str
    wx: float
    wy: float
    wz: float
    dwx: float
    dwy: float
    dwz: float
    unit: str
    description: str

#
# ITRF2014 plate motion model
#
# Reference: Altamimi, Z., Metivier, L., Rebischung, P., Rouby, H. and Collilieux, X. (2017): "ITRF2014 plate motion 
#            model", Geophysical Journal International, doi: 10.1093/gji/ggx136
#
itrf2014 = PlateMotionModel(
    name="itrf2014", 
    description="ITRF2014 plate motion model",
    poles= dict(
        anta=RotationPole("anta", wx=-0.248, wy=-0.324, wz= 0.675, dwx=0.004, dwy=0.004, dwz=0.008, unit="milliarcsecond per year", description="Antarctic plate"),
        arab=RotationPole("arab", wx= 1.154, wy=-0.136, wz= 1.444, dwx=0.020, dwy=0.022, dwz=0.014, unit="milliarcsecond per year", description="Arabian plate"),
        aust=RotationPole("aust", wx= 1.510, wy= 1.182, wz= 1.215, dwx=0.004, dwy=0.004, dwz=0.004, unit="milliarcsecond per year", description="Australian plate"),
        eura=RotationPole("eura", wx=-0.085, wy=-0.531, wz= 0.770, dwx=0.004, dwy=0.002, dwz=0.005, unit="milliarcsecond per year", description="Eurasian plate"),
        indi=RotationPole("indi", wx= 1.154, wy=-0.005, wz= 1.454, dwx=0.027, dwy=0.117, dwz=0.035, unit="milliarcsecond per year", description="Indian plate"),
        nazc=RotationPole("nazc", wx=-0.333, wy=-1.544, wz= 1.623, dwx=0.006, dwy=0.015, dwz=0.007, unit="milliarcsecond per year", description="Nazca plate"),
        noam=RotationPole("noam", wx= 0.024, wy=-0.694, wz=-0.063, dwx=0.002, dwy=0.005, dwz=0.004, unit="milliarcsecond per year", description="North American plate"),
        nubi=RotationPole("nubi", wx= 0.099, wy=-0.614, wz= 0.733, dwx=0.004, dwy=0.003, dwz=0.003, unit="milliarcsecond per year", description="Nubia plate"),
        pcfc=RotationPole("pcfc", wx=-0.409, wy= 1.047, wz=-2.169, dwx=0.003, dwy=0.004, dwz=0.004, unit="milliarcsecond per year", description="Pacific plate"),
        soam=RotationPole("soam", wx=-0.270, wy=-0.301, wz=-0.140, dwx=0.006, dwy=0.006, dwz=0.003, unit="milliarcsecond per year", description="South American plate"),
        soma=RotationPole("soma", wx=-0.121, wy=-0.794, wz= 0.884, dwx=0.035, dwy=0.034, dwz=0.008, unit="milliarcsecond per year", description="Somali plate"),
    )
)


#
# ITRF2008 plate motion model
#
# Reference: Altamimi, Z., Metivier, L., and Collilieux, X. (2012): "ITRF2008 plate motion model", Journal of 
#            Geophysical Research, doi: 10.1029/2011JB008930
#
itrf2008 = PlateMotionModel(
    name="itrf2008", 
    description="ITRF2008 plate motion model",
    poles= dict(
        amur=RotationPole("amur", wx=-0.190, wy=-0.442, wz= 0.915, dwx=0.040, dwy=0.051, dwz=0.049, unit="milliarcsecond per year", description="Amurian plate"),
        anta=RotationPole("anta", wx=-0.252, wy=-0.302, wz= 0.643, dwx=0.008, dwy=0.006, dwz=0.009, unit="milliarcsecond per year", description="Antarctic plate"),
        arab=RotationPole("arab", wx= 1.202, wy=-0.054, wz= 1.485, dwx=0.082, dwy=0.100, dwz=0.063, unit="milliarcsecond per year", description="Arabian plate"),
        aust=RotationPole("aust", wx= 1.504, wy= 1.172, wz= 1.228, dwx=0.007, dwy=0.007, dwz=0.007, unit="milliarcsecond per year", description="Australian plate"),
        carb=RotationPole("carb", wx= 0.049, wy=-1.088, wz= 0.664, dwx=0.201, dwy=0.417, dwz=0.146, unit="milliarcsecond per year", description="Caribbean plate"),
        eura=RotationPole("eura", wx=-0.083, wy=-0.534, wz= 0.775, dwx=0.008, dwy=0.007, dwz=0.008, unit="milliarcsecond per year", description="Eurasian plate"),
        indi=RotationPole("indi", wx= 1.232, wy= 0.303, wz= 1.540, dwx=0.031, dwy=0.128, dwz=0.030, unit="milliarcsecond per year", description="Indian plate"),
        nazc=RotationPole("nazc", wx=-0.333, wy=-1.551, wz= 1.625, dwx=0.011, dwy=0.029, dwz=0.013, unit="milliarcsecond per year", description="Nazca plate"),
        noam=RotationPole("noam", wx= 0.035, wy=-0.662, wz=-0.100, dwx=0.008, dwy=0.009, dwz=0.008, unit="milliarcsecond per year", description="North American plate"),
        nubi=RotationPole("nubi", wx= 0.095, wy=-0.598, wz= 0.723, dwx=0.009, dwy=0.007, dwz=0.009, unit="milliarcsecond per year", description="Nubia plate"),
        pcfc=RotationPole("pcfc", wx=-0.411, wy= 1.036, wz=-2.166, dwx=0.007, dwy=0.007, dwz=0.009, unit="milliarcsecond per year", description="Pacific plate"),
        soam=RotationPole("soam", wx=-0.243, wy=-0.311, wz=-0.154, dwx=0.009, dwy=0.010, dwz=0.009, unit="milliarcsecond per year", description="South American plate"),
        soma=RotationPole("soma", wx=-0.080, wy=-0.745, wz= 0.897, dwx=0.028, dwy=0.030, dwz=0.012, unit="milliarcsecond per year", description="Somali plate"),
    )
)


#
# NNR-MORVEL56 plate motion model
#
# Webside: http://www.geology.wisc.edu/~chuck/MORVEL/MRVL_AVs.html
#
# Reference: Argus, D.F., R.G. Gordon, and C.DeMets, Geologically current motion of 56 plates relative to the 
#            no-net-rotation reference frame, Geochemistry, Geophysics, Geosystems, 12, No. 11, 13 pp.,
#            https://doi.org/10.1029/2011GC003751, 2011. 
#
#
#    Plate          Abbr  Lat    Lon      w              RMS   Area
#                         deg N  deg E    deg/Myr        mm/yr
#    ________________________________________________________________
#    Amur            am   63.17  −122.82  0.297 ± 0.020  28.1  0.1307
#    Antarctica      an   65.42  −118.11  0.250 ± 0.008  15.2  1.4327
#    Arabia          ar   48.88    −8.49  0.559 ± 0.016  47.6  0.1208
#    Australia       au   33.86    37.94  0.632 ± 0.017  63.1  0.9214
#    Capricorn       cp   44.44    23.09  0.608 ± 0.019  66.2  0.2036
#    Caribbean       ca   35.20   −92.62  0.286 ± 0.023  14.9  0.0730
#    Cocos           co   26.93  −124.31  1.198 ± 0.045  74.6  0.0722
#    Eurasia         eu   48.85  −106.50  0.223 ± 0.009  22.8  1.1963
#    India           in   50.37    −3.29  0.544 ± 0.010  57.6  0.3064
#    Juan de Fuca    jf  −38.31    60.04  0.951 ± 0.256  17.4  0.0063
#    Lwandle         lw   51.89   −69.52  0.286 ± 0.026  26.5  0.1171
#    Macquarie       mq   49.19    11.05  1.144 ± 0.274  49.5  0.0079
#    Nazca           nz   46.23  −101.06  0.696 ± 0.029  70.0  0.3967
#    North America   na   −4.85   −80.64  0.209 ± 0.013  19.8  1.3657
#    Nubia           nb   47.68   −68.44  0.292 ± 0.007  29.2  1.4406
#    Pacific         pa  −63.58   114.70  0.651 ± 0.011  65.5  2.5768
#    Philippine Sea  ps  −46.02   −31.36  0.910 ± 0.050  52.6  0.1341
#    Rivera          ri   20.25  −107.29  4.536 ± 0.630  11.8  0.0025
#    Sandwich        sw  −29.94   −36.87  1.362 ± 0.744  72.6  0.0045
#    Scotia          sc   22.52  −106.15  0.146 ± 0.016  16.2  0.0419
#    Somalia         sm   49.95   −84.52  0.339 ± 0.011  31.0  0.3548
#    South America   sa  −22.62  −112.83  0.109 ± 0.011  10.6  1.0034
#    Sunda           su   50.06   −95.02  0.337 ± 0.020  32.2  0.2197
#    Sur             sr  −32.50  −111.32  0.107 ± 0.028  11.0  0.0271
#    Yangtze         yz   63.03  −116.62  0.334 ± 0.013  36.5  0.0542
# 
nnr_morvel56 = PlateMotionModel(
    name="nnr_morvel56", 
    description="NNR-MORVEL56 plate motion model",
    poles= dict(
        amur=RotationPole("amur", wx=-0.26156, wy=-0.40555, wz= 0.95410, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Amurian plate"),
        anta=RotationPole("anta", wx=-0.17639, wy=-0.33021, wz= 0.81844, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Antarctic plate"),
        arab=RotationPole("arab", wx= 1.30893, wy=-0.19539, wz= 1.51601, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Arabian plate"),
        aust=RotationPole("aust", wx= 1.49003, wy= 1.16163, wz= 1.26766, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Australian plate"),
        capr=RotationPole("capr", wx= 1.43757, wy= 0.61288, wz= 1.53251, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Capricorn plate"),
        carb=RotationPole("carb", wx=-0.03846, wy=-0.84045, wz= 0.59349, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Caribbean plate"),
        coco=RotationPole("coco", wx=-2.16738, wy=-3.17607, wz= 1.95327, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Cocos plate"),
        eura=RotationPole("eura", wx=-0.15004, wy=-0.50651, wz= 0.60450, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Eurasian plate"),
        indi=RotationPole("indi", wx= 1.24706, wy=-0.07169, wz= 1.50832, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Indian plate"),
        juan=RotationPole("juan", wx= 1.34157, wy= 2.32742, wz=-2.12234, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Juan de Fuca plate"),
        lwan=RotationPole("lwan", wx= 0.22233, wy=-0.59528, wz= 0.81012, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Lwandle plate"),
        macq=RotationPole("macq", wx= 2.64169, wy= 0.51589, wz= 3.11714, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Macquarie plate"),
        nazc=RotationPole("nazc", wx=-0.33251, wy=-1.70109, wz= 1.80935, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Nazca plate"),
        noam=RotationPole("noam", wx= 0.12193, wy=-0.73972, wz=-0.06361, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="North American plate"),
        nubi=RotationPole("nubi", wx= 0.26008, wy=-0.65822, wz= 0.77725, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Nubia plate"),
        pcfc=RotationPole("pcfc", wx=-0.43574, wy= 0.94737, wz=-2.09883, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Pacific plate"),
        phil=RotationPole("phil", wx= 1.94255, wy=-1.18388, wz=-2.35735, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Philippine Sea plate"),
        rive=RotationPole("rive", wx=-4.55332, wy=-14.62801,wz= 5.65195, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Rivera plate"),
        sand=RotationPole("sand", wx= 3.39908, wy=-2.54932, wz=-2.44715, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Sandwich plate"),
        scot=RotationPole("scot", wx=-0.13505, wy=-0.46636, wz= 0.20131, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Scotia plate"),
        soam=RotationPole("soam", wx= 0.07499, wy=-0.78168, wz= 0.93420, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="South American plate"),
        soma=RotationPole("soma", wx=-0.14054, wy=-0.33384, wz=-0.15092, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Somali plate"),
        sund=RotationPole("sund", wx=-0.06815, wy=-0.77587, wz= 0.93018, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Sunda plate"),
        sur_=RotationPole("sur_", wx=-0.11812, wy=-0.30264, wz=-0.20697, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Sur plate"),
        yang=RotationPole("ynag", wx=-0.24434, wy=-0.48751, wz= 1.07163, dwx=float("nan"), dwy=float("nan"), dwz=float("nan"), unit="milliarcsecond per year", description="Yangtze plate"),
        
    )
)



