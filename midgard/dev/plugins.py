"""Set up a plug-in architecture for Midgard

Description:
------------

In order to be able to add models, parsers, data sources etc without needing to
hardcode names, but rather pick them from configuration files, we use a simple
plug-in architecture. The plug-in mechanism is based on the different plug-ins
registering themselves using the `register` decorator:

    from midgard.dev import plugins

    @plugins.register
    def simple_model(*args, **kwargs):
        ...

Plug-ins are registered based on the name of the module (file) they are defined
in, as well as the package (directory) which contains them. Typically all
plug-ins of a given type are collected in a package, e.g. models, techniques,
parsers, etc. To list all plug-ins in a package use `names`:

    > from midgard.dev import plugins
    > plugins.names('midgard.models')
    ['model_one', 'model_three', 'model_two']

If the optional parameter `config_key` is given, then only plug-ins listed in
the corresponding section in the current configuration file is listed. For
instance, if the configuration file contains a line saying

    ham_models = model_three, model_one

then we can list only the `ham_models` as follows:

    > from midgard.dev import plugins
    > plugins.names('midgard.models', config_key='ham_models')
    ['model_one', 'model_three']

Note that the plug-ins by default are sorted alphabetically.

To run the plug-ins, use either `call_all` or `call_one`. The former calls all
plug-ins and returns a dictionary containing the result from each plug-in. As
with `names` the optional parameter `config_key` may be given:

    > from midgard.dev import plugins
    > plugins.call_all('midgard.models', config_key='ham_models', arg_to_plugin='hello')
    {'model_three': <result from model_three>, 'model_one': <result from model_one>}

Arguments to the plug-ins should be passed as named arguments to `call_all`.

Similarly, one plug-in may be called explicitly using `call_one`:

    > from midgard.dev import plugins
    > plugins.call_one('midgard.models', plugin_name='model_one', arg_to_plugin='hello')
    <result from model_one>

There may be more than one function in each plug-in that is decorated by
`register`. In this case, the default behaviour is that only the first function
will be called. To call the other registered functions one should use the
`list_parts` function to get a list of these functions and call them explicitly
using the `part` optional parameter to `call_one`:

    > from midgard.dev import plugins
    > plugins.list_parts('midgard.techniques', plugin_name='vlbi')
    ['read', 'edit', 'calculate', 'estimate', 'write_result'])
    > for part in plugins.list_parts('midgard.techniques', plugin_name='vlbi'):
    ...   plugins.call_one('midgard.techniques', plugin_name='vlbi', part=part, ...)

"""
# Standard library imports
import functools
import importlib
import inspect
import pathlib
import re
import sys
from typing import Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple

# Midgard imports
from midgard.dev import console
from midgard.dev.exceptions import UnknownPackageError, UnknownPluginError
from midgard.dev import log
from midgard.files import dependencies


# The _PLUGINS-dict is populated by the `register` decorator in each module.
_PLUGINS: Dict[str, Dict[str, Any]] = dict(__aliases__=dict(), __packages__=dict())


# Simple structure containing information about a plug-in
class Plugin(NamedTuple):
    """Information about a plug-in

    Args:
        name:        Name of the plug-in.
        function:    The plug-in.
        file_path:   Path to the source code of the plug-in, may be used to add the source as a dependency.
        sort_value:  Value used when sorting plug-ins in order to control the order they are called.
    """

    name: str
    function: Callable
    file_path: pathlib.Path
    sort_value: int


