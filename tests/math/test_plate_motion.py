"""Tests for the math.site_velocity-module

    Note: If '-s' option is used by calling pytest, then also debug messages are printed.
"""
# Third party imports
import pytest
import numpy as np

# Midgard imports
from midgard.data.position import Position
from midgard.dev import exceptions
from midgard.math.plate_motion import PlateMotion
from midgard.math.unit import Unit


#
# Test data
#
@pytest.fixture
def pos():
    """Station position data for testing"""
    return Position([2102928.189605, 721619.617278, 5958196.398820], system="trs")

    
#
# Test 
#
@pytest.mark.parametrize("system, model, expected_vel", [
                ("trs", "itrf2014", np.array([-0.01804 , 0.01030, 0.00512])),  # vx, vy, vz velocity in m/yr for PMM ITRF2014
                ("trs", "itrf2008", np.array([-0.01805 , 0.01040, 0.00515])),  # vx, vy, vz velocity in m/yr for PMM ITRF2008 -> #TODO: Check ITRF2008 better.
                ("trs", "nnr_morvel56", np.array([-0.01675 , 0.01050, 0.00464])),  # vx, vy, vz velocity in m/yr for PMM NNR-MORVEL56
                ("enu", "itrf2014", np.array([0.01560 , 0.01465])),  # East, North velocity velocity in m/yr for PMM ITRF2014
                ("enu", "itrf2008", np.array([0.01536 , 0.01474])),  # East, North velocity velocity in m/yr for PMM ITRF2008 -> #TODO: Check ITRF2008 better.
                ("enu", "nnr_morvel56", np.array([0.01536 , 0.01327])),  # East, North velocity velocity in m/yr for PMM NNR-MORVEL56
])
def test_get_velocity(pos, system, model, expected_vel):
    """Test of get_velocity() function with 'system=trs'
    
    The test is based on webside:
        https://www.unavco.org/software/geodetic-utilities/plate-motion-calculator/plate-motion-calculator.html
        
    The 'expected_vel' solution is for XYZ coordinates (2102928.189605, 721619.617278, 5958196.398820) and the
    chosen plate motion model (ITRF2014, ITRF2008, NNR-MORVEL56) for Eurasian plate.
    """
    # Determine velocity for East and North direction in m/yr
    pm = PlateMotion(plate="eura", model=model)
    vel = pm.get_velocity(pos.trs.val, system=system) # in mm/yr
   
    if system == "trs":
        print(f"DEBUG test_get_velocity (model={model}): vel({vel[0]:.5f}, {vel[1]:.5f}, {vel[2]:.5f}); "
              f"expected_vel({expected_vel[0]:.5f}, {expected_vel[1]:.5f}, {expected_vel[2]:.5f}))")
    elif system == "enu":
        print(f"DEBUG test_get_velocity (model={model}): vel({vel[0]:.5f}, {vel[1]:.5f}); "
              f"expected_vel({expected_vel[0]:.5f}, {expected_vel[1]:.5f}))")
        vel = np.array([vel[0], vel[1]])
        
    # Check velocity solution
    np.testing.assert_allclose(vel, expected_vel, rtol=0, atol=1e-3)
  
    
    
def test_get_velocity_raise_error(pos):
    """Test of get_velocity() function. Test raising of error, if wrong tectonic plate is chosen.
    """
    with pytest.raises(exceptions.UnknownSystemError, match="Tectonic plate 'fail' unknown in plate motion model 'itrf2014'. .*"):
        PlateMotion(plate="fail", model="itrf2014")
  
        
def test_as_spherical_and_to_cartesian():
    """Test as_spherical() and to_cartesian() function
    """
    pm = PlateMotion(plate="eura", model="itrf2014")
    sph = pm.as_spherical()
    crt = pm.to_cartesian(sph)
    expected_crt = np.array([pm.pole.wx, pm.pole.wy, pm.pole.wz]) * Unit(pm.pole.unit).to("milliarcsecond per year").m

    print(f"DEBUG test_as_spherical_and_to_cartesian: crt({crt[0]:.3f}, {crt[1]:.3f}, {crt[2]:.3f}); "
          f"expected_crt({expected_crt[0]:.3f}, {expected_crt[1]:.3f}, {expected_crt[2]:.3f}))")
    np.testing.assert_allclose(crt, expected_crt, rtol=0, atol=1e-3)
    
def test_as_cartesian():
    """Test as_spherical() and to_cartesian() function
    """
    pm = PlateMotion(plate="eura", model="itrf2014")
    crt = pm.as_cartesian()
    expected_crt = np.array([pm.pole.wx, pm.pole.wy, pm.pole.wz]) * Unit(pm.pole.unit).to("milliarcsecond per year").m

    print(f"DEBUG test_as_cartesian: crt({crt[0]:.3f}, {crt[1]:.3f}, {crt[2]:.3f}); "
          f"expected_crt({expected_crt[0]:.3f}, {expected_crt[1]:.3f}, {expected_crt[2]:.3f}))")
    np.testing.assert_allclose(crt, expected_crt, rtol=0, atol=1e-3)


