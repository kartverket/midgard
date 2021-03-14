# midgard.dev


## midgard.dev.console
Simpler dealing with the console

**Description:**

Utilities for using the console. Mainly wrappers around other libraries to make them easier and more intuitive to use.

Size of console: The two functions `lines()` and `columns()` report the current size of the console.

Textwrapping: The function `fill()` can be used to rewrap a text-string so that it fits inside the console.



**Examples:**

    >>> from midgard.dev import console
    >>> console.columns()  # doctest: +SKIP
    86

    >>> print(console.fill(a_very_long_string))  # doctest: +SKIP
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras tempus eleifend feugiat.
    Maecenas vitae posuere metus. Sed sit amet fermentum velit. Aenean vitae turpis at
    risus sollicitudin fringilla in in nisi. Maecenas vitae ante libero. Aenean ut eros
    consequat, ornare erat at, tempus arcu. Suspendisse velit leo, eleifend eget mi non,
    vehicula ultricies erat. Vestibulum id nisi eget nisl venenatis dignissim. Duis cursus
    quam dui, vel hendrerit nibh lacinia id.

    >>> print(console.color.Fore.YELLOW + console.color.Back.BLUE + 'I am YELLOW text on BLUE backdrop!')  # doctest: +SKIP
    I am YELLOW text on a BLUE background!



### **columns**()

Full name: `midgard.dev.console.columns`

Signature: `() -> int`

The width of the console

**Returns:**

The width of the console in characters.


### **dedent**()

Full name: `midgard.dev.console.dedent`

Signature: `(text: str, num_spaces: Union[int, NoneType] = None) -> str`

Wrapper around textwrap.dedent

Dedents at most num_spaces. If num_spaces is not specified, dedents as much as possible.

**Args:**

- `text`:        Text that will be dedented.
- `num_spaces`:  Number of spaces that will be used for dedentation.

**Returns:**

Dedented string.


### **fill**()

Full name: `midgard.dev.console.fill`

Signature: `(text: str, *, width: Union[int, NoneType] = None, hanging: Union[int, NoneType] = None, **tw_args: Any) -> str`

Wrapper around textwrap.fill

The `tw_args` are passed on to textwrap.fill. See textwrap.TextWrapper for available keyword arguments.

The default value for `width` is console.columns(), while the new argument `hanging`, if defined, will try
to set (although not override) the textwrap-arguments `initial_indent` and `subsequent_indent` to create a hanging
indent (no indent on the first line) of `hanging` spaces.

**Args:**

- `text`:     Text that will be wrapped.
- `width`:    The maximum width (in characters) of wrapped lines.
- `hanging`:  Number of characters used for hanging indent.
- `tw_args`:  Arguments passed on to `textwrap.fill`.

**Returns:**

Wrapped string.


### **indent**()

Full name: `midgard.dev.console.indent`

Signature: `(text: str, num_spaces: int, **tw_args: Any) -> str`

Wrapper around textwrap.indent

The `tw_args` are passed on to textwrap.indent.

**Args:**

- `text`:        Text that will be indented.
- `num_spaces`:  Number of spaces that will be used for indentation.

**Returns:**

Indented string.


### **lines**()

Full name: `midgard.dev.console.lines`

Signature: `() -> int`

The height of the console

**Returns:**

The heigth of the console in characters.


### **num_leading_spaces**()

Full name: `midgard.dev.console.num_leading_spaces`

Signature: `(text: str, space_char: str = ' ') -> int`

Count number of leading spaces in a string

**Args:**

- `text`:        String to count.
- `space_char`:  Which characters count as spaces.

**Returns:**

Number of leading spaces.


### **progress_bar**()

Full name: `midgard.dev.console.progress_bar`

Signature: `(iteration: int, total: int, prefix: str = '')`

Call in a loop to create terminal progress bar

**Args:**

iteration    current iteration
total        total iterations
prefix       prefix string


## midgard.dev.exceptions
Definition of Midgard-specific exceptions

**Description:**

Custom exceptions used by Midgard for more specific error messages and handling.



### **FieldDoesNotExistError**

Full name: `midgard.dev.exceptions.FieldDoesNotExistError`

Signature: `()`



### **FieldExistsError**

Full name: `midgard.dev.exceptions.FieldExistsError`

