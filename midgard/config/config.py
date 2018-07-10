"""Midgard library module for handling of configuration settings

Description:
------------

A Configuration consists of one or several sections. Each ConfigurationSection consists of one or more entries. Each
ConfigurationEntry consists of a key and a value.


Examples:
---------

For basic use, an entry is looked up by simple attribute access. For instance if `cfg` is a Configuration with the
section `midgard` which has an entry `foo = bar`:

    >>> cfg.midgard.foo
    ConfigurationEntry('foo', 'bar')

ConfigurationEntry has several access methods that convert the entry to a given data type:

    >>> cfg.midgard.foo_pi
    ConfigurationEntry('foo_pi', '3.14')
    >>> cfg.midgard.foo_pi.float
    3.14
    >>> cfg.midgard.foo_pi.str
    '3.14'
    >>> cfg.midgard.foo_pi.tuple
    ('3.14', )


Sources:
--------

Each configuration entry records its source. That is, where that entry was defined. Examples include read from file,
set as a command line option, or programmatically from a dictionary. The source can be looked up on an individual
entry, or for all entries in a configuration.

    >>> cfg.midgard.foo.source
    '/home/midgard/midgard.conf'
    >>> cfg.sources
    {'/home/midgard/midgard.conf', 'command line'}


Profiles:
---------


Parent Configuration:
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

# Where imports
from midgard.dev import console
from midgard.collections import enums
from midgard.dev import exceptions


# Typing
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

ProfileName = Union[None, str]
SectionName = str
Sections = Dict[SectionName, "ConfigurationSection"]
EntryName = str
ConfigVars = Dict[str, Any]


# Date and datetime formats
FMT_date = "%Y-%m-%d"
FMT_datetime = "%Y-%m-%d %H:%M:%S"
FMT_dt_file = "%Y%m%d-%H%M%S"


class Configuration():
    """Represents a Configuration"""

    def __init__(self, name: str) -> None:
        """Initialize a Configuration

        The name is used purely for representation and error messages.

        Args:
            name:  Name of configuration.
        """
        self.name = name
        self.parent_config = None
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
    def update_on_file(cls, file_path: Union[str, pathlib.Path], **as_str_args) -> None:
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

    def write_to_file(self, file_path: Union[str, pathlib.Path], **as_str_args) -> None:
        """Write the configuration to a file

        In addition to the file path, arguments can be specified and will be passed on to the as_str() function. See
        `as_str()` for more information.

        Todo: Use files.open_path
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, mode="w") as fid:
            fid.write(self.as_str(**as_str_args) + "\n")

    @property
    def sections(self) -> List[SectionName]:
        """List of sections in Configuration"""
        return list(self._sections.keys())

    @property
    def sources(self) -> Set[str]:
        """Sources of entries in Configuration"""
        return {self[s][k].source for s in self.sections for k in self[s].keys() if self[s][k].source}

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
    def parent_config(self) -> "Configuration":
        """The parent configuration"""
        if self._parent_config is None:
            raise exceptions.MissingConfigurationError(
                f"Configuration '{self.name}' has not defined a parent configuration"
            )
        return self._parent_config

    @parent_config.setter
    def parent_config(self, cfg: Optional["Configuration"]) -> None:
        """Set the parent configuration"""
        self._parent_config = cfg

    @property
    def master_section(self) -> "ConfigurationSection":
        """The master section"""
        if self._master_section is None:
            raise exceptions.MissingSectionError(f"Configuration '{self.name}' has not defined a master section")

        try:
            return self._sections[self._master_section]
        except KeyError:
            return ConfigurationSection("undefined")

    @master_section.setter
    def master_section(self, section: Optional[SectionName]):
        """Set the master section"""
        if section is None or section in self._sections:
            self._master_section = section
        else:
            raise exceptions.MissingSectionError(f"Configuration '{self.name}' does not contain section '{section}'")

    def get(
        self, key: str, value: Optional[str] = None, section: Optional[str] = None, default: Optional[str] = None
    ) -> "ConfigurationEntry":
        """Get an entry from a configuration with possibility for override and default value

        A value for an entry is found using the following priorities:

            1. An explicit value given in `value`. None is used as a marker for no value.
            2. Looked up in the current configuration.
            3. Looked up in any parent confiurations that are defined.
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
            return self.master_section[key] if section is None else self[section][key]
        except (exceptions.MissingSectionError, exceptions.MissingEntryError):
            try:
                return self.parent_config.get(key=key, section=section)
            except (exceptions.MissingConfigurationError, exceptions.MissingEntryError):
                if default is None:
                    return self.master_section[key] if section is None else self[section][key]
                else:
                    return ConfigurationEntry(key, value=default, source="default value", vars_dict=self.vars)

    def update(
        self,
        section: SectionName,
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
        self, file_path: Union[str, pathlib.Path], allow_new: bool = True, interpolate: bool = False
    ) -> None:
        """Update the configuration from a configuration file

        The Python ConfigParser is used to read the file. The file format that is supported is described at
        https://docs.python.org/library/configparser.html

        Different profiles in a configuration file is denoted by double underscores in the sections names. For instance
        does the following configuration have a `foo` profile in the `spam` section (in addition to the default
        profile):

            [spam]
            ...

            [spam__foo]
            ...

        If `interpolate` is set to True, ExtendedInterpolation of variables in the configuration file is used. See
        https://docs.python.org/library/configparser.html#configparser.ExtendedInterpolation for details.

        Args:
            file_path:    Path to the configuration file.
            allow_new:    Whether to allow the creation of new sections and entries.
            interpolate:  Whether to interpolate variables in the configuration file.
        """
        # Use ConfigParser to read from file
        cfg_parser_args = dict(
            allow_no_value=True,
            delimiters=("=",),
            interpolation=ExtendedInterpolation() if interpolate else BasicInterpolation(),
        )
        cfg_parser = ConfigParser(**cfg_parser_args)
        cfg_parser.read(file_path)

        # Add configuration entries
        for cfg_section in cfg_parser.sections():
            section, has_profile, profile = cfg_section.partition("__")
            for key, value in cfg_parser[cfg_section].items():
                # Handle meta-information
                if ":" in key:
                    continue
                meta = {k.partition(":")[-1]: v for k, v in cfg_parser[cfg_section].items() if k.startswith(f"{key}:")}

                # Create a configuration entry
                self.update(
                    section,
                    key,
                    value if value is None else value.replace("\n", " "),
                    profile=profile if has_profile else None,
                    source=str(file_path),
                    meta=meta,
                    allow_new=allow_new,
                    _update_sections=False,
                )

        self._set_sections_for_profiles()

    def update_from_config_section(
        self, other_section: "ConfigurationSection", section: Optional[SectionName] = None, allow_new: bool = True
    ) -> None:
        section = other_section.name if section is None else section
        for key, entry in other_section.items():
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
            self.update(
                opt_section,
                opt_key,
                opt_value,
                profile=profile,
                source=f"{source} ({option})",
                allow_new=allow_new,
                _update_sections=False,
            )

        self._set_sections_for_profiles()

    def update_from_dict(
        self,
        cfg_dict: Dict[str, Any],
        section: Optional[SectionName] = None,
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
        self, getters: Optional[Dict[SectionName, Dict[str, str]]] = None, default_getter: str = "str"
    ) -> Dict[SectionName, Dict[str, Any]]:
        """The configuration represented as a dictionary

        Args:
            getters:         How to get the value of each entry in each section.
            default_getter:  How to get the value of entries not specified in getters.

        Returns:
            Representation of the configuration as a nested dictionary.
        """
        getters = dict() if getters is None else getters
        return {k: v.as_dict(getters=getters.get(k), default_getter=default_getter) for k, v in self._sections.items()}

    def __getitem__(self, key: SectionName) -> "ConfigurationSection":
        """Get a section or entry from the master section from the configuration"""
        try:
            return self._sections[key]
        except KeyError:
            try:
                return self.master_section[key]
            except exceptions.MissingSectionError:
                raise exceptions.MissingSectionError(f"Configuration '{self.name}' has no section '{key}'") from None

    def __getattr__(self, key: SectionName) -> "ConfigurationSection":
        """Get a section or entry from the master section from the configuration"""
        return self[key]

    def __delitem__(self, key: SectionName) -> None:
        """Delete a section from the configuration"""
        del self._sections[key]

    def __delattr__(self, key: SectionName) -> None:
        """Delete a section from the configuration"""
        del self._sections[key]

    def __dir__(self) -> List[str]:
        """List attributes and sections in the configuration"""
        try:
            return super().__dir__() + self.sections + self.master_section.as_list()
        except exceptions.MissingSectionError:
            return super().__dir__() + self.sections

    def __str__(self) -> str:
        """The configuration represented as a string

        This string can be stored in a file and read back with `update_from_file`.
        """
        return "\n\n".join(str(s) for s in self._sections.values())

    def __repr__(self) -> str:
        """A simple string representation of the configuration"""
        return f"{self.__class__.__name__}(name='{self.name}')"


class ConfigurationSection(UserDict):

    def __init__(self, name: SectionName) -> None:
        super().__init__()
        self.name = name

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

    def __getitem__(self, key: EntryName) -> "ConfigurationEntry":
        """Get an entry from the configuration section"""
        try:
            return self.data[key]
        except KeyError:
            raise exceptions.MissingEntryError(f"Configuration section '{self.name}' has no entry '{key}'") from None

    def __getattr__(self, key: EntryName) -> "ConfigurationEntry":
        """Get an entry from the configuration section"""
        try:
            return self.data[key]
        except KeyError:
            raise exceptions.MissingEntryError(f"Configuration section '{self.name}' has no entry '{key}'") from None

    def __dir__(self) -> List[str]:
        """List attributes and entries in the configuration section"""
        return super().__dir__() + self.as_list()

    def __str__(self) -> str:
        """The configuration section represented as a string"""
        return f"[{self.name}]\n" + "\n".join(str(v) for v in self.data.values())

    def __repr__(self) -> str:
        """A simple string representation of the configuration section"""
        return f"{self.__class__.__name__}(name='{self.name}')"


class ConfigurationEntry():

    _BOOLEAN_STATES = {
        "0": False, "1": True, "false": False, "true": True, "no": False, "yes": True, "off": False, "on": True
    }

    def __init__(
        self,
        key: EntryName,
        value: Any,
        *,
        source: builtins.str = "",
        meta: Optional[Dict[str, Any]] = None,
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

    def as_list(self, split_re: builtins.str = r"[\s,]", convert: Callable = builtins.str) -> List[Any]:
        """Value of ConfigurationEntry converted to a list

        The entry is converted to a list by using the `split_re`-regular expression. By default the entry will be split
        at commas and whitespace.

        Args:
            split_re:  Regular expression used to split entry into list.
            convert:   Function used to convert each element of the list.

        Returns:
            Value of entry as list.
        """
        self._using("list")
        return [convert(s) for s in re.split(split_re, self._value) if s]

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

    def as_tuple(self, split_re: builtins.str = r"[\s,]", convert: Callable = builtins.str) -> Tuple[Any, ...]:
        """Value of ConfigurationEntry converted to a tuple

        The entry is converted to a tuple by using the `split_re`-regular expression. By default the entry will be
        split at commas and whitespace.

        Args:
            split_re:  Regular expression used to split entry into tuple.
            convert:   Function used to convert each element of the tuple.

        Returns:
            Value of entry as tuple.
        """
        self._using("tuple")
        return tuple([convert(s) for s in re.split(split_re, self._value) if s])

    @property
    def dict(self) -> Dict[builtins.str, builtins.str]:
        """Value of ConfigurationEntry converted to a dict"""
        self._using("dict")
        return dict(i.split(":", maxsplit=1) for i in self.list)

    def as_dict(
        self,
        item_split_re: builtins.str = r"[\s,]",
        key_value_split_re: builtins.str = r"[:]",
        convert: Callable = builtins.str,
    ) -> Dict[builtins.str, Any]:
        """Value of ConfigurationEntry converted to a dictionary

        By default the dictionary is created by splitting items at commas and whitespace,
        and key from value at colons.

        Args:
            item_split_re:       Regular expression used to split entry into items.
            key_value_split_re:  Regular expression used to split items into keys and values.
            convert:             Function used to convert each value in the dictionary.

        Returns:
            Value of entry as dict.
        """
        self._using("dict")
        items = [s for s in re.split(item_split_re, self._value) if s]
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
        replacement_vars = dict(self._vars_dict, **replace_vars)
        replacement_value = self._value
        replacements = list()

        matches = re.findall(r"\{\$\w+\}", replacement_value)
        for match in matches:
            var = match.strip("${}")
            replacement = str(replacement_vars.get(var, match if default is None else default))
            replacements.append(f"{var}={replacement}")
            replacement_value = replacement_value.replace(match, replacement)

        return self.__class__(
            key=self._key,
            value=replacement_value,
            source=self.source + " ({','.join(replacements)})",
            _used_as=self._used_as,
        )

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
