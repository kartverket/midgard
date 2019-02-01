"""Array with sigma values

See https://docs.scipy.org/doc/numpy/user/basics.subclassing.html for information about subclassing Numpy arrays.

SigmaArray is a regular Numpy array with an added field, sigma.
"""

# Third party imports
import numpy as np


class SigmaArray(np.ndarray):
    def __new__(cls, values, sigma=None):
        """Create a new SigmaArray"""
        obj = np.asarray(values).view(cls)
        obj.sigma = sigma
        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new SigmaArray is created"""
        if obj is None:
            return
        # Copy sigma from the original object
        self.sigma = getattr(obj, "_sigma_sliced", None)

    @property
    def sigma(self):
        """Sigma values"""
        return self._sigma

    @sigma.setter
    def sigma(self, value):
        """Set sigma values"""
        if value is None:
            self._sigma = np.full(self.shape, np.nan)
        else:
            self._sigma = np.asarray(value) * np.ones(self.shape)

    def __getitem__(self, key):
        """Update _sigma_sliced with correct shape, used by __array_finalize__"""
        self._sigma_sliced = self._sigma[key]
        return super().__getitem__(key)
