"""Midgard library module for handling optional dependencies

Description:
------------

Import dependencies that are only necessary for specific parts of Midgard. Using this module will delay raising an
ImportError until the dependency is actually used. This means that if one for instance only wants to run a GNSS
analysis (or only use a Rinex-parser) installing special libraries only used for VLBI is not necessary.

Examples:
---------

The optional import is typically used as follows::

    from midgard.lib import optional
    netCDF4 = optional.optional_import('netCDF4')

"""

# Standard library imports
import importlib
import sys
from typing import Any, Dict, Optional, Union


class SimpleMock:
    """Class that can stand in for any other object

    The SimpleMock is used to stand in for any library that can not be imported. The mock object simply returns itself
    whenever it is called, or any attributes are looked up on the object. This is done, to avoid ImportErrors when a
    library is imported, but never used (for instance if a plugin is loaded but never called).

    Instead the ImportError is raised when the SimpleMock is used in any way. The ImportError will only be raised once
    for any SimpleMock-object (which is only important if the ImportError is caught and the program carries on).

    The exception is if any attributes (`attrs`) are explicitly defined on the mock. No exception is raised if those
    attributes are looked up.
    """

    def __init__(
        self,
        name: str,
        raise_error: bool = True,
        attrs: Optional[Dict[str, Any]] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        """Initialize SimpleMock object

        Args:
            name:         Name of SimpleMock-object. Used for string representation and when raising Errors.
            raise_error:  Whether ImportError should be raised when object is used.
            attrs:        Attributes that should be added to the SimpleMock.
            error_msg:    Text that will be added to error message.
        """
        self._name = name
        self._children: Dict[str, "SimpleMock"] = dict()
        self._raise_error = raise_error
        self._attrs = attrs
        self._error_msg = error_msg

        if attrs is not None:
            for name, attr in attrs.items():
                setattr(self, name, attr)

    def _raise_import_error(self) -> None:
        """Raise an import error when the SimpleMock object is used

        The ImportError is only raised the first time the object is used.
        """
        # Only raise the error once
        if self._raise_error:
            self._raise_error = False
        else:
            return

        # Find calling function
        caller = sys._getframe()
        while caller.f_code.co_filename == __file__:
            caller = caller.f_back
        func_name = caller.f_code.co_name
        line_num = caller.f_lineno
        file_name = caller.f_code.co_filename

        # Raise ImportError with a helpful message
        error_msg = (
            f"The module '{self._name}' is not installed, "
            f"but is used by '{func_name}' on line {line_num} of {file_name}"
        )
        if self._error_msg:
            error_msg += f".\n    {self._error_msg}"
        raise ImportError(error_msg)

    def __call__(self, *args: Any, **kwargs: Any) -> "SimpleMock":
        """Return the same SimpleMock-object when it is called

        An ImportError is raised the first time the object is used.

        Returns:
            Itself.
        """
        self._raise_import_error()
        return self

    def __getattr__(self, key: str) -> Any:
        """Create a child-SimpleMock-object and return it.

        The same child object is returned if the same attribute is gotten several times. An ImportError is raised the
        first time the SimpleMock-object is used. Additional errors are not raised for the children.

        Args:
            key:   Name of attribute.

        Returns:
            A child-SimpleMock-object.
        """
        self._raise_import_error()

        if key not in self._children:
            child_name = f"{self._name}.{key}"
            self._children[key] = type(self)(child_name, raise_error=self._raise_error, attrs=self._attrs)
            setattr(self, key, self._children[key])
        return self._children[key]

    def __repr__(self) -> str:
        """String representation of the SimpleMock-object

        Returns:
            Simple string representation of the SimpleMock-object.
        """
        return f"{self.__class__.__name__}('{self._name}')"


class EmptyStringMock(SimpleMock):
    """A mock object whose properties are all empty strings
    """

    def __getattr__(self, key: str) -> str:
        """All attributes are empty strings.

        Args:
            key:  Name of attribute.

        Returns:
            An empty string.
        """
        return ""


def optional_import(
    module_name: str, raise_error: bool = True, mock_cls: type = SimpleMock, attrs: Optional[Dict[str, Any]] = None
) -> Union[Any, SimpleMock]:  # TODO: Should be typed types.ModuleType? but causes typing errors
    """Try to import an optional module

    If the module does not exist, a SimpleMock-object is returned instead. If this SimpleMock-object is later used, an
    ImportError will be raised then (if `raise_error` is True, which is default).

    Args:
        module_name:   Name of module to import.
        raise_error:   Whether an ImportError should be raised if the module does not exist, but is used.
        attrs:         Attributes that should be added to the SimpleMock used if the module does not exist.

    Returns:
        Imported module object, or a SimpleMock-object if the module can not be imported.
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return mock_cls(module_name, raise_error=raise_error, attrs=attrs)
