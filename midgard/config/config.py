"""Midgard library module for handling of configuration settings

Description:
------------

A Configuration consists of one or several sections. Each ConfigurationSection
consists of one or more entries. Each ConfigurationEntry consists of a key and
a value.


Examples:
---------

For basic use, an entry is looked up by simple attribute access. For instance
if `cfg` is a Configuration with the section `midgard` which has an entry `foo
= bar`:

    >>> cfg = Configuration("config_name")
    >>> cfg.update("midgard", "foo", "bar")
    >>> cfg.midgard.foo
    ConfigurationEntry(key='foo', value='bar')

ConfigurationEntry has several access methods that convert the entry to a given
data type:

    >>> cfg.update("midgard", "foo_pi", 3.14, source="command line")
    >>> cfg.midgard.foo_pi
    ConfigurationEntry(key='foo_pi', value='3.14')
    >>> cfg.midgard.foo_pi.float
    3.14
    >>> cfg.midgard.foo_pi.str
    '3.14'
    >>> cfg.midgard.foo_pi.tuple
    ('3.14',)


Sources:
--------

Each configuration entry records its source. That is, where that entry was
defined. Examples include read from file, set as a command line option, or
programmatically from a dictionary. The source can be looked up on an
individual entry, or for all entries in a configuration.

    >>> cfg.midgard.foo_pi.source
    'command line'
    >>> cfg.sources  # doctest: +SKIP
    {'/home/midgard/midgard.conf', 'command line'}


Profiles:
---------


Fallback Configuration:
---------------------


Master Section:
---------------


Replacement Variables:
----------------------


Help text and Type hints:
-------------------------

"""

# Standard library imports
import builtins
from configparser import ConfigParser, BasicInterpolation, ExtendedInterpolation
from contextlib import contextmanager
import datetime as stdlib_datetime
import os.path
import pathlib
import re
import sys
from collections import UserDict

# Midgard imports
from midgard.dev import console
from midgard.collections import enums
from midgard.dev import exceptions


# Typing
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, Union

ProfileName = Optional[str]
Sections = Dict[str, "ConfigurationSection"]
EntryName = str
ConfigVars = Dict[str, str]


# Date and datetime formats
FMT_date = "%Y-%m-%d"
FMT_datetime = "%Y-%m-%d %H:%M:%S"
FMT_dt_file = "%Y%m%d-%H%M%S"


class CasedConfigParser(ConfigParser):
    """ConfigParser with case-sensitive keys"""

    def optionxform(self, optionstr: str) -> str:
        """Do not turn optionstr (key) into lowercase"""
        return optionstr


