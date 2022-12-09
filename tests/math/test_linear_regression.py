"""Tests for the math.linear_regression-module

Note: pytest can be started with commando:
    python -m pytest -s test_linear_regression.py

"""
# Third party imports
import pytest
import numpy as np

# Midgard imports
from midgard.math.linear_regression import LinearRegression

#
# Test data sets
#
@pytest.fixture
def linreg_set():
    """A basic test set linear regression data"""
    x=np.linspace(0, 10, 11)
    y=np.array([ 1.42274251,  0.76670381,  0.53375993, -0.35339823, -0.96415597, -0.02571656,  1.02526094,  1.00517286,
      1.2355888 ,  0.11537742, -0.8675229 ])
    return x, y 
    

#
# Tests
#    
def test_linear_regression(linreg_set):
    """Test linear regression"""

    linreg = LinearRegression(*linreg_set)
    assert np.isclose(0.68328237, linreg.interception, rtol=1e-7)
    assert np.isclose(0.47755214, linreg.interception_sigma, rtol=1e-7)
    assert np.isclose(0.06887090, linreg.r_square, rtol=1e-7)                      
    assert np.isclose(0.76578707, linreg.rms, rtol=1e-7)  
    assert np.isclose(-0.06585988, linreg.slope, rtol=1e-7)
    assert np.isclose(0.08072104, linreg.slope_sigma, rtol=1e-7)
    
    assert len(linreg.residuals) == 11
    assert len(linreg.x) == 11
    assert len(linreg.y) == 11
    assert len(linreg.y_modeled) == 11
    
    assert np.isclose(0.73946014, linreg.residuals[0], rtol=1e-7)
    assert np.isclose(0.68328237, linreg.y_modeled[0], rtol=1e-7)
    
    
def test_linear_regression_reject_outlier(linreg_set):
    """Test linear regression by rejecting outliers"""

    linreg = LinearRegression(*linreg_set, reject_outlier=True)

    assert np.isclose(1.01871373, linreg.interception, rtol=1e-7)
    assert len(linreg.x) == 6
    assert len(linreg.y) == 6   


def test_linear_regression_outlier_iteration(linreg_set):
    """Test linear regression by changing number of outlier iterations"""

    linreg = LinearRegression(*linreg_set, reject_outlier=True, outlier_iteration=2)
   
    assert np.isclose(0.76570960, linreg.interception, rtol=1e-7)
    assert len(linreg.x) == 3
    assert len(linreg.y) == 3 
    

def test_linear_regression_outlier_limit_factor(linreg_set):
    """Test linear regression by changing RMS outlier limit"""

    linreg = LinearRegression(*linreg_set, reject_outlier=True, outlier_limit_factor=1.5)
   
    assert np.isclose(0.89297916, linreg.interception, rtol=1e-7)
    assert len(linreg.x) == 10
    assert len(linreg.y) == 10                   


    