Signature: `()`



### **InitializationError**

Full name: `midgard.dev.exceptions.InitializationError`

Signature: `()`



### **MidgardException**

Full name: `midgard.dev.exceptions.MidgardException`

Signature: `()`



### **MidgardExit**

Full name: `midgard.dev.exceptions.MidgardExit`

Signature: `()`



### **MissingConfigurationError**

Full name: `midgard.dev.exceptions.MissingConfigurationError`

Signature: `()`



### **MissingDataError**

Full name: `midgard.dev.exceptions.MissingDataError`

Signature: `()`



### **MissingEntryError**

Full name: `midgard.dev.exceptions.MissingEntryError`

Signature: `()`



### **MissingSectionError**

Full name: `midgard.dev.exceptions.MissingSectionError`

Signature: `()`



### **ParserError**

Full name: `midgard.dev.exceptions.ParserError`

Signature: `()`



### **TimerNotRunning**

Full name: `midgard.dev.exceptions.TimerNotRunning`

Signature: `()`



### **TimerRunning**

Full name: `midgard.dev.exceptions.TimerRunning`

Signature: `()`



### **UnitError**

Full name: `midgard.dev.exceptions.UnitError`

Signature: `()`



### **UnknownConstantError**

Full name: `midgard.dev.exceptions.UnknownConstantError`

Signature: `()`



### **UnknownConversionError**

Full name: `midgard.dev.exceptions.UnknownConversionError`

Signature: `()`



### **UnknownEnumError**

Full name: `midgard.dev.exceptions.UnknownEnumError`

Signature: `()`



### **UnknownPackageError**

Full name: `midgard.dev.exceptions.UnknownPackageError`

Signature: `()`



### **UnknownPluginError**

Full name: `midgard.dev.exceptions.UnknownPluginError`

Signature: `()`



### **UnknownSystemError**

Full name: `midgard.dev.exceptions.UnknownSystemError`

Signature: `()`



## midgard.dev.library
Python wrapper around C-libraries

**Description:**

Loads a C-library. If a library is missing, a mock library is returned. If this
mock is used for anything, a warning will be printed. This is done to avoid
dependencies to all the C/C++-libraries for Python programs only using some of
them.


### **SimpleMock**

Full name: `midgard.dev.library.SimpleMock`

Signature: `(name, raise_error=True)`

Class that can stand in for any other object

The SimpleMock is used to stand in for any library that can not be
imported. The mock object simply returns itself whenever it is called, or
any attributes are looked up on the object. This is done, to avoid
ImportErrors when a library is imported, but never used (typically because
a plugin is loaded but never called).

Instead the ImportError is raised when the SimpleMock is used in any
way. The ImportError will only be raised once for any SimpleMock-object
(which is only important if the ImportError is caught and the program
carries on).


### **load_name**()

Full name: `midgard.dev.library.load_name`

Signature: `(library_name, func_specs=None, name_patterns=None)`

Load the given shared C-library

See `load_path` for an explanation of the `func_specs` and
`name_patterns`-arguments.

**Args:**

library_name (String): The name of the library.
func_specs (Dict):     Specification of types in lib (see load_path).
name_patterns (List):  Name mangling patterns (see load_path).

**Returns:**

ctypes.CDLL:   Representation of the shared library.


### **load_path**()

Full name: `midgard.dev.library.load_path`

Signature: `(library_path, func_specs=None, name_patterns=None)`

Load the given shared C-library

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

**Args:**

library_path (String): The path to the library.
func_specs (Dict):     Specification of types in library (see above).
name_patterns (List):  Name mangling patterns (see above).

**Returns:**

ctypes.CDLL:   Representation of the shared library.


## midgard.dev.log
Midgard library module for logging

**Description:**

The Midgard **log** module provides simple logging functionality. 

To use it, you must first add a an active logger. This is typically done using the init-functions: **init()** and/or
 **file_init()**. **init()** initializes a console logger, where logging messages are written to the console. 
**file_init()** initializes a file logger, where logging messages are written to a defined file path.

Following logging levels are defined:
    
| Level      | Description          |
|:-----------|:---------------------|
| **debug**  | Debug messages       |
| **info**   | Information messages |
| **warn**   | Warning messages     |
| **error**  | Error messages       |
| **fatal**  | Fatal error messages |