#
# REGISTER PLUG-INS
#
def register(func: Callable, name: Optional[str] = None, sort_value: int = 0) -> Callable:
    """Decorator used to register a plug-in

    Plug-ins are registered based on the name of the module (file) they are
    defined in, as well as the package (directory) which contains
    them. Typically all plug-ins of a given type are collected in a package,
    e.g. models, techniques, parsers, etc. The path to the source code file is
    also stored. This is used to be able to add the source code as a dependency
    file when the plug-in is called.

    If `name` is given, the plug-in is registered based on this name instead of
    the name of the module. The name of the module is still registered as a
    part that can be used to distinguish between similar plug-ins in different
    files (see for instance how `session` is used in `midgard.pipelines`).

    Args:
        func:        The function that is being registered.
        name:        Alternative name of plug-in. Used by `register_named`.
        sort_value:  The value used when sorting plug-ins. Used by `register_ordered`.

    Returns:
        The function that is being registered.
    """
    # Get information from the function being registered
    package_name, _, plugin_name = func.__module__.rpartition(".")
    package_name = _PLUGINS["__aliases__"].get(package_name, package_name)
    file_path = pathlib.Path(sys.modules[func.__module__].__file__)

    # Store Plugin-object in _PLUGINS dictionary
    _PLUGINS["__packages__"].setdefault(package_name, [package_name])
    plugin_info = _PLUGINS.setdefault(package_name, dict()).setdefault(plugin_name, dict())
    if name is None:
        name = func.__name__  # Name of function is used as default name
        plugin_info.setdefault("__parts__", list()).append(name)  # Only unnamed parts are added to list

    plugin = Plugin(f"{plugin_name}.{name}", func, file_path, sort_value)
    plugin_info[name] = plugin
    log.debug(f"Registering {plugin.name} ({plugin.file_path}) as a {package_name}-plugin")

    # Add first registered unnamed part as default
    if "__parts__" in plugin_info:
        plugin_info["__default__"] = plugin_info[plugin_info["__parts__"][0]]

    return func


def register_named(name: str) -> Callable:
    """Decorator used to register a named plug-in

    This allows for overriding the name used to register the plug-in. See
    `register` for more details.

    Args:
        name:   Name used for plug-in instead of module name.

    Returns:
        Decorator that registers a named function.
    """
    return functools.partial(register, name=name)


def register_ordered(sort_value: int) -> Callable:
    """Decorator used to register a plug-in with a specific sort order

    The sort value should be a number. Lower numbers are sorted first, higher
    numbers last. Plug-ins without an explicit sort_order gets the sort value
    of 0.

    Args:
        sort_value:   The value used when sorting plug-ins.

    Returns:
        Decorator that registers an ordered function.
    """
    return functools.partial(register, sort_value=sort_value)


def get(package_name: str, plugin_name: str, part: Optional[str] = None, prefix: Optional[str] = None) -> Plugin:
    """Get a specific plugin-object

    If the plug-in is not part of the package an UnknownPluginError is raised.

    If there are several functions registered in a plug-in and `part` is not
    specified, then the first function registered in the plug-in will be
    called.

    Args:
        package_name:  Name of package containing plug-ins.
        plugin_name:   Name of the plug-in, i.e. the module containing the plug-in.
        part:          Name of function to call within the plug-in (optional).
        prefix:        Prefix of the plug-in name, used if the plug-in name is not found (optional).

    Returns:
        Plugin-namedtuple representing the plug-in.
    """
    # Get Plugin-object
    plugin_name = load(package_name, plugin_name, prefix=prefix)
    part = "__default__" if part is None else part
    try:
        return _PLUGINS[package_name][plugin_name][part]
    except KeyError:
        # TODO: List available plugins
        raise UnknownPluginError(f"Plugin {part!r} not found for {plugin_name!r} in {package_name!r}") from None


