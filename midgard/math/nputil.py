"""Utility wrapper for numpy functions

Makes sure numpy functions can be called in a similar fashion for different use cases
 + both 1- and 2-dimensional input
 + both single values and arrays

"""
import functools

# Third party imports
import numpy as np


def unit_vector(vector):
    if vector.ndim == 1:
        return vector / np.linalg.norm(vector)
    elif vector.ndim == 2:
        return vector / np.linalg.norm(vector, axis=1)[:, None]
    else:
        raise ValueError(f"vector must be 1- or 2-dimensional, not {vector.ndim}-dimensional")


def norm(vector):
    return np.linalg.norm(vector, axis=vector.ndim - 1)


def take(vector, item):
    vector = np.asarray(vector)
    return np.take(vector, item, axis=vector.ndim - 1)


def col(vector):
    vector = np.asarray(vector)
    return np.expand_dims(vector, axis=vector.ndim)


def row(vector):
    vector = np.asarray(vector)
    return np.expand_dims(vector, axis=vector.ndim - 1)


class HashArray(np.ndarray):
    def __new__(cls, val):
        """Create a new hashable array"""

        obj = np.asarray(val).view(cls)
        obj.flags.writeable = False
        return obj

    def __array_finalize__(self, obj):
        """Called automatically when a new HashArray is created"""
        if obj is None:
            return

        obj.flags.writeable = False

    def __hash__(self):
        return hash(self.tobytes())

    def __eq__(self, other):
        return self.data.tobytes() == other.data.tobytes()


def hashable(func):
    """Decorator for functions with numpy arrays as input arguments that will benefit from caching

    Example:

    from midgard.math import nputil
    from functools import lru_cache

    @nputil.hashable
    @lru_cache()
    def test_func(a: np.ndarray, b: np.ndarray = None)
        do_something
        return something
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        new_args_list = list()
        for arg in args:
            if isinstance(arg, np.ndarray):
                arg = HashArray(arg)
            new_args_list.append(arg)

        for k, v in kwargs.items():
            if isinstance(v, np.ndarray):
                kwargs[k] = HashArray(v)
        return func(*new_args_list, **kwargs)

    return wrapper
