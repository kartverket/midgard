"""Midgard library module for linear regression

Description:
------------

"""

# Standard library imports
from dataclasses import dataclass

# Third party imports
import numpy as np

@dataclass
class LinearRegression:
    __slots__ = ['x', 'y']
    x: np.ndarray
    y: np.ndarray
    
    @property
    def interception(self) -> np.ndarray:
        """Interception of regression line
        """
        return self._model.intercept_

    @property
    def residuals(self) -> np.ndarray:
        """Residuals of regression line (observed - modeled)
        """
        return self.y - self.y_modeled
            
    @property
    def rms(self) -> np.ndarray:
        """RMS of regression line residuals
        """
        return np.sqrt(np.nanmean(np.square(self.residuals)))
    
    @property
    def r_square(self) -> np.ndarray:
        """Coefficient of determination R^2
        
        Better fitted regression line, if R^2 closer to 1.
        """
        return self._model.score(self.x[:, None], self.y)

    @property
    def slope(self) -> np.ndarray:
        """Slope of regression line
        """
        return self._model.coef_[0]
  
    @property
    def y_modeled(self) -> np.ndarray:
        """Modeled y-data for given x-data
        """
        return self._model.predict(self.x[:, None])

    @property
    def _model(self) -> object:
        """Generate LinearRegression object
        """
        from sklearn.linear_model import LinearRegression
        return LinearRegression().fit(self.x[:, None], self.y)
