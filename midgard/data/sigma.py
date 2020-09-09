"""Array with sigma values

See https://docs.scipy.org/doc/numpy/user/basics.subclassing.html for information about subclassing Numpy arrays.

SigmaArray is a regular Numpy array with an added field, sigma.
"""

# Third party imports
import numpy as np


class SigmaArray(np.ndarray):

    type = "sigma"

    def __new__(cls, values, sigma=None, unit=None):
        """Create a new SigmaArray"""
        obj = np.asarray(values, dtype=float).view(cls)
        sigma = np.array(sigma) if sigma is not None else np.full(values.shape, np.nan)
        if sigma.ndim == 0:
            sigma = sigma.item()
        obj._sigma = sigma
        obj._unit = unit
        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new SigmaArray is created"""
        if obj is None:
            return

        sigma_sliced = getattr(obj, "_sigma_sliced", None)
        if sigma_sliced is not None:
            self.sigma = sigma_sliced

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

    def unit(self, _):
        """Unit of SigmaArray

        The subfield sigma share the same unit as the SigmaArray itself"""
        return self._unit

    def set_unit(self, new_unit):
        """Update unit of SigmaArray"""
        self._unit = new_unit

    @classmethod
    def insert(cls, a, pos, b, memo):
        """ Insert b into a at position pos"""
        id_a = id(a)
        if id_a in memo:
            return memo[id_a][-1]

        id_b = id(b)
        if id_b in memo:
            return memo[id_b][-1]

        val = np.insert(np.asarray(a), pos, np.asarray(b))
        sigma = np.insert(a.sigma, pos, b.sigma)
        new_sigma = cls(val, sigma)
        memo[id_a] = (a, new_sigma)
        memo[id_b] = (b, new_sigma)
        return new_sigma

    def fieldnames(self):
        return ["sigma"]

    def __add__(self, _):
        """self + other"""
        return NotImplemented

    def __radd__(self, _):
        """other + self"""
        return NotImplemented

    def __sub__(self, _):
        """self - other"""
        return NotImplemented

    def __rsub__(self, _):
        """other - self"""
        return NotImplemented

    def __iadd__(self, _):
        """self += other"""
        return NotImplemented

    def __isub__(self, _):
        """self -= other"""
        return NotImplemented

    def __matmul__(self, _):
        """self @ _"""
        return NotImplemented

    def __rmatmul__(self, _):
        """_ @ self"""
        return NotImplemented

    def __imatmul__(self, _):
        """self @= _"""
        return NotImplemented

    def __mul__(self, other):
        """self * other """
        val = np.asarray(self) * other
        sigma = self.sigma * other
        return self.__class__(val, sigma)

    def __rmul__(self, other):
        """other * self"""
        return self.__mul__(other)

    def __imul__(self, _):
        """self *= _"""
        return NotImplemented

    def __truediv__(self, _):
        """self / _"""
        return NotImplemented

    def __rtruediv__(self, _):
        """_ / self"""
        return NotImplemented

    def __itruediv__(self, _):
        """self /= _"""
        return NotImplemented

    def __floordiv__(self, _):
        """self // _"""
        return NotImplemented

    def __rfloordiv__(self, _):
        """ _ // self"""
        return NotImplemented

    def __ifloordiv__(self, _):
        """self //= _"""
        return NotImplemented

    def __pow__(self, _):
        """ self ** _"""
        return NotImplemented

    def __rpow(self, _):
        """ _ ** self """
        return NotImplemented

    def __ipow__(self, _):
        """ self **= _"""
        return NotImplemented

    def __deepcopy__(self, memo):
        new_sigma_array = self.__class__(np.asarray(self), self.sigma)
        memo[id(self)] = new_sigma_array
        return new_sigma_array

    def __setitem__(self, item, value):
        """TODO"""
        return super().__setitem__(item, value)

    def __getitem__(self, item):
        """Update _sigma_sliced with correct shape, used by __array_finalize__"""
        self._sigma_sliced = self.sigma[item]
        from_super = super().__getitem__(item)
        if isinstance(item, int):
            return self.__class__(from_super, self._sigma_sliced)
        return from_super
