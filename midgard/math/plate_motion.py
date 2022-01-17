"""Midgard library module for handling tectonic plate motion

Description:
------------

Example:
--------

import numpy as np
from midgard.math.plate_motion import PlateMotion

pm = PlateMotion(plate="eura")
pos = np.array([2102928.189605, 721619.617278, 5958196.398820]) # in meter
vel = pm.get_velocity(pos) # in mm/yr

"""

# Standard library imports
from typing import List, Union

# Third party imports
import numpy as np

# Midgard imports
from midgard.collections import plate_motion_models
from midgard.data.position import Position, PositionDelta
from midgard.dev import exceptions
from midgard.math.unit import Unit


class PlateMotion():
    """A class for handling of tectonic plate motion
    """
    
    def __init__(self, plate: str, model: str="itrf2014") -> None:
        """Initilialize PlateMotion object by defining tectonic plate
        
        Args:
            plate: Name of tectonic plate
            model: Name of plate motion model
        """
        model_ = plate_motion_models.get(model)
        if not plate in model_.plates:
            raise exceptions.UnknownSystemError(f"Tectonic plate {plate!r} unknown in plate motion model {model!r}. "
                                                f"Use one of {model_.plates}")
            
        self.plate = plate
        self.model = model
        self.pole = model_.get_pole(plate, unit="radian per year")
        
        
    def get_velocity(self, pos: Union[List[float], np.ndarray], system: str="trs") -> np.ndarray:
        """Get station velocity in meter/year for a given station position depending on chosen coordinate system
        
        Args:
            pos:     Station position in geocentric coordinates (X,Y,Z) in meter
            system:  Choose coordinates sytem:
                        trs: Terrestial reference system. Geocentric coordinates in x,y,z
                        enu: Topocentric coordinates (East, North, Up)
            
        Returns:
            Station velocity in meter/year either in X,Y,Z or East, North, Up
        """
        pole_vec = np.array([self.pole.wx, self.pole.wy, self.pole.wz])
        vel = np.cross(pole_vec, np.array(pos))
        if system == "trs":
            return vel
        else:
            dvel = PositionDelta(vel, system="trs", ref_pos=Position(pos, system="trs"))
            return dvel.enu
        
        
    def as_spherical(self):
       """Get Euler pole of tectonic plate in spherical coordinates, that means location in latitude and longitude and magnitude of rotation
       
       https://geo.libretexts.org/Courses/University_of_California_Davis/GEL_056%3A_Introduction_to_Geophysics/Geophysics_is_everywhere_in_geology.../04%3A_Plate_Tectonics/4.07%3A_Plate_Motions_on_a_Sphere
       
       Returns:
           Euler pole in spherical coordinates (latitude [deg], longitude [deg], magnitude of rotation [degree per million years])
       """
       return self.to_spherical(np.array([self.pole.wx, self.pole.wy, self.pole.wz]) * Unit(self.pole.unit).to("milliarcsecond per year").m)
       
   
    def as_cartesian(self):
       """Get Euler pole of tectonic plate in cartesian coordinates (X,Y,Z)
       
       Returns:
           Euler pole in cartesian coordinates (X, Y, Z) in [milliarcsecond/yr]
       """
       return np.array([self.pole.wx, self.pole.wy, self.pole.wz]) * Unit(self.pole.unit).to("milliarcsecond per year").m
   
   
    def to_cartesian(self, pole: np.ndarray) -> np.ndarray:
       """Convert Euler pole of tectonic plate from spherical to cartesian coordinates
       
       That means from location in latitude and longitude and magnitude of rotation to X, Y and Z coordinates.
       
       https://geo.libretexts.org/Courses/University_of_California_Davis/GEL_056%3A_Introduction_to_Geophysics/Geophysics_is_everywhere_in_geology.../04%3A_Plate_Tectonics/4.07%3A_Plate_Motions_on_a_Sphere
       
       Args:
           pole: Euler pole array in spherical coordinates (latitude [deg], longitude [deg], magnitude of rotation [degree per million years])
       
       Returns:
           Euler pole in cartesian coordinates (X, Y, Z) in [milliarcsecond/yr]
       """
       lat = pole[0] * Unit.degree2radian
       lon = pole[1] * Unit.degree2radian
       w = pole[2] * Unit("degree per year").to("radian per year").m / 1000000

       wx = w * np.cos(lat) * np.cos(lon) * Unit.radian2milliarcsecond
       wy = w * np.cos(lat) * np.sin(lon) * Unit.radian2milliarcsecond
       wz = w * np.sin(lat) * Unit.radian2milliarcsecond
       
       return np.array([wx, wy, wz])
   
    
    def to_spherical(self, pole: np.ndarray) -> np.ndarray:
       """Convert Euler pole of tectonic plate from cartesian to spherical coordinates, that means location in latitude and longitude and magnitude of rotation
       
       https://geo.libretexts.org/Courses/University_of_California_Davis/GEL_056%3A_Introduction_to_Geophysics/Geophysics_is_everywhere_in_geology.../04%3A_Plate_Tectonics/4.07%3A_Plate_Motions_on_a_Sphere
       
       Args:
           pole: Euler pole array in cartesian coordinates (X,Y,Z) in [milliarcsecond per year])
       
       Returns:
           Euler pole in spherical coordinates (latitude [deg], longitude [deg], magnitude of rotation [degree per million years])
       """
       wx = pole[0] * Unit.milliarcsec2radian
       wy = pole[1] * Unit.milliarcsec2radian
       wz = pole[2] * Unit.milliarcsec2radian
       
       latitude = np.arctan2(wz, np.sqrt(wx**2 + wy**2)) * Unit.radian2degree
       longitude = np.arctan2(wy, wx) * Unit.radian2degree
       omega = np.sqrt(wx**2 + wy**2 + wz**2) * Unit("radian per year").to("degree per year").m * 1000000
       
       return np.array([latitude, longitude, omega])