class Configuration:
    """Represents a Configuration"""

    def __init__(self, name: str) -> None:
        """Initialize a Configuration

        The name is used purely for representation and error messages.

        Args:
            name:  Name of configuration.
        """
        self.name = name
        self.fallback_config = None
        self.master_section = None

        self._profiles: List[ProfileName] = [None]
        self._profile_sections: Dict[ProfileName, Sections] = dict()
        self._sections: Sections = dict()
        self._vars_dict: ConfigVars = dict()
        self._update_count: int = 0

    @classmethod
    def read_from_file(cls, cfg_name: str, *file_paths: Union[str, pathlib.Path]) -> "Configuration":
        """Read a configuration from one or more files

        Args:
            cfg_name:    Name of configuration.
            file_paths:  File(s) that will be read.

        Returns:
            A Configuration representing the file(s).
        """
        cfg = cls(cfg_name)
        for file_path in file_paths[::-1]:
            cfg.update_from_file(file_path)

        return cfg

    @classmethod
    @contextmanager
    def update_on_file(cls, file_path: Union[str, pathlib.Path], **as_str_args: Any) -> Generator:
        """Context manager for updating a configuration on file
        """
        # Read config from file
        cfg = cls.read_from_file("Temporary", file_path)
        update_count_before = cfg._update_count

        # Yield config so it can be updated
        yield cfg

        # Write config if it has been updated
        if cfg._update_count > update_count_before:
            cfg.write_to_file(file_path, **as_str_args)

    def write_to_file(self, file_path: Union[str, pathlib.Path], **as_str_args: Any) -> None:
        """Write the configuration to a file

        In addition to the file path, arguments can be specified and will be passed on to the as_str() function. See
        `as_str()` for more information.

        Todo: Use files.open_path
        """
        file_path = pathlib.Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, mode="w") as fid:
            fid.write(self.as_str(**as_str_args) + "\n")

    @property
    def section_names(self) -> List[str]:
        """Names of sections in Configuration"""
        return list(self._sections.keys())

    @property
    def sections(self) -> List["ConfigurationSection"]:
        """Sections in Configuration"""
        return list(self._sections.values())

    @property
    def sources(self) -> Set[str]:
        """Sources of entries in Configuration"""
        return {s[k].source for s in self.sections for k in s.keys() if s[k].source}

    @property
    def profiles(self) -> List[ProfileName]:
        """List of profiles currently being used in Configuration"""
        return self._profiles

    @profiles.setter
    def profiles(self, values: Union[None, List[ProfileName]]) -> None:
        """Set profiles that will be used in Configuration

        The list of profiles should be a prioritized list where the first profile listed will be used if available.
        None is used to indicate default values (no profile), and will be automatically appended at the end of the list
        of profiles.

        To not use any profiles, set `cfg.profiles = None`.

        Args:
            values:  List of profiles to use.
        """
        if values is None:
            values = [None]
        elif values[-1] is not None:
            values.append(None)

        self._profiles = values
        self._set_sections_for_profiles()

    def _set_sections_for_profiles(self) -> None:
        """Update sections according to profiles"""
        self._sections.clear()

        # Add values in reverse order so that the first profile is prioritized
        for profile in self.profiles[::-1]:
            for section_name, profile_section in self._profile_sections.get(profile, dict()).items():
                self._sections.setdefault(section_name, ConfigurationSection(section_name))
                for key, entry in profile_section.items():
                    self._sections[section_name][key] = entry

    @property
    def fallback_config(self) -> "Configuration":
        """The fallback configuration"""
        if self._fallback_config is None:
            raise exceptions.MissingConfigurationError(
                f"Configuration '{self.name}' has not defined a fallback configuration"
            )
        return self._fallback_config

    @fallback_config.setter
    def fallback_config(self, cfg: Optional["Configuration"]) -> None:
        """Set the fallback configuration"""
        self._fallback_config = cfg

    @property
    def master_section(self) -> "ConfigurationSection":
        """The master section"""
        if self._master_section is None:
            raise exceptions.MissingSectionError(f"Configuration {self.name!r} has not defined a master section")
        if self._master_section not in self._sections:
            raise exceptions.MissingSectionError(
                f"Master section {self._master_section!r} does not exist in configuration {self.name!r}"
            )

        return self._sections[self._master_section]

    @master_section.setter
    def master_section(self, section: Optional[str]) -> None:
        """Set the master section"""
        self._master_section = section

    def get(
        self, key: str, value: Optional[str] = None, section: Optional[str] = None, default: Optional[str] = None
    ) -> "ConfigurationEntry":
        """Get an entry from a configuration with possibility for override and default value

        A value for an entry is found using the following priorities:

            1. An explicit value given in `value`. None is used as a marker for no value.
            2. Looked up in the current configuration.
            3. Looked up in any fallback configurations that are defined.
            4. The default value is used.

        If `value` is not None, that value is simply returned as a `ConfigurationEntry`. If `default` is not given (is
        None), and a value is not found in any other way, a MissingEntryError is raised.

        Args:
            key:      Name of option (key in the configuration entry).
            value:    Value of entry. Used for overriding the configuration.
            section:  Section in the configuration in which to look up the key.
            default:  Default value that is returned if value is not found any other way.

        Returns:
            Entry representing the value.
        """
        if value is not None:
            return ConfigurationEntry(key, value=value, source="method call", vars_dict=self.vars)

        try:
            section_value = self.master_section if section is None else self[section]
            if isinstance(section_value, ConfigurationEntry):
                return section_value
            else:
                return section_value[key]
        except (exceptions.MissingSectionError, exceptions.MissingEntryError) as err:
            try:
                return self.fallback_config.get(key=key, section=section)
            except (exceptions.MissingConfigurationError, exceptions.MissingEntryError):
                if default is None:
                    # Raise original error
                    raise err
                else:
                    return ConfigurationEntry(key, value=default, source="default value", vars_dict=self.vars)

    def exists(self, key: str, section: Optional[str] = None) -> bool:
        """Check if a configuration entry exists

        Args:
            key:      Name of option (key in the configuration entry).
            section:  Section in the configuration in which to look up the key.

        Returns:
            True if the configuration entry exists, otherwise False.
        """
        if section is None:
            return self.master_section.exists(key)

        try:
            cfg_section = self[section]
        except (exceptions.MissingSectionError, exceptions.MissingEntryError):
            return False

        if isinstance(cfg_section, ConfigurationEntry):
            return False
        else:
            return cfg_section.exists(key)

    def update(
        self,
        section: str,
        key: str,
        value: str,
        *,
        profile: ProfileName = None,
        source: str = "unknown",
        meta: Optional[Dict[str, str]] = None,
        allow_new: bool = True,
        _update_sections: bool = True,
    ) -> None:
        """Update a configuration section with a configuration entry

        If `allow_new` is False, the configuration entry must already exist. If it is True the update is allowed to
        create a new section and a new entry is necessary.

        The `_update_sections` flag can be used to not update the sections of the configuration, only the
        profiles. This should typically not be done, but is used by some of the other update methods which update the
        sections themselves.

        Args:
            section:    Section to update.
            key:        Key of entry.
            value:      Value of entry.
            profile:    Profile to update.
            source:     Source of the update.
            meta:       Metadata like help text and type hints for the entry.
            allow_new:  Whether to allow the creation of a new section and entry.
        """
        if not allow_new:
            profile_str = "" if profile is None else f"(profile: '{profile}')"
            if section not in self._sections:
                raise exceptions.MissingSectionError(
                    f"Configuration '{self.name}' does not contain section '{section}' {profile_str}"
                )
            if key not in self._sections[section]:
                raise exceptions.MissingEntryError(
                    f"Section '{section}' of configuration '{self.name}' does not contain entry '{key}' {profile_str}"
                )

        # Add entry to profile
        source = source if profile is None else f"{source} ({profile})"
        profile_sections = self._profile_sections.setdefault(profile, dict())
        profile_sections.setdefault(section, ConfigurationSection(section))

        # Record that configuration has been updated
        if key not in profile_sections[section] or profile_sections[section][key]._value != value:
            self._update_count += 1

        profile_sections[section][key] = ConfigurationEntry(
            key, value=value, source=source, meta=meta, vars_dict=self.vars
        )

        # Update sections
        if _update_sections:
            self._set_sections_for_profiles()

    def update_from_file(
        self,
        file_path: Union[str, pathlib.Path],
        allow_new: bool = True,
        interpolate: bool = False,
        case_sensitive: bool = False,
    ) -> None:
        """Update the configuration from a configuration file

        The Python ConfigParser is used to read the file. The file format that is supported is described at
        https://docs.python.org/library/configparser.html

        Different profiles in a configuration file are denoted by double underscores in the sections names. For
        instance will the following configuration have a `foo` profile in the `spam` section (in addition to the
        default profile):

            [spam]
            ...

            [spam__foo]
            ...

        The file may contain a special section called `__replace__` which may contain key-value pairs which will
        replace format-style strings in keys and values in the rest of the file.

        Additionally, the file may contain a special section called `__vars__`. The key-value pairs from this section
        will be added to the `dictionary` of the configuration.

        If `interpolate` is set to True, ExtendedInterpolation of variables in the configuration file is used. This
        means that variables of the form ${key:section} can be used for references within the file. See
        https://docs.python.org/library/configparser.html#configparser.ExtendedInterpolation for details.

        Args:
            file_path:      Path to the configuration file.
            allow_new:      Whether to allow the creation of new sections and entries.
            interpolate:    Whether to interpolate variables in the configuration file.
            case_sensitive: Whether to read keys as case sensitive (or convert to lower case).
        """
        # Use ConfigParser to read from file
        cfg_parser_cls = CasedConfigParser if case_sensitive else ConfigParser
        cfg_parser = cfg_parser_cls(
            allow_no_value=True,
            delimiters=("=",),
            interpolation=ExtendedInterpolation() if interpolate else BasicInterpolation(),
        )
        cfg_parser.read(file_path)

        # Read special __replace__
        replace_vars = {k: v for k, v in cfg_parser["__replace__"].items()} if "__replace__" in cfg_parser else {}

        # Add __vars__ to vars dictionary
        if "__vars__" in cfg_parser.sections():
            self.update_vars({k: v for k, v in cfg_parser["__vars__"].items()})

        # Add configuration entries
        for cfg_section in cfg_parser.sections():
            section, has_profile, profile = cfg_section.partition("__")
            if not section:  # Skip dunder sections
                continue
            for key, value in cfg_parser[cfg_section].items():
                # Handle meta-information
                if ":" in key:
                    continue
                meta = {k.partition(":")[-1]: v for k, v in cfg_parser[cfg_section].items() if k.startswith(f"{key}:")}

                # Create a configuration entry
                self.update(
                    section,
                    _replace(key, replace_vars),
                    value if value is None else _replace(value, replace_vars).replace("\n", " "),
                    profile=profile if has_profile else None,
                    source=str(file_path),
                    meta=meta,
                    allow_new=allow_new,
                    _update_sections=False,
                )

        self._set_sections_for_profiles()

    def update_from_config_section(
        self, other_section: "ConfigurationSection", section: Optional[str] = None, allow_new: bool = True
    ) -> None:
        section = other_section.name if section is None else section
        for key, entry in other_section.data.items():
            self.update(
                section,
                key,
                entry.str,
                source=entry.source,
                meta=entry.meta,
                allow_new=allow_new,
                _update_sections=False,
            )

        self._set_sections_for_profiles()

    def update_from_options(
        self,
        options: Optional[List[str]] = None,
        profile: ProfileName = None,
        source: str = "command line",
        allow_new: bool = False,
    ) -> None:
        if options is None:
            options = sys.argv[1:]

        updated_options = set()
        for option in options:
            if not (option.startswith("--") and "=" in option):
                continue

            # Parse config name, section, key and value of the form name:section:key=value
            opt_key, _, opt_value = option[2:].partition("=")
            opt_section, _, opt_key = opt_key.rpartition(":")
            opt_name, _, opt_section = opt_section.rpartition(":")

            # Update current configuration
            if opt_name and opt_name != self.name:
                continue
            if not opt_section:
                opt_section = self.master_section.name
            try:
                self.update(
                    opt_section,
                    opt_key,
                    opt_value,
                    profile=profile,
                    source=f"{source} ({option})",
                    allow_new=allow_new,
                    _update_sections=False,
                )
                updated_options.add(option)
            except exceptions.MissingEntryError:
                pass

        self._set_sections_for_profiles()
        return list(set(options) - updated_options)

    def update_from_dict(
        self,
        cfg_dict: Dict[str, Any],
        section: Optional[str] = None,
        source: str = "dictionary",
        allow_new: bool = True,
    ) -> None:
        section = self.master_section.name if section is None else section
        for key, value in cfg_dict.items():
            self.update(section, key, value, source=source, allow_new=allow_new, _update_sections=False)

        self._set_sections_for_profiles()

    def clear(self) -> None:
        """Clear the configuration"""
        self._sections.clear()
        self.clear_vars()

    @property
    def vars(self) -> ConfigVars:
        """The configuration variables"""
        return self._vars_dict

    def clear_vars(self) -> None:
        """Clear the configuration variables"""
        self._vars_dict.clear()

    def update_vars(self, new_vars: ConfigVars) -> None:
        """Update the configuration variables"""
        self._vars_dict.update(new_vars)

    def as_str(
        self, width: Optional[int] = None, key_width: int = 30, only_used: bool = False, metadata: bool = True
    ) -> str:
        """The configuration represented as a string

        This is simililar to what is shown by `str(configuration)` (and implemented by `__str__`), but has more
        flexibility.

        Args:
            width:      Width of text for wrapping. Default is width of console.
            key_width:  Width of the key column. Default is 30 characters.
            only_used:  Only include configuration entries that has been used so far.
            metadata:   Include metadata like type and help text.

        Returns:
            String representation of the configuration.
        """
        sections = self._sections.values()
        section_strs = [
            s.as_str(width=width, key_width=key_width, only_used=only_used, metadata=metadata) for s in sections
        ]

        return "\n\n\n".join(s for s in section_strs if s)

    def as_dict(
        self, getters: Optional[Dict[str, Dict[str, str]]] = None, default_getter: str = "str"
    ) -> Dict[str, Dict[str, Any]]:
        """The configuration represented as a dictionary

        Args:
            getters:         How to get the value of each entry in each section.
            default_getter:  How to get the value of entries not specified in getters.

        Returns:
            Representation of the configuration as a nested dictionary.
        """
        getters = dict() if getters is None else getters
        return {k: v.as_dict(getters=getters.get(k), default_getter=default_getter) for k, v in self._sections.items()}

    def __getitem__(self, key: str) -> Union["ConfigurationSection", "ConfigurationEntry"]:
        """Get a section or entry from the master section from the configuration"""
        if key in self.section_names:
            return self._sections[key]

        try:
            return self.master_section[key]
        except exceptions.MissingSectionError:
            try:
                return self.fallback_config[key]
            except exceptions.MidgardException:
                raise exceptions.MissingSectionError(f"Configuration {self.name!r} has no section {key!r}") from None

    def __getattr__(self, key: str) -> Union["ConfigurationSection", "ConfigurationEntry"]:
        """Get a section or entry from the master section from the configuration"""
        return self[key]

    def __delitem__(self, key: str) -> None:
        """Delete a section from the configuration"""
        del self._sections[key]

    def __delattr__(self, key: str) -> None:
        """Delete a section from the configuration"""
        del self._sections[key]

    def __dir__(self) -> List[str]:
        """List attributes and sections in the configuration"""
        try:
            return list(super().__dir__()) + self.section_names + self.master_section.as_list()
        except exceptions.MissingSectionError:
            return list(super().__dir__()) + self.section_names

    def __str__(self) -> str:
        """The configuration represented as a string

        This string can be stored in a file and read back with `update_from_file`.
        """
        return "\n\n".join(str(s) for s in self._sections.values())

    def __repr__(self) -> str:
        """A simple string representation of the configuration"""
        return f"{self.__class__.__name__}(name='{self.name}')"