#
# CALL PLUG-INS
#
def call(
    package_name: str,
    plugin_name: str,
    part: Optional[str] = None,
    prefix: Optional[str] = None,
    plugin_logger: Optional[Callable[[str], None]] = None,
    **plugin_args: Any,
) -> Any:
    """Call one plug-in

    Args:
        package_name:   Name of package containing plug-ins.
        plugin_name:    Name of the plug-in, i.e. the module containing the plug-in.
        part:           Name of function to call within the plug-in (optional).
        prefix:         Prefix of the plug-in name, used if the plug-in name is not found (optional).
        plugin_logger:  Function used for logging (optional).
        plugin_args:    Named arguments passed on to the plug-in.

    Returns:
        Return value of the plug-in.
    """
    plugin = get(package_name, plugin_name, part, prefix)

    # Log message about calling plug-in
    if plugin_logger is not None:
        plugin_logger(f"Start plug-in {plugin.name!r} in {package_name!r}")

    # Add dependency to the plug-in
    dependencies.add(plugin.file_path, label=f"plugin:{package_name}")

    # Call plug-in
    return plugin.function(**plugin_args)


def call_all(
    package_name: str,
    plugins: Optional[List[str]] = None,
    part: Optional[str] = None,
    prefix: Optional[str] = None,
    plugin_logger: Optional[Callable[[str], None]] = None,
    **plugin_args: Any,
) -> Dict[str, Any]:
    """Call all plug-ins in a package

    If `plugins` is given, it should be a list of names of plug-ins.  If a
    plug-in listed in the `plugins`-list or in the config file does not exist,
    an UnknownPluginError is raised.

    If `plugins` is not given, all available plugins will be called. Do note,
    however, that this will import all python files in the package.

    Args:
        package_name:   Name of package containing plug-ins.
        plugins:        List of plug-in names that should be used (optional).
        part:           Name of function to call within the plug-ins (optional).
        prefix:         Prefix of the plug-in names, used for a plug-in if it is not found (optional).
        plugin_logger:  Function used for logging (optional).
        plugin_args:    Named arguments passed on to all the plug-ins.

    Returns:
        Dictionary of all results from the plug-ins.
    """
    plugin_names = names(package_name, plugins=plugins, prefix=prefix)
    return {p: call(package_name, p, part=part, plugin_logger=plugin_logger, **plugin_args) for p in plugin_names}


#
# GET DOCUMENTATION FOR PLUG-INS
#
def doc(
    package_name: str,
    plugin_name: str,
    part: Optional[str] = None,
    prefix: Optional[str] = None,
    long_doc: bool = True,
    include_details: bool = False,
    use_module: bool = False,
) -> str:
    """Document one plug-in

    If the plug-in is not part of the package an UnknownPluginError is raised.

    If there are several functions registered in a plug-in and `part` is not
    specified, then the first function registered in the plug-in will be
    documented.

    Args:
        package_name:     Name of package containing plug-ins.
        plugin_name:      Name of the plug-in, i.e. the module containing the plug-in.
        part:             Name of function to call within the plug-in (optional).
        prefix:           Prefix of the plug-in name, used if the plug-in name is unknown (optional).
        long_doc:         Whether to return the long doc-string or the short one-line string (optional).
        include_details:  Whether to include development details like parameters and return values (optional).
        use_module:       Whether to use module doc-string instead of plug-in doc-string (optional).

    Returns:
        Documentation of the plug-in.
    """
    # Get Plugin-object and pick out doc-string
    plugin = get(package_name, plugin_name, part, prefix)
    if use_module:
        doc = sys.modules[plugin.function.__module__].__doc__ or ""
    else:
        doc = plugin.function.__doc__ or ""

    if long_doc:
        # Strip short description and indentation
        doc = console.dedent("\n\n".join(doc.split("\n\n")[1:]))
        lines = doc.rstrip().splitlines()

        # Stop before Args:, Returns: etc if details should not be included
        idx_args = len(lines)
        if not include_details:
            re_args = re.compile("(Args:|Returns:|Details:|Examples?:|Attributes:)$")
            try:
                idx_args = [re_args.match(l) is not None for l in lines].index(True)
            except ValueError:
                pass
        return "\n".join(lines[:idx_args]).strip()

    else:
        # Return short description
        return doc.split("\n\n")[0].replace("\n", " ").strip()


