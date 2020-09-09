"""Midgard library module with utility functions for easier script development

Example:
from midgard.dev import util
directory, date = util.parse_args('string', 'date')

Description:

This module provides the boilerplate code necessary for starting a script. In particular handling of command line 
arguments and default options including --help are done.

"""

# Standard library imports
from datetime import date, datetime
import functools
from importlib import import_module
import os
import pathlib
import platform
import re
import sys
from typing import Any, Dict, List, Tuple, Union

# Midgard imports
from midgard.dev import log
from midgard.files import files

# Source code cache, used by trace_source
_CACHE_SRC = dict()


def check_help_and_version(module: str, doc_module: str = None, replace_vars: Dict[str, str]=dict()) -> None:
    """Show help or version if asked for

    Show the help message parsed from the script's docstring if -h or --help option is given. Show the script's version
    if --version is given.

    Args:
        module:       Module name.
        doc_module:   Module containing help text.
        replace_vars: Dictionary with variable for replacement in docstring
    """
    # Help message
    if check_options("-h", "--help"):
        print(_get_doc(doc_module).format(**replace_vars))
        raise SystemExit

    # Version information
    if check_options("--version"):
        _print_version(module)
        raise SystemExit


def check_options(*options: Tuple[str]) -> str:
    """Check if any of a list of options is specified on the command line

    Returns the actual option that is specified. The first option specified on the command line is returned if there
    are several matches. Returns the empty string if no option is specified. This means that this method works fine
    also in a boolean context, for example

        if check_options('-F', '--force'):
            do_something()

    Args:
        options:   Strings specifying which options to check for, including '-'-prefix.

    Returns:
        String: Option that is specified, blank string if no option is specified

    """
    cmd_argv = [a.split("=")[0] for a in sys.argv[1:]]

    for option in cmd_argv:
        if option in options:
            return option

    return ""


def get_callers() -> str:
    """Get a list of methods calling this function

    Returns:
        Lists all methods calling the function
    """
    callers = list()
    caller = sys._getframe(1)
    while caller:
        func_name = caller.f_code.co_name
        line_no = caller.f_lineno
        file_name = caller.f_code.co_filename
        if file_name.endswith(".py"):
            module_name = file_name[-file_name[::-1].find("/erehw/") : -3].replace("/", ".")
            callers.insert(0, "{}.{} ({})".format(module_name, func_name, line_no))

        caller = caller.f_back

    return "\n    -> ".join(callers)


def get_pid_and_server() -> str:
    """Find process id and name of server the analysis is running on

    Use the platform.uname to find servername instead of os.uname because the latter is not supported on Windows.
    
    Returns:
        Process id and name of server
    """
    pid = os.getpid()
    server = platform.uname().node
    return f"{pid}@{server}"


def get_program_info(module: str) -> str:
    """Get the name and the version of the running program
    
    Args:
        module: Module name.
    
    Returns:
        Program name and version
    """
    return f"{get_program_name()} v{module.__version__}"


def get_program_name() -> str:
    """Get the name of the running program

    Returns:
        String trying to be similar to how the user called the program.
    """
    program_name = sys.argv[0]
    if not program_name.startswith("./"):
        program_name = pathlib.Path(program_name).stem
    return program_name


def get_python_version() -> str:
    """ Find python version used

    Returns:
        Name of executable and version number
    """
    pyexe = pathlib.Path(sys.executable).stem
    version = ".".join(str(v) for v in sys.version_info[:3])
    return f"{pyexe}, version {version}"


def not_implemented() -> None:
    """A placeholder for functions that are not implemented yet

    A note about the missing implementation is written to the log.
    """
    caller = sys._getframe(1)
    funcname = caller.f_code.co_name
    args = ", ".join([k + "=" + str(v) for k, v in caller.f_locals.items()])
    filename = caller.f_code.co_filename
    lineno = caller.f_lineno
    log.fatal(f"Function {funcname}({args}) is not implemented in {filename}, line {lineno}")


def no_traceback(func):
    """Decorator for turning off traceback, instead printing a simple error message

    Use the option --show_tb to show the traceback anyway.
    """
    if check_options("-T", "--showtb"):
        return func

    def no_traceback_hook(_not_used_1, value, _not_used_2):
        """Only prints the error message, no traceback."""
        log.error(str(value))

    @functools.wraps(func)
    def _no_traceback(*args, **kwargs):
        remember_excepthook = sys.excepthook
        sys.excepthook = no_traceback_hook
        values = func(*args, **kwargs)
        sys.excepthook = remember_excepthook
        return values

    return _no_traceback


@no_traceback
def parse_args(*param_types: Tuple[str], doc_module: str = None) -> Union[Any, List[Any]]:
    """Parse command line arguments and general options

    Parse arguments from the given parameter types.

    Args:
        param_types: Strings describing the expected parameter types. Each string must be one of the keys in #_PARSERS.
        doc_module:  Module containing help text.

    Returns:
        List of command line arguments parsed according to param_types.
    """
    # Parse arguments
    try:
        arguments = [_PARSERS[type]() for type in param_types]
    except Exception:
        print(_get_doc(doc_module))
        raise

    # Return arguments (scalar if only one element, None if list is empty)
    if len(arguments) > 1:
        return arguments
    elif arguments:
        return arguments[0]