class ConfigurationSection(UserDict):

    data: Dict[str, "ConfigurationEntry"]

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name

    def as_str(
        self, width: Optional[int] = None, key_width: int = 30, only_used: bool = False, metadata: bool = True
    ) -> str:
        """The configuration section represented as a string

        This is simililar to what is shown by `str(section)` (and implemented by `__str__`), but has more flexibility.

        Args:
            width:      Width of text for wrapping. Default is width of console.
            key_width:  Width of the key column. Default is 30 characters.
            only_used:  Only include configuration entries that has been used so far.
            metadata:   Include metadata like type and help text.

        Returns:
            String representation of the configuration section.
        """
        lines = list()
        for entry in self.data.values():
            if only_used and not entry.is_used:
                continue
            lines.append(entry.entry_as_str(width=width, key_width=key_width, metadata=metadata))

        if lines:
            return f"[{self.name}]\n" + "\n".join(lines)
        else:
            return ""

    def as_list(self) -> List[str]:
        """List of keys of entries in configuration section

        Returns:
            List of keys of entries in configuration section.
        """
        return list(self.data.keys())

    def as_dict(self, getters: Dict[str, str] = None, default_getter: str = "str") -> Dict[str, Any]:
        """The configuration section represented as a dictionary

        Args:
            getters:         How to get the value of each entry in the section.
            default_getter:  How to get the value of entries not specified in getters.

        Returns:
            Representation of the configuration section as a dictionary.
        """
        getters = dict() if getters is None else getters
        getters = {k: getters.get(k, default_getter) for k in self.keys()}
        return {k: getattr(e, getters[k]) for k, e in self.items()}

    def exists(self, key: str) -> bool:
        """Check if key exists in section

        Args:
            key:  Name of configuration key.

        Returns:
            True if key is in section, False otherwise.
        """
        return key in self.data

    def __getitem__(self, key: str) -> "ConfigurationEntry":
        """Get an entry from the configuration section"""
        try:
            return self.data[key]
        except KeyError:
            raise exceptions.MissingEntryError(f"Configuration section '{self.name}' has no entry '{key}'") from None

    def __getattr__(self, key: str) -> "ConfigurationEntry":
        """Get an entry from the configuration section"""
        try:
            return self.data[key]
        except KeyError:
            raise exceptions.MissingEntryError(f"Configuration section '{self.name}' has no entry '{key}'") from None

    def __dir__(self) -> List[str]:
        """List attributes and entries in the configuration section"""
        return list(super().__dir__()) + self.as_list()

    def __str__(self) -> str:
        """The configuration section represented as a string"""
        return f"[{self.name}]\n" + "\n".join(str(v) for v in self.data.values())

    def __repr__(self) -> str:
        """A simple string representation of the configuration section"""
        return f"{self.__class__.__name__}(name='{self.name}')"


