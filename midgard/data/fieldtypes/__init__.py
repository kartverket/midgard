"""Field types that can be used by Dataset

"""
# Standard library imports
from typing import Callable, List

# Midgard imports
from midgard.dev import plugins


def names() -> List[str]:
    """Names of fieldtype plugins"""
    return plugins.names(__name__)


def function(plugin_name: str) -> Callable:
    """Function creating new field"""
    return plugins.get(__name__, plugin_name=plugin_name).function
