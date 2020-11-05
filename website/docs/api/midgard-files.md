# midgard.files


## midgard.files.dates
Convenience functions for working with dates

**Description:**

Formats and converters that can be used for convenience and consistency.



### FMT_date (str)
`FMT_date = '%Y-%m-%d'`


### FMT_datetime (str)
`FMT_datetime = '%Y-%m-%d %H:%M:%S'`


### FMT_dt_file (str)
`FMT_dt_file = '%Y%m%d-%H%M%S'`


### **date_vars**()

Full name: `midgard.files.dates.date_vars`

Signature: `(date: Union[datetime.date, datetime.datetime, NoneType]) -> Dict[str, str]`

Construct a dict of date variables

From a given date, construct a dict containing all relevant date
variables. This dict can be used to for instance replace variables in file
names.

**Examples:**


    >>> from datetime import date
    >>> date_vars(date(2009, 11, 2))  # doctest: +NORMALIZE_WHITESPACE
    {'yyyy': '2009', 'ce': '20', 'yy': '09', 'm': '11', 'mm': '11', 'mmm': 'nov', 'MMM': 'NOV', 'd': '2',
     'dd': '02', 'doy': '306', 'dow': '1', 'h': '0', 'hh': '00'}

    >>> date_vars(None)
    {}

**Args:**

- `date`:  The given date.

**Returns:**

Dictionary with date variables for the given date.


## midgard.files.dependencies
Midgard library module for handling dependencies

**Description:**

Stores a list of files with a hash/checksum or a timestamp that can be used to detect if a file changes.

Two strategies are available:

- Timestamps: Fast, but not always reliable as timestamps may update without the file actually changing.
- md5 hash/checksum: Slower, since it needs to read through the whole file, but will reliably only trigger when a file
  has changed.


### **add**()

Full name: `midgard.files.dependencies.add`

Signature: `(*file_paths: Union[str, pathlib.Path], label: str = '') -> None`

Add a list of files to the list of dependencies

Records the current time stamp or md5 hash of the files specified by file
paths, and stores as dependencies on the dependency file.

Before adding dependencies, a call to `init()` has to be done, to set up
where to store the dependencies.

**Args:**

- `file_paths`:  List of file paths to add to the dependency file.
- `label`:       Optional label for dependencies.


### **changed**()

Full name: `midgard.files.dependencies.changed`

Signature: `(file_path: Union[str, pathlib.Path], fast_check: bool = True) -> bool`

Check if the dependencies have changed

Returns True if any of the files listed in the dependency file have
changed, or if the dependency file itself does not exist.

**Args:**

- `file_path`:   Path to dependency file.
- `fast_check`:  Fast check uses timestamps, slow check uses md5 checksums.

**Returns:**

True if any file has changed or if the dependecy file does not exist, False otherwise.


### **get_md5**()

Full name: `midgard.files.dependencies.get_md5`

Signature: `(file_path: Union[str, pathlib.Path]) -> str`

Return a md5 checksum based on a file.

**Args:**

- `file_path`: Path to file.

**Returns:**

Hex-string representing the contents of the file.


### **get_paths_with_label**()

Full name: `midgard.files.dependencies.get_paths_with_label`

Signature: `(file_path: Union[str, pathlib.Path], label_pattern: str) -> List[pathlib.Path]`

Find all paths with the given label

**Args:**

- `file_path`:      Path to dependency file.
- `label_pattern`:  String with label or regular expression (e.g. 'gnss_rinex_nav_[MGE]' or 'gnss_rinex_nav_.').

**Returns:**

- `List`:  List of file paths.


### **get_timestamp**()

Full name: `midgard.files.dependencies.get_timestamp`

Signature: `(file_path: Union[str, pathlib.Path]) -> str`

Return a textual timestamp from the modification date of a file

**Args:**

- `file_path`:  Path to file.

**Returns:**

String representing the modification date of the file.


### **init**()

Full name: `midgard.files.dependencies.init`

Signature: `(file_path: Union[str, pathlib.Path], fast_check: bool = True) -> None`

Start a clean list of dependencies

The file_path is to the file in which dependencies are stored. This is
cached, so after init() is run, the other functions do not need to specify
the file_path.

**Args:**

- `file_path`:   Path to dependency file.
- `fast_check`:  Fast check uses timestamps, slow check uses md5 checksums.


### **write**()

Full name: `midgard.files.dependencies.write`

Signature: `() -> None`

Write dependencies to file


## midgard.files.files
Utilities for working with files



### **move**()

Full name: `midgard.files.files.move`

Signature: `(from_path: Union[str, pathlib.Path], to_path: Union[str, pathlib.Path], overwrite: bool = True) -> None`

Move a file to another path

With overwrite set to True, to_path may already exist and will be overwritten without warning. Setting overwrite to
False will raise a FileExistsError if to_path already exists.

**Args:**

- `from_path`:  Path of file to be moved.
- `to_path`:    Path file will be moved to.
- `overwrite`:  If True, to_path may already exist. If False, to_path will never be overwritten.


### **open**()

Full name: `midgard.files.files.open`

Signature: `(file_path: Union[str, pathlib.Path], create_dirs: bool = False, open_as_gzip: Union[bool, NoneType] = None, **open_args: Any) -> Iterator`

Open a file.

Can automatically create the necessary directories before writing to a file, as well as handle gzipped files.

With `open_as_gzip` set to None (default), it will try to detect whether the path is a .gz file simply by looking
at the path suffix. For more control, you can set the parameter to True or False explicitly.

**Args:**

- `file_path`:     String or pathlib.Path representing the full file path.
- `create_dirs`:   True or False, if True missing directories are created.
- `open_as_gzip`:  Use gzip library to open file.
- `open_args`:     All keyword arguments are passed on to the built-in open.

**Returns:**

File object representing the file.


## midgard.files.url
Midgard library module, defining a URL class that mirrors Pathlib.Path

Warning: There are many intricacies of URLs that are not handled by this class at the moment.



### **URL**

Full name: `midgard.files.url.URL`

Signature: `()`

Simple wrapper around String to have URLs work similar to pathlib.Path
