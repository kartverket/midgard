"""Python wrapper around C-libraries

Description:
------------

Loads a C-library. If a library is missing, a mock library is returned. If this
mock is used for anything, a warning will be printed. This is done to avoid
dependencies to all the C/C++-libraries for Python programs only using some of
them.
"""

# Standard library imports
import ctypes as c
from ctypes import util as c_util
import sys


def load_name(library_name, func_specs=None, name_patterns=None):
    """Load the given shared C-library

    See `load_path` for an explanation of the `func_specs` and
    `name_patterns`-arguments.

    Args:
        library_name (String): The name of the library.
        func_specs (Dict):     Specification of types in lib (see load_path).
        name_patterns (List):  Name mangling patterns (see load_path).

    Returns:
        ctypes.CDLL:   Representation of the shared library.
    """
    library_path = c_util.find_library(library_name)
    return load_path(library_path, func_specs=func_specs, name_patterns=name_patterns)


def load_path(library_path, func_specs=None, name_patterns=None):
    """Load the given shared C-library

    The optional func_specs-dictionary can be used to specify argument and
    return types of functions in the library (see the ctypes documentation for
    information about argtypes and restype). The dictionary should be on the
    form::

        func_spec = {'func_1': dict(func_name='name_of_func_1_in_lib',
                                    argtypes=[ ... argtypes of func_1 ... ],
                                    restype=... restype of func_1 ...),
                     'func_2': ...
                    }

    If the library is not found, a mock library is returned instead. The mock
    library will print a warning if it is used.

    For some libraries, name mangling is used and this might be different
    depending on operating system and how the library is compiled. For
    instance, in a Fortran library the function `Test` might be represented as
    `__Test` on a Windows system and `test_` (with lower-case `t`) on a Linux
    system. This can be handled by providing a list of possible patterns. The
    above example can be handled by::

        name_patterns = ('__{func_name}', '{func_name_lower}_')

    In this case, each function in func_specs is looked up by testing each
    pattern in turn until a match is found.

    Args:
        library_path (String): The path to the library.
        func_specs (Dict):     Specification of types in library (see above).
        name_patterns (List):  Name mangling patterns (see above).

    Returns:
        ctypes.CDLL:   Representation of the shared library.
    """
    library_handle = c.cdll.LoadLibrary(library_path)

    # Return a Mock object if the library is not found
    if library_handle._name is None:
        mock = SimpleMock(name=library_path)
        return mock

    # Handle name mangling
    if name_patterns is None:

        def mangled_name(name):
            return name

    else:

        def mangled_name(name):
            for pattern in name_patterns:
                full_name = pattern.format(func_name=name, func_name_lower=name.lower())
                if hasattr(library_handle, full_name):
                    return full_name
            return name

    # Set argument and return types on functions
    if func_specs:
        for name, spec in func_specs.items():
            if "func_name" in spec:
                func_name = mangled_name(spec["func_name"])
            else:
                func_name = mangled_name(name)
            func = getattr(library_handle, func_name)
            delattr(library_handle, func_name)
            if "argtypes" in spec:
                func.argtypes = spec["argtypes"]
            if "restype" in spec:
                func.restype = spec["restype"]
            setattr(library_handle, name, func)

    return library_handle


class SimpleMock:
    """Class that can stand in for any other object

    The SimpleMock is used to stand in for any library that can not be
    imported. The mock object simply returns itself whenever it is called, or
    any attributes are looked up on the object. This is done, to avoid
    ImportErrors when a library is imported, but never used (typically because
    a plugin is loaded but never called).

    Instead the ImportError is raised when the SimpleMock is used in any
    way. The ImportError will only be raised once for any SimpleMock-object
    (which is only important if the ImportError is caught and the program
    carries on).
    """

    def __init__(self, name, raise_error=True):
        """Initialize SimpleMock object

        Args:
            name (String):      Name of SimpleMock-object.
            raise_error (Bool): Should ImportError be raised when using object.
        """
        self._name = name
        self._children = dict()
        self._raise_error = raise_error

    def _raise_import_error(self):
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
        line_no = caller.f_lineno
        file_name = caller.f_code.co_filename

        # Raise ImportError with a helpful message
        raise ImportError(
            "The library '{}' is not installed, but is used by '{}' on line {} of {}"
            "".format(self._name, func_name, line_no, file_name)
        )

    def __call__(self, *args, **kwargs):
        """Return the same SimpleMock-object when it is called

        An ImportError is raised the first time the object is used.

        Returns:
            SimpleMock:   Itself.
        """
        self._raise_import_error()
        return self

    def __getattr__(self, key):
        """Create a child-SimpleMock-object and return it.

        The same child object is returned if the same attribute is gotten
        several times. An ImportError is raised the first time the
        SimpleMock-object is used. Additional errors are not raised for the
        children.

        Args:
            key (String):   Name of attribute.

        Returns:
            SimpleMock:   A child-SimpleMock-object.

        """
        self._raise_import_error()

        if key not in self._children:
            self._children[key] = type(self)("{}.{}".format(self._name, key), raise_error=self._raise_error)
            setattr(self, key, self._children[key])
        return self._children[key]

    def __repr__(self):
        """String representation of the SimpleMock-object

        Returns:
            String: Simple representation of the SimpleMock-object.
        """
        return "{}('{}')".format(self.__class__.__name__, self._name)

    def __str__(self):
        """Convert to the empty string

        Returns:
            String: An empty string.
        """
        return ""