To write a log message, simply call **log.{level}** (e.g. log.info), whereby {level} is a placeholder for the defined
logging levels in the table above.

To add a different logger, you should subclass the Logger abstract class.


**Example:**

    >>> from midgard.dev import log
    >>> log.init("info", prefix="My prefix")
    >>> n, m = 5, 3
    >>> log.info(f"Calculating the inverse of a {n:>2d}x{m:<2d} matrix")
    INFO  [My prefix] Calculating the inverse of a  5x3  matrix



### **ConsoleLogger**

Full name: `midgard.dev.log.ConsoleLogger`

Signature: `(log_level: Union[str, NoneType] = None, prefix: str = '', use_command_line: bool = True) -> None`

Log to the console, the log level can also be set using command line parameters

### **FileLogger**

Full name: `midgard.dev.log.FileLogger`

Signature: `(file_path: Union[str, pathlib.Path], log_level: Union[str, NoneType] = None, prefix: str = '', rotation: Union[int, NoneType] = None) -> None`

Log to a file, the log files can be rotated so that older files are kept

**Args:**

- `file_path`:      File path.
- `log_level`:      Define level from which logging should be started.
- `prefix`:         Add prefix to logging messages.
- `rotation`:       Logging files are rolled based on given number of rotations. That means, if there are old 
                    log files, they will be moved to files with extension .0, .1 and so on. If the argument
                    is not specified, then existing logging file is overwritten from newer ones.            


### **Logger**

Full name: `midgard.dev.log.Logger`

Signature: `(log_level: Union[str, NoneType] = None, prefix: str = '')`

Abstract class that can be specialized to create new loggers

### **all**()

Full name: `midgard.dev.log.all`

Signature: `(log_text: str, *, level: str = 'all') -> None`

partial(func, *args, **keywords) - new function with partial application
of the given arguments and keywords.


### **blank**()

Full name: `midgard.dev.log.blank`

Signature: `() -> None`

Log blank line

### **debug**()

Full name: `midgard.dev.log.debug`

Signature: `(log_text: str, *, level: str = 'debug') -> None`

partial(func, *args, **keywords) - new function with partial application
of the given arguments and keywords.


### **error**()

Full name: `midgard.dev.log.error`

Signature: `(log_text: str, *, level: str = 'error') -> None`

partial(func, *args, **keywords) - new function with partial application
of the given arguments and keywords.


### **fatal**()

Full name: `midgard.dev.log.fatal`

Signature: `(log_text: str, *, level: str = 'fatal') -> None`

partial(func, *args, **keywords) - new function with partial application
of the given arguments and keywords.


### **file_init**

Full name: `midgard.dev.log.file_init`

Signature: `(file_path: Union[str, pathlib.Path], log_level: Union[str, NoneType] = None, prefix: str = '', rotation: Union[int, NoneType] = None) -> None`

Log to a file, the log files can be rotated so that older files are kept

**Args:**

- `file_path`:      File path.
- `log_level`:      Define level from which logging should be started.
- `prefix`:         Add prefix to logging messages.
- `rotation`:       Logging files are rolled based on given number of rotations. That means, if there are old 
                    log files, they will be moved to files with extension .0, .1 and so on. If the argument
                    is not specified, then existing logging file is overwritten from newer ones.            


### **info**()

Full name: `midgard.dev.log.info`

Signature: `(log_text: str, *, level: str = 'info') -> None`

partial(func, *args, **keywords) - new function with partial application
of the given arguments and keywords.


### **init**

Full name: `midgard.dev.log.init`

Signature: `(log_level: Union[str, NoneType] = None, prefix: str = '', use_command_line: bool = True) -> None`

Log to the console, the log level can also be set using command line parameters

### **log**()

Full name: `midgard.dev.log.log`

Signature: `(log_text: str, level: str) -> None`

Log text at the given level

### **none**()

Full name: `midgard.dev.log.none`

Signature: `(log_text: str, *, level: str = 'none') -> None`

partial(func, *args, **keywords) - new function with partial application
of the given arguments and keywords.


### **print_file**()

Full name: `midgard.dev.log.print_file`

Signature: `(log_path: Union[str, pathlib.Path], log_level: str = 'info', print_func: Callable[[str], NoneType] = <built-in function print>) -> None`