def doc_all(
    package_name: str,
    plugins: Optional[Iterable[str]] = None,
    prefix: Optional[str] = None,
    long_doc: bool = True,
    include_details: bool = False,
    use_module: bool = False,
) -> Dict[str, str]:
    """Call all plug-ins in a package

    If `plugins` is given, it should be a list of names of plug-ins. If a
    plug-in listed in the `plugins`-list does not exist, an UnknownPluginError
    is raised.

    If `plugins` is not given, all available plugins will be called. Do note,
    however, that this will import all python files in the package.

    Args:
        package_name:     Name of package containing plug-ins.
        plugins:          List of plug-ins that should be used (optional).
        prefix:           Prefix of the plug-in names, used if any of the plug-ins are unknown (optional).
        long_doc:         Whether to return the long doc-string or the short one-line string (optional).
        include_details:  Whether to include development details like parameters and return values (optional).
        use_module:       Whether to use module doc-string instead of plug-in doc-string (optional).

    Returns:
        Dictionary of all doc-strings from the plug-ins.
    """
    plugin_names = names(package_name, plugins=plugins, prefix=prefix)
    return {
        p: doc(package_name, p, long_doc=long_doc, include_details=include_details, use_module=use_module)
        for p in plugin_names
    }


def signature(
    package_name: str, plugin_name: str, part: Optional[str] = None, prefix: Optional[str] = None
) -> inspect.Signature:
    """Get signature of a plug-in

    If the plug-in is not part of the package an UnknownPluginError is raised.

    If there are several functions registered in a plug-in and `part` is not
    specified, then the first function registered in the plug-in will be
    documented.

    Args:
        package_name:     Name of package containing plug-ins.
        plugin_name:      Name of the plug-in, i.e. the module containing the plug-in.
        part:             Name of function to call within the plug-in (optional).
        prefix:           Prefix of the plug-in name, used if the plug-in name is unknown (optional).

    Returns:
        Signature of the plugin
    """
    # Get Plugin-object and pick out signature
    plugin = get(package_name, plugin_name, part, prefix)
    return inspect.signature(plugin.function)


#
# LIST AVAILABLE PLUG-INS
#
def names(package_name: str, plugins: Optional[Iterable[str]] = None, prefix: Optional[str] = None) -> List[str]:
    """List plug-ins in a package

    If `plugins` is given, it should be a list of names of plug-ins.  If a
    plug-in listed in the `plugins`-list does not exist, an UnknownPluginError
    is raised.

    If `plugins` is not given, all available plugins will be listed. Do note,
    however, that this will import all python files in the package.

    Args:
        package_name:  Name of package containing plug-ins.
        plugins:       List of plug-ins that should be used (optional).
        prefix:        Prefix of the plug-in names, used if any of the plug-in names are unknown (optional).

    Returns:
        List of strings with names of plug-ins.
    """
    # Figure out names of plug-ins
    if plugins is None:
        _import_all(package_name)
        plugins = _PLUGINS.get(package_name, dict()).keys()

    # Load each plug-in and return them in sort order
    def _sort_value(plugin: str) -> Tuple[int, str]:
        """Pick out sort_value of plugin"""
        return (getattr(_PLUGINS[package_name][plugin].get("__default__"), "sort_value", 0), plugin)

    return sorted((load(package_name, p, prefix=prefix) for p in plugins), key=_sort_value)


def parts(package_name: str, plugin_name: str, prefix: Optional[str] = None) -> List[str]:
    """List all parts of one plug-in

    Args:
        package_name:  Name of package containing plug-ins.
        plugin_name:   Name of the plug-in.
        prefix:        Prefix of the plug-in name, used if the plug-in name is unknown (optional).

    Returns:
        List: Strings with names of parts.
    """
    plugin_name = load(package_name, plugin_name, prefix=prefix)
    return _PLUGINS[package_name][plugin_name].get("__parts__", list())


