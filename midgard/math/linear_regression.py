"""Midgard library module for linear regression

Description:
------------
The 'statsmodels' module is used for the linear regression. Outlier can be rejected beside normal linear regression 
analysis. Hereby a linear regression analysis is carried out, whereby a linear trend is estimated of the given data.
The root-mean square (RMS) of the residuals (observation - linear trend) is used to detect outliers. As default
the following outlier limit is defined: 
    
    limit = outlier_limit_factor * RMS   (with outlier_limit_factor=1.0)
    
The 'outlier_limit_factor' can be chosen as argument by initialization of a LinearRegression class object. In addition
the number of iteration for the outlier detection can be chosen with the argument 'outlier_iteration'.

Example:
--------

# Import Midgard LinearRegression class of linear_regression module
from midgard.math.linear_regression import LinearRegression

# Generate LinearRegression object
linreg = LinearRegression(x,y)

# Get solution
interception = linreg.interception
slope = linreg.slope
"""

# Standard library imports
from dataclasses import dataclass
from typing import Union

# Third party imports
import numpy as np
import statsmodels.api as sm

@dataclass
class LinearRegression:
    """Linear regression class
    
    Following arguments can be chosen by initialization of LinearRegression class objects:
        
        | Arguments             | Type       | Description                                                           |
        |:----------------------| :----------| :---------------------------------------------------------------------|
        | outlier_limit_factor  | float      | RMS of residuals are used for detecting outliers, whereby             |
        |                       |            | 'outlier_limit_factor' * 'RMS' is used as limit. As default is        |
        |                       |            | 'outlier_limit_factor' = 1.0 chosen.                                  |
        | outlier_iteration     | int        | Number of iteration used to detect and reject outliers. Default is 1. |
        | reject_outlier        | bool       | Determine if outliers should be detected and rejected. Default is     |
        |                       |            | 'False', which means that no outliers are rejected.                   |
        | x                     | np.ndarray | X training data                                                       |
        | y                     | np.ndarray | Y target data                                                         | 
        
    """
    x: Union[np.ndarray, list]
    y: Union[np.ndarray, list]
    reject_outlier: bool = False
    outlier_limit_factor: float = 1.0
    outlier_iteration: int = 1
    
    def __post_init__(self):
        
        if type(self.x) == list:
            self.x = np.array(self.x)
        
        if type(self.y) == list:
            self.y = np.array(self.x)    
                
        if self.reject_outlier:
            self._result = self._generate_result_and_reject_outlier()
        else:
            self._result = self._generate_result()
    
    @property
    def interception(self) -> np.float64:
        """Interception of regression line
        """
        return self._result.params[0]
    
    @property
    def interception_sigma(self) -> np.float64:
        """Standard deviation of interception of regression line
        """
        return self._result.bse[0]

    @property
    def residuals(self) -> np.ndarray:
        """Residuals of regression line (observed - modeled)
        """
        return self._result.resid
            
    @property
    def rms(self) -> np.float64:
        """RMS of regression line residuals
        """
        return np.sqrt(np.nanmean(np.square(self.residuals)))
    
    @property
    def r_square(self) -> np.float64:
        """Coefficient of determination R^2
        
        Better fitted regression line, if R^2 closer to 1.
        """
        return self._result.rsquared

    @property
    def slope(self) -> np.float64:
        """Slope of regression line
        """
        return self._result.params[1]
    
    @property
    def slope_sigma(self) -> np.float64:
        """Standard deviation of slope of regression line
        """
        return self._result.bse[1]
      
    @property
    def y_modeled(self) -> np.ndarray:
        """Modeled y-data for given x-data
        """
        return self._result.predict(self._x_ones)
    
    def _generate_result_and_reject_outlier(self) -> object:
        """Generate LinearRegression result by rejecting outliers of x and y arrays
        """       
       
        for ii in range(self.outlier_iteration):
            
            # Make linear regression analysis
            result = sm.OLS(self.y, self._x_ones).fit()
            rms = np.sqrt(np.nanmean(np.square(result.resid)))
            limit = self.outlier_limit_factor * rms
            
            # Detect outliers based on RMS limit and decimate x and y arrays
            idx = np.abs(result.resid) < limit
            self.x = self.x[idx]
            self.y = self.y[idx]
            
        return sm.OLS(self.y, self._x_ones).fit()
    
    
    def _generate_result(self) -> object:
        """Generate LinearRegression result object
        """
        return sm.OLS(self.y, self._x_ones).fit()

    
    @property
    def _x_ones(self) -> object:
        """Add column with ones to x
        
        This is needed to get also interception results.
        """
        return sm.add_constant(self.x)  
