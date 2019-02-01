"""Midgard library module defining an assortment of constants

Description:
------------

This module provides constants that are used within the Midgard project. The actual constants are defined in the
`constants.conf` file (see the file list for location). See that file for references and for adding or changing
constants.

The constants are stored as module variables so they can be used simply as `constant.c` as in the example above. Some
models use particular values for constants that are different from the conventional ones. This is handled by the source
parameter. For instance, the EGM 2008 gravity field is calculated with a value for GM different from the IERS
Conventions value, using::

    constant.get('GM', source='egm_2008')

instead of simply `constant.GM`.


Example:
--------

    >>> from midgard.math.constant import Constant
    >>> print(f"The speed of light is {constant.c:0.2f}")
    The speed of light is 299792458.00


Todo:
-----

Rewrite as a class instead of a module, to have somewhat cleaner code (and be more consistent with things like
lib.unit).

"""
# Standard library imports
from contextlib import contextmanager
from typing import List

try:
    import importlib.resources as importlib_resources  # Python >= 3.7
except ImportError:
    import importlib_resources  # Python <= 3.6:  pip install importlib_resources

# Midgard imports
from midgard.config.config import Configuration
from midgard.dev import exceptions


class Constant:

    _constants = Configuration("constant")

    def __init__(self) -> None:
        # Read constants from file
        package, _, name = __name__.rpartition(".")
        with importlib_resources.path(package, f"{name}.txt") as path:
            self.update_from_file(path)

        # Set default source
        self._source = "default"

    def update_from_file(self, file_path):
        """Update list of constants from file"""
        self._constants.update_from_file(file_path, case_sensitive=True)

    @property
    def source(self):
        return self._source

    def get(self, constant: str, source: str = None) -> float:
        """Get the value of one constant

        Note that if you need the default value of the constant (from the
        default source) it is typically better to read it as a property. That
        is, `constant.c` is preferred to `constant.get('c')`.

        Args:
            constant:   Name of the constant.
            source:     Source from which the constant is defined.

        Returns:
            Value of constant.
        """
        source = self.source if source is None else source

        try:
            return self._constants[constant][source].float
        except exceptions.MissingSectionError:
            raise exceptions.UnknownConstantError(
                f"Constant {constant!r} is not defined in {', '.join(self._constants.sources)}"
            ) from None
        except exceptions.MissingEntryError:
            raise exceptions.UnknownConstantError(
                f"Constant {constant!r} is not defined by source {source!r} in {', '.join(self._constants.sources)}"
            ) from None

    def unit(self, constant: str) -> str:
        """Unit of constant"""
        try:
            return self._constants[constant].__unit__.str
        except exceptions.MissingSectionError:
            raise exceptions.UnknownConstantError(
                f"Constant {constant!r} is not defined in {', '.join(self._constants.sources)}"
            ) from None
        except exceptions.MissingEntryError:
            raise exceptions.UnitError(
                f"Constant {constant!r} has not defined a unit in {', '.join(self._constants.sources)}"
            ) from None

    @contextmanager
    def use_source(self, source: str) -> None:
        """Context manager for handling different sources

        Example:
            >>> constant.GM
            398600441800000.0

            >>> with constant.use_source("de430"):
            ...     print(constant.GM)
            ...
            398600435436000.0

        Args:
            source:  Name of source of constant.
        """
        previous_source = self.source
        self._source = source
        try:
            yield None
        finally:
            self._source = previous_source

    def __getattr__(self, constant: str) -> float:
        """Get constant as an attribute with dot-notation"""
        if constant in self._constants.section_names:
            try:
                return self._constants[constant][self.source].float
            except exceptions.MissingEntryError:
                raise exceptions.UnknownConstantError(
                    f"Constant {constant!r} is not defined by source {self.source!r} in "
                    f"{', '.join(self._constants.sources)}"
                ) from None

        # Raise error for unknown attributes
        else:
            raise AttributeError(
                f"Constant {constant!r} is not defined in {', '.join(self._constants.sources)}"
            ) from None

    def __dir__(self) -> List[str]:
        """List all constants"""
        return super().__dir__() + list(self._constants.section_names)

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(self._constants.sources)!r})"


constant = Constant()