Print a log file with colors, stripping away any item below log_level

### **warn**()

Full name: `midgard.dev.log.warn`

Signature: `(log_text: str, *, level: str = 'warn') -> None`

partial(func, *args, **keywords) - new function with partial application
of the given arguments and keywords.


## midgard.dev.plugins
Set up a plug-in architecture for Midgard

**Description:**

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



### **Plugin**

Full name: `midgard.dev.plugins.Plugin`

Signature: `(name: str, function: Callable, file_path: pathlib.Path, sort_value: int)`

Information about a plug-in

**Args:**

- `name`:        Name of the plug-in.
- `function`:    The plug-in.
- `file_path`:   Path to the source code of the plug-in, may be used to add the source as a dependency.
- `sort_value`:  Value used when sorting plug-ins in order to control the order they are called.


### **add_alias**()

Full name: `midgard.dev.plugins.add_alias`

Signature: `(package_name: str, alias: str) -> None`

Add alias to plug-in package

This allows one package of plug-ins to be spread over several directories

**Args:**

- `package_name`:  Name of package containing plug-ins.
- `directory`:     Additional plug-in directory.


### **call**()

Full name: `midgard.dev.plugins.call`

Signature: `(package_name: str, plugin_name: str, part: Union[str, NoneType] = None, prefix: Union[str, NoneType] = None, plugin_logger: Union[Callable[[str], NoneType], NoneType] = None, **plugin_args: Any) -> Any`

Call one plug-in

**Args:**

- `package_name`:   Name of package containing plug-ins.
- `plugin_name`:    Name of the plug-in, i.e. the module containing the plug-in.
- `part`:           Name of function to call within the plug-in (optional).
- `prefix`:         Prefix of the plug-in name, used if the plug-in name is not found (optional).
- `plugin_logger`:  Function used for logging (optional).
- `plugin_args`:    Named arguments passed on to the plug-in.

**Returns:**

Return value of the plug-in.


### **call_all**()

Full name: `midgard.dev.plugins.call_all`

Signature: `(package_name: str, plugins: Union[List[str], NoneType] = None, part: Union[str, NoneType] = None, prefix: Union[str, NoneType] = None, plugin_logger: Union[Callable[[str], NoneType], NoneType] = None, **plugin_args: Any) -> Dict[str, Any]`

Call all plug-ins in a package

If `plugins` is given, it should be a list of names of plug-ins.  If a
plug-in listed in the `plugins`-list or in the config file does not exist,
an UnknownPluginError is raised.

If `plugins` is not given, all available plugins will be called. Do note,
however, that this will import all python files in the package.

**Args:**

- `package_name`:   Name of package containing plug-ins.
- `plugins`:        List of plug-in names that should be used (optional).
- `part`:           Name of function to call within the plug-ins (optional).
- `prefix`:         Prefix of the plug-in names, used for a plug-in if it is not found (optional).
- `plugin_logger`:  Function used for logging (optional).
- `plugin_args`:    Named arguments passed on to all the plug-ins.

**Returns:**

Dictionary of all results from the plug-ins.


### **doc**()

Full name: `midgard.dev.plugins.doc`

Signature: `(package_name: str, plugin_name: str, part: Union[str, NoneType] = None, prefix: Union[str, NoneType] = None, long_doc: bool = True, include_details: bool = False, use_module: bool = False) -> str`

Document one plug-in

If the plug-in is not part of the package an UnknownPluginError is raised.

If there are several functions registered in a plug-in and `part` is not
specified, then the first function registered in the plug-in will be
documented.

**Args:**

- `package_name`:     Name of package containing plug-ins.
- `plugin_name`:      Name of the plug-in, i.e. the module containing the plug-in.
- `part`:             Name of function to call within the plug-in (optional).
- `prefix`:           Prefix of the plug-in name, used if the plug-in name is unknown (optional).
- `long_doc`:         Whether to return the long doc-string or the short one-line string (optional).
- `include_details`:  Whether to include development details like parameters and return values (optional).
- `use_module`:       Whether to use module doc-string instead of plug-in doc-string (optional).

**Returns:**

Documentation of the plug-in.


### **doc_all**()

Full name: `midgard.dev.plugins.doc_all`