class ConfigurationEntry:

    _BOOLEAN_STATES = {
        "0": False,
        "1": True,
        "false": False,
        "true": True,
        "no": False,
        "yes": True,
        "off": False,
        "on": True,
    }

    def __init__(
        self,
        key: str,
        value: Any,
        *,
        source: builtins.str = "",
        meta: Optional[Dict[str, str]] = None,
        vars_dict: Optional[ConfigVars] = None,
        _used_as: Optional[Set[builtins.str]] = None,
    ) -> None:
        self.source = source
        self.meta = dict() if meta is None else meta
        self._key = key
        self._value = str(value)
        self._vars_dict = dict() if vars_dict is None else vars_dict
        self._used_as = set() if _used_as is None else _used_as

    @property
    def type(self) -> Optional[builtins.str]:
        """Type hint for the ConfigurationEntry"""
        return self.meta.get("type", None)

    @property
    def help(self) -> builtins.str:
        """Help text for the ConfigurationEntry"""
        return self.meta.get("help", "")

    @property
    def str(self) -> builtins.str:
        """Value of ConfigurationEntry as string"""
        self._using("str")
        return self._value

    def as_str(self) -> builtins.str:
        """Value of ConfigurationEntry as string"""
        return self.str

    @property
    def int(self) -> builtins.int:
        """Value of ConfigurationEntry converted to an integer"""
        self._using("int")
        try:
            return int(self._value)
        except ValueError:
            raise ValueError(
                f"Value '{self._value}' of '{self._key}' in {self.source} cannot be converted to an integer"
            ) from None

    def as_int(self) -> builtins.int:
        """Value of ConfigurationEntry converted to an integer"""
        return self.int

    @property
    def float(self) -> builtins.float:
        """Value of ConfigurationEntry converted to a float"""
        self._using("float")
        try:
            return float(self._value)
        except ValueError:
            raise ValueError(
                f"Value '{self._value}' of '{self._key}' in {self.source} cannot be converted to a float"
            ) from None

    def as_float(self) -> builtins.float:
        """Value of ConfigurationEntry converted to a float"""
        return self.float

    @property
    def bool(self) -> builtins.bool:
        """Value of ConfigurationEntry converted to a boolean

        The conversion is done by looking up the string value of the entry in _BOOLEAN_STATES.
        """
        self._using("bool")
        try:
            return self._BOOLEAN_STATES[self._value.lower()]
        except KeyError:
            raise ValueError(
                f"Value '{self._value}' of '{self._key}' in {self.source} cannot be converted to a boolean"
            ) from None

    def as_bool(self) -> builtins.bool:
        """Value of ConfigurationEntry converted to a boolean

        The conversion is done by looking up the string value of the entry in _BOOLEAN_STATES.
        """
        return self.bool

    @property
    def date(self) -> stdlib_datetime.date:
        """Value of ConfigurationEntry converted to a date object assuming format `FMT_date`"""
        return self.as_date(format=FMT_date)

    def as_date(self, format: builtins.str = FMT_date) -> stdlib_datetime.date:
        """Value of ConfigurationEntry converted to a date object

        Args:
            format (String):  Format string, see strftime for information about the string.

        Returns:
            Date:  Value of entry.
        """
        self._using("date")
        try:
            return stdlib_datetime.datetime.strptime(self._value, format).date()
        except ValueError:
            raise ValueError(
                f"Value '{self._value}' of '{self._key}' in {self.source} does not match the date format '{format}'"
            ) from None

    @property
    def datetime(self) -> stdlib_datetime.datetime:
        """Value of ConfigurationEntry converted to a datetime object assuming format `FMT_datetime`"""
        return self.as_datetime(format=FMT_datetime)

    def as_datetime(self, format: builtins.str = FMT_datetime) -> stdlib_datetime.datetime:
        """Value of ConfigurationEntry converted to a datetime object

        Args:
            format (String):  Format string, see strftime for information about the string.

        Returns:
            Datetime:  Value of entry.
        """
        self._using("datetime")
        try:
            return stdlib_datetime.datetime.strptime(self._value, format)
        except ValueError:
            raise ValueError(
                f"Value '{self._value}' of '{self._key}' in {self.source} does not match the date format '{format}'"
            ) from None

    @property
    def path(self) -> pathlib.Path:
        """Value of ConfigurationEntry interpreted as a path string"""
        self._using("path")
        path = self._value
        if "~" in path:
            path = os.path.expanduser(path)

        return pathlib.Path(path)

    def as_path(self) -> pathlib.Path:
        """Value of ConfigurationEntry interpreted as a path string"""
        return self.path

    @property
    def list(self) -> List[builtins.str]:
        """Value of ConfigurationEntry converted to a list by splitting at commas and whitespace"""
        self._using("list")
        return self._value.replace(",", " ").split()

    def as_list(
        self, split_re: builtins.str = r"[\s,]", convert: Callable = builtins.str, maxsplit: builtins.int = 0
    ) -> List[Any]:
        """Value of ConfigurationEntry converted to a list

        The entry is converted to a list by using the `split_re`-regular expression. By default the entry will be split
        at commas and whitespace.

        Args:
            split_re:  Regular expression used to split entry into list.
            convert:   Function used to convert each element of the list.
            maxsplit:  If nonzero, at most maxsplit splits occur.

        Returns:
            Value of entry as list.
        """
        self._using("list")
        return [convert(s) for s in re.split(split_re, self._value, maxsplit=maxsplit) if s]

    @property
    def list_of_lists(self) -> List[List[builtins.str]]:
        self._using("list_of_lists")
        raise NotImplementedError

    def as_list_of_lists(
        self,
        split_res: Tuple[builtins.str, ...] = (r"[\s,]", r"[^_\w]"),
        num_elements: Optional[builtins.int] = None,
        convert: Callable = builtins.str,
    ) -> List[List[Any]]:
        self._using("list_of_lists")
        raise NotImplementedError

    @property
    def tuple(self) -> Tuple[builtins.str, ...]:
        """Value of ConfigurationEntry converted to tuple by splitting at commas and whitespace"""
        self._using("tuple")
        return tuple(self._value.replace(",", " ").split())

    def as_tuple(
        self, split_re: builtins.str = r"[\s,]", convert: Callable = builtins.str, maxsplit: builtins.int = 0
    ) -> Tuple[Any, ...]:
        """Value of ConfigurationEntry converted to a tuple

        The entry is converted to a tuple by using the `split_re`-regular expression. By default the entry will be
        split at commas and whitespace.

        Args:
            split_re:  Regular expression used to split entry into tuple.
            convert:   Function used to convert each element of the tuple.
            maxsplit:  If nonzero, at most maxsplit splits occur.

        Returns:
            Value of entry as tuple.
        """
        self._using("tuple")
        return tuple([convert(s) for s in re.split(split_re, self._value, maxsplit=maxsplit) if s])

    @property
    def dict(self) -> Dict[builtins.str, builtins.str]:
        """Value of ConfigurationEntry converted to a dict"""
        self._using("dict")
        return dict(i.partition(":")[::2] for i in self.list)

    def as_dict(
        self,
        item_split_re: builtins.str = r"[\s,]",
        key_value_split_re: builtins.str = r"[:]",
        convert: Callable = builtins.str,
        maxsplit: builtins.int = 0,
    ) -> Dict[builtins.str, Any]:
        """Value of ConfigurationEntry converted to a dictionary

        By default the dictionary is created by splitting items at commas and whitespace,
        and key from value at colons.

        Args:
            item_split_re:       Regular expression used to split entry into items.
            key_value_split_re:  Regular expression used to split items into keys and values.
            convert:             Function used to convert each value in the dictionary.
            maxsplit:            If nonzero, at most maxsplit splits occur when splitting entry into items.

        Returns:
            Value of entry as dict.
        """
        self._using("dict")
        items = [s for s in re.split(item_split_re, self._value, maxsplit=maxsplit) if s]
        key_values = [re.split(key_value_split_re, i, maxsplit=1) for i in items]
        return {k: convert(v) for k, v in key_values}

    def as_enum(self, enum: builtins.str) -> enums.enum.Enum:
        """Value of ConfigurationEntry converted to an enumeration

        Args:
            enum (String):   Name of Enum.

        Returns:
            Enum:  Value of entry as Enum.
        """
        self._using("enum")
        return enums.get_value(enum, self._value)

    @property
    def replaced(self) -> "ConfigurationEntry":
        """Value of ConfigurationEntry with {$}-variables replaced"""
        return self.replace()

    def replace(self, default: Optional[builtins.str] = None, **replace_vars: builtins.str) -> "ConfigurationEntry":
        value = _replace(self._value, dict(self._vars_dict, **replace_vars), default)
        return self.__class__(key=self._key, value=value, source=self.source, _used_as=self._used_as)

    @property
    def is_used(self) -> builtins.bool:
        return bool(self._used_as)

    def entry_as_str(
        self, width: Optional[builtins.int] = None, key_width: builtins.int = 30, metadata: builtins.bool = True
    ) -> builtins.str:
        """The configuration entry represented as a string

        This is simililar to what is shown by `str(entry)` (and implemented by `__str__`), but has more flexibility.

        Args:
            width:      Width of text for wrapping. Default is width of console.
            key_width:  Width of the key column. Default is 30 characters.
            metadata:   Include metadata like type and help text.

        Returns:
            String representation of the configuration entry.
        """
        lines = list()
        width = console.columns() if width is None else width
        fill_args = dict(width=width, hanging=key_width + 3, break_long_words=False, break_on_hyphens=False)

        # The entry itself
        lines.append(console.fill(f"{self._key:<{key_width}} = {self._value}", **fill_args))

        # Metadata, including help text and type hints
        if metadata and self.meta:
            for meta_key, meta_value in self.meta.items():
                if meta_value is None:
                    lines.append(console.fill(f"{self._key}:{meta_key}", **fill_args))
                else:
                    lines.append(console.fill(f"{f'{self._key}:{meta_key}':<{key_width}} = {meta_value}", **fill_args))
            lines.append("")

        return "\n".join(lines)

    def _using(self, as_type: builtins.str) -> None:
        """Register that entry is used as a type

        Args:
            as_type:  Name of type entry is used as.
        """
        self._used_as.add(as_type)

    def __add__(self, other: "ConfigurationEntry") -> "ConfigurationEntry":
        if isinstance(other, self.__class__):
            if self.source == other.source:
                source = f"{self.source} (+)"
            else:
                source = f"{self.source} + {other.source}"
            return self.__class__(
                key=f"{self._key} + {other._key}", value=self.str + other.str, source=source, vars_dict=self._vars_dict
            )
        else:
            return NotImplemented

    def __bool__(self) -> builtins.bool:
        """A ConfigurationEntry is truthy if the value is not empty"""
        return bool(self._value)

    def __str__(self) -> builtins.str:
        """The configuration entry represented as a string"""
        return self.entry_as_str()

    def __repr__(self) -> builtins.str:
        """A simple string representation of the configuration entry"""
        return f"{self.__class__.__name__}(key='{self._key}', value='{self._value}')"


def _replace(string: str, replace_vars: Dict[str, str], default: Optional[str] = None) -> str:
    """Replace format style variables in a string

    Handles nested replacements by first replacing the replace_vars. Format specifiers (after colon, :) are allowed,
    but can not contain nested format strings.

    This function is used instead of str.format for three reasons. It handles:

    - that not all pairs of {...} are replaced at once
    - optional default values for variables that are not specified
    - nested replacements where values of replace_vars may be replaced themselves

    Args:
        string:        Original string
        replace_vars:  Variables that can be replaced
        default:       Optional default value used for variables that are not in replace_vars.
    """
    matches = re.finditer(r"\{(\w+)(:[^\{\}]*)?\}", string)
    for match in matches:
        var = match.group(1)
        var_expr = match.string[slice(*match.span())]
        replacement = replace_vars.get(var)
        if replacement is None:
            replacement = var_expr if default is None else default  # Default replacements
        else:
            replacement = _replace(str(replacement), replace_vars, default)  # Nested replacements

        # Use str.format to handle format specifiers
        string = string.replace(var_expr, var_expr.format(**{var: replacement}))

    return string
