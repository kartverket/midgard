"""Field types that can be used by Dataset

"""
# Standard library imports
from typing import Callable, List, Any

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import plugins


def names() -> List[str]:
    """Names of fieldtype plugins"""
    return plugins.names(__name__)


def function(plugin_name: str) -> Callable:
    """Function creating new field"""
    return plugins.get(__name__, plugin_name=plugin_name).function


def fieldtype(data: Any) -> Callable:
    """Find correct field type for given data"""
    try:
        return data.type
    except AttributeError:
        for ftype in names():
            func = function(ftype)
            if func.dtype is not None:
                if np.issubdtype(func.dtype, data.dtype.type):
                    return ftype
    raise TypeError(f"Unable to find suitable fieldtype for {data}")
