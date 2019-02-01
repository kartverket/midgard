"""Midgard library module for caching

Description:
------------

Adds caching to properties on classes, using the recipe explained in Python
Cookbook, 3rd ed. Recipe 8.10.

Also, adds a cached property that may depend on other data, with the
possibility to reset the cache if the dependencies change.

"""
# Standard library imports
import functools
from typing import Any, cast, Callable, Dict, List, Set, Tuple

# Cache for dependent properties
_DEPENDENT_PROPERTIES: Dict[str, Set[Tuple[str, str]]] = dict()


class property:
    """Cached property, see Python Cookbook, 3rd ed. Recipe 8.10."""

    def __init__(self, fget: Callable) -> None:
        """Set up decorator"""
        self.fget = fget
        functools.update_wrapper(cast(Callable, self), fget)

    def __get__(self, instance: Any, cls: Any) -> Any:
        """Overwrite the value, the first time the property is calculated"""
        if instance is None:
            return self
        else:
            value = self.fget(instance)
            setattr(instance, self.fget.__name__, value)
            return value


class register_dependencies(type):
    """Metaclass for registering dependencies using dot notation"""

    _dependencies: List[str] = list()

    def __call__(cls, fget: Callable) -> Any:
        *container, name = fget.__qualname__.split(".")
        for dependency in cls._dependencies:
            _DEPENDENT_PROPERTIES.setdefault(dependency, set()).add((".".join(container), name))
        return super().__call__(fget)

    def __getattr__(cls, key: str) -> Any:
        cls._dependencies.append(key)
        return cls


class dependent_property(property, metaclass=register_dependencies):
    """Decorator for cached properties that can be reset when dependencies change"""

    pass


def forget_dependent_values(obj: object, *dependencies: str) -> None:
    """Reset cache when given dependencies change"""
    for dependency in dependencies:
        for container, prop in _DEPENDENT_PROPERTIES.get(dependency, ()):
            if container == obj.__class__.__qualname__:
                try:
                    delattr(obj, prop)
                except AttributeError:
                    pass


# Include lru_cache from standard library for completeness
function = functools.lru_cache
