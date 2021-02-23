# midgard.config


## midgard.config.config
Midgard library module for handling of configuration settings

**Description:**

A Configuration consists of one or several sections. Each ConfigurationSection
consists of one or more entries. Each ConfigurationEntry consists of a key and
a value.


**Examples:**

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


**Sources:**

Each configuration entry records its source. That is, where that entry was
defined. Examples include read from file, set as a command line option, or
programmatically from a dictionary. The source can be looked up on an
individual entry, or for all entries in a configuration.

    >>> cfg.midgard.foo_pi.source
    'command line'
    >>> cfg.sources  # doctest: +SKIP
    {'/home/midgard/midgard.conf', 'command line'}


**Profiles:**


**Fallback Configuration:**


**Master Section:**


**Replacement Variables:**


**Help text and Type hints:**



### **CasedConfigParser**

Full name: `midgard.config.config.CasedConfigParser`

Signature: `(defaults=None, dict_type=<class 'dict'>, allow_no_value=False, *, delimiters=('=', ':'), comment_prefixes=('#', ';'), inline_comment_prefixes=None, strict=True, empty_lines_in_values=True, default_section='DEFAULT', interpolation=<object object at 0x7fa99576b930>, converters=<object object at 0x7fa99576b930>)`

ConfigParser with case-sensitive keys

### **Configuration**

Full name: `midgard.config.config.Configuration`

Signature: `(name: str) -> None`

Represents a Configuration

### **ConfigurationEntry**

Full name: `midgard.config.config.ConfigurationEntry`

Signature: `(key: str, value: Any, *, source: str = '', meta: Union[Dict[str, str], NoneType] = None, vars_dict: Union[Dict[str, str], NoneType] = None, _used_as: Union[Set[str], NoneType] = None) -> None`



### **ConfigurationSection**

Full name: `midgard.config.config.ConfigurationSection`

Signature: `(name: str) -> None`



### FMT_date (str)
`FMT_date = '%Y-%m-%d'`


### FMT_datetime (str)
`FMT_datetime = '%Y-%m-%d %H:%M:%S'`


### FMT_dt_file (str)
`FMT_dt_file = '%Y%m%d-%H%M%S'`


## midgard.config.files
Midgard library module for opening files based on a special configuration

**Example:**

    from midgard.config import files
    with files.open('eopc04_iau', mode='rt') as fid:
        for line in fid:
            print(line.strip())

**Description:**

This module handles opening of files registered in a special configuration, typically a configuration file.


The cfg.files.open and cfg.files.open_path methods are both wrappers around the built-in open function, and behave
mainly similar. In particular, they accept all the same keyword arguments (like for instance mode). Furthermore, to
make sure files are properly closed they should normally be used with a context manager as in the example above.



### **FileConfiguration**

Full name: `midgard.config.files.FileConfiguration`

Signature: `(name: str) -> None`

Configuration for handling files

### path_type (TypeVar)
`path_type = ~path_type`
