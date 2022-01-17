"""Tests for the collections.plate_motion_models-module

"""
# Standard library imports
from dataclasses import replace

# Third party imports
import pytest

# Midgard imports
from midgard.collections import plate_motion_models
from midgard.dev import exceptions


#
# Test data
#
@pytest.fixture
def model():
    """PlateMotionModel object"""
    return plate_motion_models.get("itrf2014")
    
@pytest.fixture
def pole():
    """RotationPole object"""
    return plate_motion_models.RotationPole(
            name="eura", 
            wx=-0.085, 
            wy=-0.531, 
            wz= 0.770, 
            dwx=0.004, 
            dwy=0.002, 
            dwz=0.005, 
            unit="milliarcsecond per year", 
            description="Eurasian plate",
    )

#
# Tests
#
def test_models():
    """Test models() function"""
    models = plate_motion_models.models()
    assert "itrf2014" in models

def test_get():
    """Test get() function"""
    model = plate_motion_models.get("itrf2014")
    assert model.name == "itrf2014"
    assert model.description == "ITRF2014 plate motion model"


def test_plate_motion_model_get_pole(model):
    """Test PlateMotionModel class function get_pole()"""
    pole = model.get_pole(plate="eura")
    assert pole.name == "eura"

    
def test_plate_motion_model_get_pole_unit(model):
    """Test PlateMotionModel class function get_pole() with unit argument"""
    pole = model.get_pole(plate="eura", unit="radian per year")
    assert pole.unit == "radian per year"


def test_plate_motion_model_plates(model):
    """Test PlateMotionModel class function plates()"""
    assert set(model.plates) == set(
                ("anta", "arab", "aust", "eura", "indi", "nazc", "noam", "nubi", "pcfc", "soam", "soma")
    )
        
        
def test_plate_motion_model_to_unit(model):
    """Test PlateMotionModel class function to_unit()"""
    model.to_unit(unit="radian per year")
    assert model.poles["eura"].unit == "radian per year"
    

def test_rotation_pole_properties(pole):
    """Test RotationPole class properties"""
    assert pole.name == "eura"
    assert pole.description == "Eurasian plate"
    assert pole.unit == "milliarcsecond per year"
    assert pole.wx == -0.085
        