def exists(package_name: str, plugin_name: str) -> bool:
    """Check whether or not a plug-in exists in a package

    Tries to import the given plug-in.

    Args:
        package_name:  Name of package containing plug-ins.
        plugin_name:   Name of the plug-in (module).

    Returns:
        True if plug-in exists, False otherwise.
    """
    if plugin_name not in _PLUGINS.get(package_name, dict()):
        try:
            _import_one(package_name, plugin_name)
        except UnknownPluginError:
            return False

    return plugin_name in _PLUGINS.get(package_name, dict())


#
# LOAD PLUG-INS
#
def add_alias(package_name: str, alias: str) -> None:
    """Add alias to plug-in package

    This allows one package of plug-ins to be spread over several directories

    Args:
        package_name:  Name of package containing plug-ins.
        directory:     Additional plug-in directory.
    """
    _PLUGINS["__packages__"].setdefault(package_name, [package_name]).append(alias)
    _PLUGINS["__aliases__"][alias] = package_name


def load(package_name: str, plugin_name: str, prefix: Optional[str] = None) -> str:
    """Load one plug-in from a package

    First tries to load the plugin with the given name. If that fails, it tries
    to load {prefix}_{plugin_name} instead.

    Args:
        package_name:  Name of package containing plug-ins.
        plugin_name:   Name of the plug-in (module).
        prefix:        Prefix of the plug-in name, used if the plug-in name is unknown (optional).

    Returns:
        Actual name of plug-in (with or without prefix).

    """
    if plugin_name not in _PLUGINS.get(package_name, dict()):
        try:
            _import_one(package_name, plugin_name)
        except UnknownPluginError as import_err:
            if prefix:
                try:
                    return load(package_name, f"{prefix}_{plugin_name}")
                except UnknownPluginError:
                    pass
            raise import_err from None  # Raise original exception

    return plugin_name


def _aliases(package_name: str) -> List[str]:
    """Aliases for the given package

    Args:
        package_name:  Name of package.

    Returns:
        List of names of packages (including the given one) containing plugins.
    """
    return _PLUGINS["__packages__"].get(package_name, [package_name])


def _import_one(package_name: str, plugin_name: str) -> None:
    """Import a plugin from a package

    This is essentially just a regular python import. As the module is
    imported, the _PLUGINS-dict will be populated by @register decorated
    functions in the file.

    Args:
        package_name:  Name of package containing plug-ins.
        plugin_name:   Name of the plug-in (module).
    """
    for package in _aliases(package_name):
        module_name = f"{package}.{plugin_name}"
        try:
            importlib.import_module(module_name)
        except ImportError as err:
            # Error comes from a subimport inside the plugin
            if not hasattr(err, "name") or err.name != module_name:
                raise

            # Plugin does not exist, but might be aliased from another package
            else:
                pass  # Just to be explicit, not really necessary

        # Success, do not import more aliases
        else:
            continue

    if plugin_name not in _PLUGINS.get(package_name, dict()):
        raise UnknownPluginError(f"Plug-in {plugin_name!r} not found in package {package_name!r}") from None


def _import_all(package_name: str) -> None:
    """Import the relevant .py-files in the given package directory

    As each file is imported, the _PLUGINS-dict will be populated by @register
    decorated functions in the files.

    Args:
        package_name:  Name of package containing plug-ins.
    """
    file_paths: List[pathlib.Path] = list()
    for package_alias in _aliases(package_name):
        # Figure out the directory of the package by importing it
        try:
            package = importlib.import_module(package_alias)
        except ImportError:
            raise UnknownPackageError(f"Plug-in package {package_name!r} not found") from None

        # List all .py files in the given directory
        directory = pathlib.Path(package.__file__).parent
        file_paths += [f for f in directory.glob("*.py") if not f.stem.startswith("_")]

    # Import all Python files
    for file_path in file_paths:
        plugin_name = file_path.stem
        try:
            _import_one(package_name, plugin_name)
        except UnknownPluginError:
            pass  # OK if .py file does not contain a plugin
