"""Midgard library module for logging

Description:
------------

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


Example:
--------

    >>> from midgard.dev import log
    >>> log.init("info", prefix="My prefix")
    >>> n, m = 5, 3
    >>> log.info(f"Calculating the inverse of a {n:>2d}x{m:<2d} matrix")
    INFO  [My prefix] Calculating the inverse of a  5x3  matrix

"""
# Standard library imports
import abc
from datetime import datetime
import functools
import pathlib
import sys
from typing import Callable, Optional, Union

# Midgard imports
from midgard.collections import enums

# LogLevel type
LogLevel = enums.get_enum("log_level")

# Overview over active loggers
_ACTIVE_LOGGERS = dict()


#
# Loggers
#
class Logger(abc.ABC):
    """Abstract class that can be specialized to create new loggers"""

    name = "logger"
    log_levels = enums.get_enum("log_level")

    def __init__(self, log_level: Optional[str] = None, prefix: str = ""):
        """Register as an active logger, and set up parameters"""
        _ACTIVE_LOGGERS[self.name] = self

        # Use "warn" as default log level, None used as default parameter to allow for other default behaviours
        log_level = "warn" if log_level is None else log_level

        # Check and set log_level and prefix
        self.log_level = log_level
        self.prefix = prefix

    @property
    def log_level(self) -> LogLevel:
        """Log level as an enum"""
        return self._log_level

    @log_level.setter
    def log_level(self, value: str) -> None:
        """Set log level using string, checks that log level is a valid level"""
        self._log_level = enums.get_value("log_level", value)

    @property
    def prefix(self) -> str:
        """Prefix before log text"""
        return self._prefix

    @prefix.setter
    def prefix(self, value: str) -> None:
        """Set prefix"""
        self._prefix = f"[{value}] " if value else ""

    @classmethod
    def is_level(cls, level: str) -> bool:
        """Checks that level is a valid log level"""
        return enums.has_value("log_level", level)

    @classmethod
    def get_color(cls, level: LogLevel) -> str:
        """Get color string for the given log level"""
        return enums.get_value("log_color", level.name, default="")

    @abc.abstractmethod
    def blank(self) -> None:
        """Log blank line"""

    @abc.abstractmethod
    def log(self, level: LogLevel, log_text: str) -> None:
        """Log text at given level"""

    def __repr__(self):
        """Representation of logger"""
        return f"{type(self).__name__}({self.name!r}, log_level={self.log_level.name!r})"


class ConsoleLogger(Logger):
    """Log to the console, the log level can also be set using command line parameters"""

    name = "console"

    def __init__(self, log_level: Optional[str] = None, prefix: str = "", use_command_line: bool = True) -> None:
        """Create console logger and register as an active logger
    
        Args:
            log_level:         Define level from which logging should be started.
            prefix:            Add prefix to logging messages.
            use_command_line:  Use command line for defining log level via option --<level>, whereby <level> is
                               a placeholder for the existing logging levels 'debug', 'info', 'warn', 'error' and
                               'fatal'. 
        """

        # Use command line parameters if log level is given as `--level`
        if use_command_line:
            for arg in [o for o in sys.argv[1:] if o.startswith("--")]:
                if self.is_level(arg[2:]):
                    log_level = arg[2:]
                    break

        # Register as normal
        super().__init__(log_level=log_level, prefix=prefix)

    def blank(self) -> None:
        """Log blank line"""
        if self.log_level < self.log_levels.none:
            print()

    def log(self, level: LogLevel, log_text: str) -> None:
        """Log text at given level"""
        if level < self.log_level:
            return

        color = self.get_color(level)
        stream = sys.stderr if level >= self.log_levels.warn else sys.stdout
        print(f"{color}{level.name.upper():<6}{self.prefix}{log_text}", file=stream)


class FileLogger(Logger):
    """Log to a file, the log files can be rotated so that older files are kept

        Args:
            file_path:      File path.
            log_level:      Define level from which logging should be started.
            prefix:         Add prefix to logging messages.
            rotation:       Logging files are rolled based on given number of rotations. That means, if there are old 
                            log files, they will be moved to files with extension .0, .1 and so on. If the argument
                            is not specified, then existing logging file is overwritten from newer ones.            
    """

    def __init__(
        self,
        file_path: Union[str, pathlib.Path],
        log_level: Optional[str] = None,
        prefix: str = "",
        rotation: Optional[int] = None,
    ) -> None:
        """Create file logger and register as an active logger"""

        # Store file path and generate name
        self.file_path = pathlib.Path(file_path).resolve()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.name = f"file://{self.file_path}"

        # Rotate old log files and open log file for writing
        if rotation is not None:
            self.rotate_files(rotation)
        self.fid = open(file_path, mode="wt")

        # Register as an active logger
        super().__init__(log_level=log_level, prefix=prefix)

    def __del__(self):
        """Close log file when logger is deleted"""
        try:
            self.fid.close()
        except AttributeError:
            pass  # self.fid not defined, nothing to close

    def blank(self) -> None:
        """Log blank line"""
        if self.log_level < self.log_levels.none:
            self.fid.write("\n")

    def log(self, level: LogLevel, log_text: str) -> None:
        """Log text at given level"""
        if level < self.log_level:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.fid.write(f"{level.name.upper():<6} {timestamp} {self.prefix}{log_text}\n")

    def rotate_files(self, rotation: int) -> None:
        """Perform necessary rolling of log files

        Rolls the log files. That is, if there are old log files, they will be
        moved to files with extension .0, .1 and so on. The number of rolled
        logs to keep is specified by the rotation parameter.

        Args:
            rotation:  Number of log files to keep.
        """
        if not self.file_path.exists():
            return

        directory = self.file_path.parent
        log_name = self.file_path.name

        for roll in range(rotation - 1)[::-1]:
            if (directory / f"{log_name}.{roll}").exists():
                (directory / f"{log_name}.{roll}").replace(directory / f"{log_name}.{roll + 1}")
        if rotation > 0:
            self.file_path.replace(directory / f"{log_name}.0")


#
# Module functions used for logging
#


def log(log_text: str, level: str) -> None:
    """Log text at the given level"""
    if not _ACTIVE_LOGGERS:
        return

    # Looking up the level dynamically, as the enum may have been updated
    level = enums.get_value("log_level", level)
    for output in _ACTIVE_LOGGERS.values():
        output.log(level, log_text)


def blank() -> None:
    """Log blank line"""
    for output in _ACTIVE_LOGGERS.values():
        output.blank()


# Aliases for initializing loggers
init = ConsoleLogger
file_init = FileLogger


# Make each log level available as a function
for level in enums.get_enum("log_level"):
    globals()[level.name] = functools.partial(log, level=level.name)


#
# Convenience functions related to logging
#
def print_file(
    log_path: Union[str, pathlib.Path], log_level: str = "info", print_func: Callable[[str], None] = print
) -> None:
    """Print a log file with colors, stripping away any item below log_level"""
    log_level = enums.get_value("log_level", log_level)
    log_path = pathlib.Path(log_path)

    current_level = log_level
    with log_path.open(mode="r") as fid:  # lib.files is not available in lib.log
        for line in fid:
            line_level = line.partition(" ")[0].lower()
            current_level = enums.get_value("log_level", line_level, default=current_level)
            if current_level >= log_level:
                color = Logger.get_color(current_level)
                print_func(f"{color}| {line.rstrip()}")