Signature: `(package_name: str, plugins: Union[Iterable[str], NoneType] = None, prefix: Union[str, NoneType] = None, long_doc: bool = True, include_details: bool = False, use_module: bool = False) -> Dict[str, str]`

Call all plug-ins in a package

If `plugins` is given, it should be a list of names of plug-ins. If a
plug-in listed in the `plugins`-list does not exist, an UnknownPluginError
is raised.

If `plugins` is not given, all available plugins will be called. Do note,
however, that this will import all python files in the package.

**Args:**

- `package_name`:     Name of package containing plug-ins.
- `plugins`:          List of plug-ins that should be used (optional).
- `prefix`:           Prefix of the plug-in names, used if any of the plug-ins are unknown (optional).
- `long_doc`:         Whether to return the long doc-string or the short one-line string (optional).
- `include_details`:  Whether to include development details like parameters and return values (optional).
- `use_module`:       Whether to use module doc-string instead of plug-in doc-string (optional).

**Returns:**

Dictionary of all doc-strings from the plug-ins.


### **exists**()

Full name: `midgard.dev.plugins.exists`

Signature: `(package_name: str, plugin_name: str) -> bool`

Check whether or not a plug-in exists in a package

Tries to import the given plug-in.

**Args:**

- `package_name`:  Name of package containing plug-ins.
- `plugin_name`:   Name of the plug-in (module).

**Returns:**

True if plug-in exists, False otherwise.


### **get**()

Full name: `midgard.dev.plugins.get`

Signature: `(package_name: str, plugin_name: str, part: Union[str, NoneType] = None, prefix: Union[str, NoneType] = None) -> midgard.dev.plugins.Plugin`

Get a specific plugin-object

If the plug-in is not part of the package an UnknownPluginError is raised.

If there are several functions registered in a plug-in and `part` is not
specified, then the first function registered in the plug-in will be
called.

**Args:**

- `package_name`:  Name of package containing plug-ins.
- `plugin_name`:   Name of the plug-in, i.e. the module containing the plug-in.
- `part`:          Name of function to call within the plug-in (optional).
- `prefix`:        Prefix of the plug-in name, used if the plug-in name is not found (optional).

**Returns:**

Plugin-namedtuple representing the plug-in.


### **load**()

Full name: `midgard.dev.plugins.load`

Signature: `(package_name: str, plugin_name: str, prefix: Union[str, NoneType] = None) -> str`

Load one plug-in from a package

First tries to load the plugin with the given name. If that fails, it tries
to load {prefix}_{plugin_name} instead.

**Args:**

- `package_name`:  Name of package containing plug-ins.
- `plugin_name`:   Name of the plug-in (module).
- `prefix`:        Prefix of the plug-in name, used if the plug-in name is unknown (optional).

**Returns:**

Actual name of plug-in (with or without prefix).



### **names**()

Full name: `midgard.dev.plugins.names`

Signature: `(package_name: str, plugins: Union[Iterable[str], NoneType] = None, prefix: Union[str, NoneType] = None) -> List[str]`

List plug-ins in a package

If `plugins` is given, it should be a list of names of plug-ins.  If a
plug-in listed in the `plugins`-list does not exist, an UnknownPluginError
is raised.

If `plugins` is not given, all available plugins will be listed. Do note,
however, that this will import all python files in the package.

**Args:**

- `package_name`:  Name of package containing plug-ins.
- `plugins`:       List of plug-ins that should be used (optional).
- `prefix`:        Prefix of the plug-in names, used if any of the plug-in names are unknown (optional).

**Returns:**

List of strings with names of plug-ins.


### **parts**()

Full name: `midgard.dev.plugins.parts`

Signature: `(package_name: str, plugin_name: str, prefix: Union[str, NoneType] = None) -> List[str]`

List all parts of one plug-in

**Args:**

- `package_name`:  Name of package containing plug-ins.
- `plugin_name`:   Name of the plug-in.
- `prefix`:        Prefix of the plug-in name, used if the plug-in name is unknown (optional).

**Returns:**

- `List`: Strings with names of parts.


### **register**()

Full name: `midgard.dev.plugins.register`

Signature: `(func: Callable, name: Union[str, NoneType] = None, sort_value: int = 0) -> Callable`

Decorator used to register a plug-in

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