def options2args(options: List[str]) -> Union[List[str], Dict[str, str]]:
    """Convert a list of command line options to a args and kwargs 
    
    The options should be specified as a string with the necessary - or -- in front and options with a value should
    by separated by = (e.g. --station=stas).
    
    Args:
        options: List with options
        
    Returns:
        Tuple with non-keyword arguments and with keyword arguments
    
    """
    args = list()
    kwargs = dict()
    for a in options:
        if "=" in a:
            a = a.split("=", maxsplit=1)
            kwargs[a[0].lstrip("-")] = a[1]
        else:
            args.append(a)
    return args, kwargs


def read_option_value(option: str, default: str = "") -> str:
    """Read the value of one command line option

    The option should be specified as a string with the necessary - or -- in front. If that option is not one of the
    command line arguments, default is returned. If there is a value following the option that value is returned as a
    string (separated by =). If there are several occurences of the option, the first one is returned.

    Args:
        option:    Option specified with the leading - or --.
        default:   Optional default value that is returned if the option is not specified.

    Returns:
        The option or the value of the option. The default value if the option is not specified.
    """
    for arg in sys.argv[1:]:
        if arg.startswith(f"{option}="):
            # Remove the part up to and including the first =-sign
            return arg.split("=", maxsplit=1)[-1]

    return default


def write_requirements(file_path: Union[str, pathlib.Path]) -> None:
    """Write requirements (python modules) to file for reproducibility.

    Note that this only stores the modules that have been imported, and that have a `__version__`-attribute (see PEP
    396 - https://www.python.org/dev/peps/pep-0396/)
    
    Args:
        file_path: File path.
    """
    # Find versions of imported modules (use list() for copy in case modules are imported when reading __version__)
    reqs = {n: getattr(m, "__version__", None) for n, m in list(sys.modules.items())}
    reqs["python"] = platform.python_version()
    reqs_str = "\n".join(sorted("{}=={}".format(m, v.strip()) for m, v in reqs.items() if isinstance(v, str)))

    # Write to requirements-file
    with files.open(file_path, mode="w") as fid:
        fid.write(reqs_str + "\n")


def _get_doc(doc_module: str = None) -> str:
    """Get the docstring of the running program

    Args:
        doc_module:  String, name of the module with docstring. Default is __main__.

    Returns:
        String, the docstring of the given module.
    """
    if doc_module is None:
        doc_module = "__main__"

    doc = sys.modules[doc_module].__doc__

    return "" if doc is None else doc


def _get_program_version(module: str) -> str:
    """Get version info for the running program from SVN keywords

    The version of the program is read from the main __init__.py-file of the module. 

    Args:
        module:      Module name.

    Returns:
        Information about the version of the given module (running script).
    """
    return f"{get_program_name()}  v{import_module(module).__version__}"


def _next_argument():
    """Return the next argument as a string

    The next argument is returned. Options (strings starting with -) are ignored. The argument is removed from the 
    sys.argv-list.

    Returns:
        String with the next argument.
    """
    for idx in range(1, len(sys.argv)):
        if not sys.argv[idx].startswith("-"):
            return sys.argv.pop(idx)

    raise TypeError("Missing argument")


def _parse_date() -> date:
    """Return the three next arguments as a date

    The three next arguments are parsed as a datetime-object. An error-message is raised if the arguments are not of
    the required form.

    Returns:
        Datetime-object with the date specified in the three next arguments.
    """
    try:
        return date(_parse_int(), _parse_int(), _parse_int())
    except (ValueError, TypeError) as err:
        err.args = (f"{err.args[0]}\n  Date should be written year month day, for instance {date.today():%Y %m %d}",)
        raise


def _parse_doy() -> datetime:
    """Return the two next arguments as a date

    The two next arguments are parsed as a year and day-of-year. An error-message is raised if the arguments are not of
    the required form.

    Returns:
        Datetime: The date specified as year and day-of-year in the two next arguments.
    """
    try:
        return datetime.strptime("{} {}".format(_parse_int(), _parse_int()), "%Y %j").date()
    except ValueError as err:
        err.args = (err.args[0] + "\n    Date should be written year doy, for instance 2009 306",)
        raise


def _parse_float() -> float:
    """Return the next argument as a float

    The next argument is returned. Options (strings starting with -) are ignored. The argument is removed from the
    sys.argv-list. A ValueError is raised if the argument can not be parsed as a float.

    Returns:
        Float with the next argument.
    """
    return float(_next_argument())


def _parse_int() -> int:
    """Return the next argument as an int

    The next argument is returned. Options (strings starting with -) are ignored. The argument is removed from the 
    sys.argv-list. A ValueError is raised if the argument can not be parsed as an int.

    Returns:
        Int with the next argument.
    """
    return int(_next_argument())


def _print_version(module: str) -> str:
    """Print program version

    Args:
        module:    Module Name.
    """
    print(_get_program_version(module))


def _print_help_from_doc(doc_module: Union[None, str]=None, replace_vars: Dict[str, str]=dict()) -> str:
    """Filter the docstring to make it a better help text and print it

    Removes @-directives in the docstring. Furthermore, we replace the Example-heading used by Doxygen with Usage as 
    that makes more sense in a help text. Finally $-symbols at the beginning and end of lines, as introduced by the SVN
    keyword substitution, are removed.
    """
    doc = _get_doc(doc_module).format(**replace_vars)

    for line in doc.splitlines():
        if line.startswith("@"):
            continue
        line = re.sub(r"::", ":", line)
        line = re.sub(r"^\$| ?\$$", "", line)
        print(line)


# Parsers for each parameter type
_PARSERS = {"date": _parse_date, "doy": _parse_doy, "float": _parse_float, "int": _parse_int, "string": _next_argument}

# Store string about how program is started
COMMAND = "{} {}".format(get_program_name(), " ".join(sys.argv[1:]))