**Args:**

- `func`:        The function that is being registered.
- `name`:        Alternative name of plug-in. Used by `register_named`.
- `sort_value`:  The value used when sorting plug-ins. Used by `register_ordered`.

**Returns:**

The function that is being registered.


### **register_named**()

Full name: `midgard.dev.plugins.register_named`

Signature: `(name: str) -> Callable`

Decorator used to register a named plug-in

This allows for overriding the name used to register the plug-in. See
`register` for more details.

**Args:**

- `name`:   Name used for plug-in instead of module name.

**Returns:**

Decorator that registers a named function.


### **register_ordered**()

Full name: `midgard.dev.plugins.register_ordered`

Signature: `(sort_value: int) -> Callable`

Decorator used to register a plug-in with a specific sort order

The sort value should be a number. Lower numbers are sorted first, higher
numbers last. Plug-ins without an explicit sort_order gets the sort value
of 0.

**Args:**

- `sort_value`:   The value used when sorting plug-ins.

**Returns:**

Decorator that registers an ordered function.


### **signature**()

Full name: `midgard.dev.plugins.signature`

Signature: `(package_name: str, plugin_name: str, part: Union[str, NoneType] = None, prefix: Union[str, NoneType] = None) -> inspect.Signature`

Get signature of a plug-in

If the plug-in is not part of the package an UnknownPluginError is raised.

If there are several functions registered in a plug-in and `part` is not
specified, then the first function registered in the plug-in will be
documented.

**Args:**

- `package_name`:     Name of package containing plug-ins.
- `plugin_name`:      Name of the plug-in, i.e. the module containing the plug-in.
- `part`:             Name of function to call within the plug-in (optional).
- `prefix`:           Prefix of the plug-in name, used if the plug-in name is unknown (optional).

**Returns:**

Signature of the plugin


## midgard.dev.profiler
Add a profiler when running

Supports several profilers including cprofile, line_profiler, memprof and memory_profiler.



### **CProfile**

Full name: `midgard.dev.profiler.CProfile`

Signature: `()`

cprofile is used for profiling the whole program

### **LineProfiler**

Full name: `midgard.dev.profiler.LineProfiler`

Signature: `()`

line_profiler is used to profile one or a few functions in detail

### **Profiler**

Full name: `midgard.dev.profiler.Profiler`

Signature: `()`

Base class for profilers

## midgard.dev.timer
Class for timing the running time of functions and code blocks

**Description:**

The `dev.timer` can be used to log the running time of functions and general
code blocks. Typically, you will import the `Timer`-class from within the
module:

    from midgard.dev.timer import Timer

The Timer can then be used in three different ways:

1. As a decorator to time one function:

        @Timer('The time to execute some_function was')
        def some_function(some_argument, some_other_argument=some_value):
            pass

2. As a context manager together with `with` to time a code block:

        with Timer('Finish doing stuff in', logger=logger.debug) as t:
            do_something()
            do_something_else()

3. With explicit `start`- and `end`-statements:

        t = Timer()
        t.start()
        do_something()
        do_something_else()
        t.end()

As can be seen in the examples above, `Timer()` may be called with several
optional parameters, including the text to report when the timer ends and which
logger is used to report the timing. See `Timer.__init__` for more details.


### **AccumulatedTimer**

Full name: `midgard.dev.timer.AccumulatedTimer`

Signature: `(text: str = 'Elapsed time:', fmt: str = '.4f', logger: Union[Callable[[str], NoneType], NoneType] = functools.partial(<function log at 0x7fa9957b3dc0>, level='info')) -> None`



### **Timer**

Full name: `midgard.dev.timer.Timer`

Signature: `(text: str = 'Elapsed time:', fmt: str = '.4f', logger: Union[Callable[[str], NoneType], NoneType] = functools.partial(<function log at 0x7fa9957b3dc0>, level='info')) -> None`

Class for timing running time of functions and code blocks.


## midgard.dev.util
Midgard library module with utility functions for easier script development

Example:
from midgard.dev import util
directory, date = util.parse_args('string', 'date')

Description:

This module provides the boilerplate code necessary for starting a script. In particular handling of command line 
arguments and default options including --help are done.



### COMMAND (str)
`COMMAND = 'generate_api '`


### **check_help_and_version**()

Full name: `midgard.dev.util.check_help_and_version`

Signature: `(module: str, doc_module: str = None, replace_vars: Dict[str, str] = {}) -> None`

Show help or version if asked for

Show the help message parsed from the script's docstring if -h or --help option is given. Show the script's version
if --version is given.

**Args:**

- `module`:       Module name.
- `doc_module`:   Module containing help text.
- `replace_vars`: Dictionary with variable for replacement in docstring


### **check_options**()

Full name: `midgard.dev.util.check_options`

Signature: `(*options: Tuple[str]) -> str`

Check if any of a list of options is specified on the command line

Returns the actual option that is specified. The first option specified on the command line is returned if there
are several matches. Returns the empty string if no option is specified. This means that this method works fine
also in a boolean context, for example

    if check_options('-F', '--force'):
        do_something()

**Args:**

- `options`:   Strings specifying which options to check for, including '-'-prefix.

**Returns:**

- `String`: Option that is specified, blank string if no option is specified



### **get_callers**()

Full name: `midgard.dev.util.get_callers`

Signature: `() -> str`

Get a list of methods calling this function

**Returns:**

Lists all methods calling the function


### **get_pid_and_server**()

Full name: `midgard.dev.util.get_pid_and_server`

Signature: `() -> str`

Find process id and name of server the analysis is running on

Use the platform.uname to find servername instead of os.uname because the latter is not supported on Windows.

**Returns:**

Process id and name of server


### **get_program_info**()

Full name: `midgard.dev.util.get_program_info`

Signature: `(module: str) -> str`

Get the name and the version of the running program

**Args:**

- `module`: Module name.

**Returns:**

Program name and version


### **get_program_name**()

Full name: `midgard.dev.util.get_program_name`

Signature: `() -> str`

Get the name of the running program

**Returns:**

String trying to be similar to how the user called the program.


### **get_python_version**()

Full name: `midgard.dev.util.get_python_version`

Signature: `() -> str`

Find python version used

**Returns:**

Name of executable and version number


### **no_traceback**()

Full name: `midgard.dev.util.no_traceback`

Signature: `(func)`

Decorator for turning off traceback, instead printing a simple error message

Use the option --show_tb to show the traceback anyway.


### **not_implemented**()

Full name: `midgard.dev.util.not_implemented`

Signature: `() -> None`

A placeholder for functions that are not implemented yet

A note about the missing implementation is written to the log.


### **options2args**()

Full name: `midgard.dev.util.options2args`

Signature: `(options: List[str]) -> Union[List[str], Dict[str, str]]`

Convert a list of command line options to a args and kwargs 

The options should be specified as a string with the necessary - or -- in front and options with a value should
by separated by = (e.g. --station=stas).

**Args:**

- `options`: List with options

**Returns:**

Tuple with non-keyword arguments and with keyword arguments



### **parse_args**()

Full name: `midgard.dev.util.parse_args`

Signature: `(*param_types: Tuple[str], doc_module: str = None) -> Union[Any, List[Any]]`

Parse command line arguments and general options

Parse arguments from the given parameter types.

**Args:**

- `param_types`: Strings describing the expected parameter types. Each string must be one of the keys in #_PARSERS.
- `doc_module`:  Module containing help text.

**Returns:**

List of command line arguments parsed according to param_types.


### **read_option_value**()

Full name: `midgard.dev.util.read_option_value`

Signature: `(option: str, default: str = '') -> str`

Read the value of one command line option

The option should be specified as a string with the necessary - or -- in front. If that option is not one of the
command line arguments, default is returned. If there is a value following the option that value is returned as a
string (separated by =). If there are several occurences of the option, the first one is returned.

**Args:**

- `option`:    Option specified with the leading - or --.
- `default`:   Optional default value that is returned if the option is not specified.

**Returns:**

The option or the value of the option. The default value if the option is not specified.


### **write_requirements**()

Full name: `midgard.dev.util.write_requirements`

Signature: `(file_path: Union[str, pathlib.Path]) -> None`

Write requirements (python modules) to file for reproducibility.

Note that this only stores the modules that have been imported, and that have a `__version__`-attribute (see PEP
396 - https://www.python.org/dev/peps/pep-0396/)

**Args:**

- `file_path`: File path.
