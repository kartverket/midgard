"""Midgard library module for opening files based on a special configuration

Example:
--------

    from midgard.config import files
    with files.open('eopc04_iau', mode='rt') as fid:
        for line in fid:
            print(line.strip())

Description:
------------

This module handles opening of files registered in a special configuration, typically a configuration file.


The cfg.files.open and cfg.files.open_path methods are both wrappers around the built-in open function, and behave
mainly similar. In particular, they accept all the same keyword arguments (like for instance mode). Furthermore, to
make sure files are properly closed they should normally be used with a context manager as in the example above.

"""

# Standard library imports
import builtins
from contextlib import contextmanager
import gzip
import itertools
import pathlib
import re
from typing import Any, Dict, Iterator, List, Optional, Set, TypeVar

# Third party imports
import pycurl

# Midgard imports
from midgard.config.config import Configuration
from midgard.dev import console
from midgard.dev import log
from midgard.files import files
from midgard.files import url

# Type specification: scalar float or numpy array
path_type = TypeVar("path_type", str, pathlib.Path)


class FileConfiguration(Configuration):
    """Configuration for handling files"""

    download_missing = True

    @contextmanager
    def open(
        self,
        file_key: str,
        file_vars: Dict[str, str] = None,
        create_dirs: bool = False,
        is_zipped: Optional[bool] = None,
        download_missing: bool = True,
        use_aliases: bool = True,
        **open_args: Any,
    ) -> Iterator:
        """Open a file based on information in a configuration

        Open a file based on file key which is looked up in the configuration.

        The method automatically handles reading from gzipped files if the filename is specified with the special
        {gz}-ending (including the curly braces) in the file list. In that case, the mode should be specified to be
        'rt' if the contents of the file should be treated as text. If both a zipped and an unzipped version is
        available, the zipped version is used. This can be overridden by specifying True or False for the
        is_zipped-parameter.

        This function behaves similar to the built-in open-function, and should typically be used with a context
        manager as follows:

        Example:

            with cfg.open('eopc04_iau', mode='rt') as fid:
                for line in fid:
                    print(line.strip())

        Args:
            file_key:     String that is looked up in the configuration file list.
            file_vars:    Dict, extra variables used to replace variables in file name and path.
            create_dirs:  True or False, if True missing directories are created.
            iz_zipped:    None, True, or False. Whether the file
            open_args:    All keyword arguments are passed on to open_path.

        Returns:
            File object representing the file.
        """
        download_missing = download_missing and "r" in open_args.get("mode", "r")
        file_path = self.path(
            file_key, file_vars, is_zipped=is_zipped, download_missing=download_missing, use_aliases=use_aliases
        )
        if "encoding" not in open_args:
            file_encoding = self.get("encoding", section=file_key, default="").str
            open_args["encoding"] = file_encoding or None

        mode = open_args.get("mode", "r")
        _log_file_open(file_path, description=file_key, mode=mode)

        try:
            with files.open(file_path, create_dirs=create_dirs, open_as_gzip=is_zipped, **open_args) as fid:
                yield fid
        except Exception:
            raise

    @contextmanager
    def open_path(
        self,
        file_path: path_type,
        description: str = "",
        create_dirs: bool = False,
        is_zipped: Optional[bool] = None,
        write_log: bool = True,
        **open_args: Any,
    ) -> Iterator:
        """Open a file with given path

        Open a local file based on file name. This function behaves similar to the built-in open-function, but is also
        able to create intermediate directories and open gzipped files. The function should typically be used with a
        context manager as follows:

        Example:
            with files.open_path('local_output.txt', mode='rt') as fid:
                for line in fid:
                    print(line.strip())

        Args:
            file_path:       The file_path, should be a full path.
            description:     Description used for logging.
            create_dirs:     True or False, if True missing directories are created.
            is_zipped:       True or False, if True the gzip module will be used.
            open_args:       All keyword arguments are passed on to the built-in open.

        Returns:
            File object representing the file.
        """
        mode = open_args.get("mode", "r")
        if "mode" in open_args:  # TODO: "mode" should maybe be a required argument
            del open_args["mode"]
        if write_log:
            _log_file_open(file_path, description, mode)
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        is_zipped = self.is_path_zipped(file_path) if is_zipped is None else is_zipped

        try:
            if is_zipped:
                with gzip.open(file_path, mode=mode, **open_args) as fid:
                    yield fid
            else:
                with builtins.open(file_path, mode=mode, **open_args) as fid:
                    yield fid
        except Exception:
            raise

    def path(
        self,
        file_key: str,
        file_vars: Optional[Dict[str, str]] = None,
        default: Optional[str] = None,
        is_zipped: Optional[bool] = None,
        download_missing: bool = False,
        use_aliases: bool = True,
    ) -> pathlib.Path:
        """Construct a filepath for a given file with variables

        If `is_zipped` is None, and the file_path contains `<filename>{gz}`,
        the file will be assumed to be a gzip-file if there exists a file named
        `<filename>.gz`.

        When setting `use_aliases` to True, the aliases as specified in the
        files configuration file represent alternative filenames. In
        particular:

            - if directory / file_name exists it is returned
            - otherwise the first directory / alias that exists is returned
            - if none of these exist, directory / file_name is returned

        Args:
            file_key (String):        Key that is looked up in the configuration.
            file_vars (Dict):         Values used to replace variables in file name and path.
            default (String):         Value to use for variables that are not in file_vars.
            is_zipped (Bool/None):    True, False or None. If True, open with gzip. If None automatically decide.
            download_missing (Bool):  Whether to try to download missing files.
            use_aliases (Bool):       Fall back on aliases if file does not exist.

        Return:
            Path: Full path with replaced variables in file name and path.
        """
        file_vars = dict() if file_vars is None else file_vars
        directory = self[file_key].directory.replace(default=default, **file_vars).path
        file_name = self[file_key].filename.replace(default=default, **file_vars).path
        file_path = self._replace_gz(directory / file_name, is_zipped)

        # Check for aliases
        if use_aliases and not self._path_exists(file_path):
            aliases = self.get("aliases", section=file_key, default="").replace(default=default, **file_vars).list
            for alias in aliases:
                aliased_path = self._replace_gz(file_path.with_name(alias), is_zipped)
                if self._path_exists(aliased_path):
                    return aliased_path

        # Try to download the file if it is missing
        if download_missing and not self._path_exists(file_path):
            downloaded_file_path = self.download_file(file_key, file_vars, file_path, is_zipped=is_zipped)
            if downloaded_file_path is not None:
                file_path = downloaded_file_path
        return file_path

    def aliased_path(
        self,
        file_key: str,
        file_vars: Optional[Dict[str, str]] = None,
        default: Optional[str] = None,
        is_zipped: Optional[bool] = None,
    ) -> pathlib.Path:
        """Construct a list of aliased file paths for a given file key with variables

        If `is_zipped` is None, and the file_path contains `<filename>{gz}`,
        the file will be assumed to be a gzip-file if there exists a file named
        `<filename>.gz`.

        Args:
            file_key (String):        Key that is looked up in the configuration.
            file_vars (Dict):         Values used to replace variables in file name and path.
            default (String):         Value to use for variables that are not in file_vars.
            is_zipped (Bool/None):    True, False or None. If None automatically decide.
        Return:
            List of full paths with replaced variables in file name and path.
        """
        file_vars = dict() if file_vars is None else file_vars
        directory = self[file_key].directory.replace(default=default, **file_vars).path
        file_name = self[file_key].filename.replace(default=default, **file_vars).path
        file_path = self._replace_gz(directory / file_name, is_zipped)

        aliases = self.get("aliases", section=file_key, default="").replace(default=default, **file_vars).list
        return [self._replace_gz(file_path.with_name(a), is_zipped) for a in aliases]

    def url(self, file_key, file_vars=None, default=None, is_zipped=None, use_aliases=False):
        """Construct a URL for a given file with variables

        If `is_zipped` is None, and the url contains `<filename>{gz}`, the url
        will be assumed to point to a gzip-file if there exists a file named
        `<filename>.gz` on the server.

        Args:
            file_key:     Key that is looked up in the configuration.
            file_vars:    Values used to replace variables in file name and path.
            default:      Value to use for variables that are not in file_vars.
            is_zipped:    True, False or None. If True, open with gzip. If None automatically decide.
            use_aliases:  Fall back on aliases if URL does not exist - may be slow.

        Return:
            String: Full URL with replaced variables in file name and url.
        """
        file_vars = dict() if file_vars is None else file_vars
        base_url = self[file_key].url.replace(default=default, **file_vars).str.rstrip("/")
        file_name = self[file_key].filename.replace(default=default, **file_vars).str
        file_url = self._replace_gz(url.URL(f"{base_url}/{file_name}"), is_zipped=is_zipped)

        # Check for aliases
        if use_aliases and not file_url.exists():
            aliases = self.get("aliases", section=file_key, default="").replace(default=default, **file_vars).list
            for alias in aliases:
                aliased_url = self._replace_gz(file_url.with_name(alias), is_zipped=is_zipped)
                if aliased_url.exists():
                    return aliased_url

        return file_url

    @staticmethod
    def _replace_gz(file_path: pathlib.Path, is_zipped: Optional[bool] = None) -> pathlib.Path:
        """Replace the {gz} pattern with '.gz' or '' depending on whether the file is zipped

        If `is_zipped` is None, and the file_path contains `<filename>{gz}`,
        the file will be assumed to be a gzip-file if there exists a file named
        `<filename>.gz`.

        Args:
            file_path:  Path to a file
            is_zipped:  True, False or None. If True, open with gzip. If None automatically decide.

        Returns:
            File path with {gz} replaced.
        """
        if "{gz}" not in file_path.name:
            return file_path

        if is_zipped is None:
            is_zipped = file_path.with_name(file_path.name.replace("{gz}", ".gz")).exists()
        if is_zipped:
            return file_path.with_name(file_path.name.replace("{gz}", ".gz"))
        else:
            return file_path.with_name(file_path.name.replace("{gz}", ""))

    @classmethod
    def empty_file(cls, file_path: pathlib.Path) -> bool:
        """Check if a file is empty

        Args:
            file_path:  Path to a file.

        Returns:
            Whether path is empty or not.
        """
        if not cls._path_exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' does not exist")

        return not (file_path.stat().st_size > 0)

    @staticmethod
    def _path_exists(file_path: pathlib.Path) -> bool:
        """Check if a path exists

        Unfortunately, Windows throws an error when doing file_path.exists() if
        the file path contains wildcard characters like *. Thus, we wrap this
        in a check on whether the file path syntax is correct before calling
        file_path.exists.  If the file path contains non-path characters, the
        file path can not exist.

        Args:
            file_path:  Path to a file.

        Returns:
            Whether path exists or not.
        """
        try:
            return file_path.exists()
        except OSError:
            return False

    @staticmethod
    def is_path_zipped(file_path):
        """Indicate whether a path is to a gzipped file or not

        For now, this simply checks whether the path ends in .gz or not.

        Args:
            file_path (Path):  Path to a file.

        Returns:
            Boolean:   True if path is to a gzipped file, False otherwise.
        """
        try:
            file_name = file_path.name  # Assume file_path is Path-object
        except AttributeError:
            file_name = file_path  # Fall back to file_path being string
        return file_name.endswith(".gz")

    def encoding(self, file_key):
        """Look up the encoding for a given file key

        Args:
            file_key (String):  Key that is looked up in the configuration.

        Returns:
            String:  Name of encoding. If encoding is not specified None is returned.
        """
        file_encoding = self.get("encoding", section=file_key, default="").str
        return file_encoding or None

    def download_file(
        self,
        file_key: str,
        file_vars: Optional[Dict[str, str]] = None,
        file_path: Optional[pathlib.Path] = None,
        create_dirs: bool = True,
        **path_args: Any,
    ) -> Optional[pathlib.Path]:
        """Download a file from the web and save it to disk

        Use pycurl (libcurl) to do the actual downloading. Requests might be
        nicer for this, but turned out to be much slower (and in practice
        unusable for bigger files) and also not really supporting
        ftp-downloads.

        Args:
            file_key:     File key that should be downloaded.
            file_vars:    File variables used to find path from file_key.
            file_path:    Path where file will be saved, default is to read from configuration.
            create_dirs:  Create directories as necessary before downloading file.
            path_args:    Arguments passed on to .path() to find file_path.

        Returns:
            Path to downloaded file, None if no file was downloaded.
        """
        # Do not download anything if download_missing class variable is False
        if not self.download_missing:
            return None

        # Do not download anything if url is not given in configuration
        if "url" not in self[file_key] or not self[file_key].url.str:
            return None

        # Get file_path from configuration if it's not given explicitly
        file_url = self.url(file_key, file_vars=file_vars, **path_args)
        is_zipped = self.is_path_zipped(file_url)
        path_args.update(is_zipped=is_zipped)

        if file_path is None:
            file_path = self.path(file_key, file_vars=file_vars, download_missing=False, **path_args)
        file_path = file_path.with_name(file_url.name)

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        log.info(f"Download {file_key} from '{file_url}' to '{file_path}'")
        with builtins.open(file_path, mode="wb") as fid:
            c = pycurl.Curl()
            c.setopt(c.URL, file_url)
            c.setopt(c.WRITEDATA, fid)
            try:
                c.perform()
                if not (200 <= c.getinfo(c.HTTP_CODE) <= 299):
                    raise pycurl.error()
            except pycurl.error:
                log.error(f"Problem downloading file: {c.getinfo(c.EFFECTIVE_URL)} ({c.getinfo(c.HTTP_CODE)})")
                if file_path.exists():  # Print first 10 lines to console
                    head_of_file = f"Contents of '{file_path}':\n" + "\n".join(file_path.read_text().split("\n")[:10])
                    log.info(console.indent(head_of_file, num_spaces=8))
                    file_path.unlink()
                log.warn(f"Try to download '{file_url}' manually and save it at '{file_path}'")
            else:
                log.info(f"Done downloading {file_key}")
            finally:
                c.close()
        return file_path

    def glob_paths(
        self, file_key: str, file_vars: Optional[Dict[str, str]] = None, is_zipped: Optional[bool] = None
    ) -> List[pathlib.Path]:
        """Find all file paths for the given file_key matching a filename pattern"""
        path_string = str(self.path(file_key, file_vars, default="*", is_zipped=is_zipped))
        path_aliases = self.aliased_path(file_key, file_vars, default="*", is_zipped=is_zipped)
        paths = self._glob_paths(path_string)
        for alias in path_aliases:
            paths += self._glob_paths(str(alias))
        return paths

    def _glob_paths(self, path_string):
        """Find all file paths matching the path string

        Using pathlib.Path.glob() here is not trivial because we need to split
        into a base directory to start searching from and a pattern which may
        include directories. With glob.glob() this is trivial. The downside is
        that it only returns strings and not pathlib.Paths.
        """
        glob_path = pathlib.Path(re.sub(r"\*+", "*", path_string))
        idx = min((i for i, p in enumerate(glob_path.parts) if "*" in p), default=len(glob_path.parts) - 1)
        glob_base = pathlib.Path(*glob_path.parts[:idx])
        glob_pattern = str(pathlib.Path(*glob_path.parts[idx:]))
        return list(glob_base.glob(glob_pattern))

    def glob_variable(
        self, file_key: str, variable: str, pattern: str, file_vars: Optional[Dict[str, str]] = None
    ) -> Set[str]:
        """Find all possible values of variable

        Args:
            file_key:     File key that should be downloaded.
            variable:     Variable used in searching pattern.
            pattern:      Search pattern.
            file_vars:    File variables used to find path from file_key.

        Returns:
            Possible values of given variable
        """

        # Find available paths
        file_vars = dict() if file_vars is None else dict(file_vars)
        file_vars[variable] = "*"
        search_paths = self.glob_paths(file_key, file_vars)

        # Set up the regular expression
        re_vars = {**file_vars, variable: f"(?P<{variable}>__pattern__)"}
        file_path_pattern = self.path(file_key, file_vars=re_vars, default=".*")
        aliased_path_patterns = self.aliased_path(file_key, file_vars=re_vars, default=".*")

        for path_pattern in [file_path_pattern] + aliased_path_patterns:
            path_pattern = str(path_pattern).replace("\\", "\\\\")
            values = self._match_pattern(search_paths, path_pattern, variable, pattern)
            if values:
                break
        return values

    def _match_pattern(self, search_paths, path_pattern, variable, pattern):
        """Look for variable matching pattern in the given search paths."""
        for i in itertools.count():
            # Give unique names to each occurance of variable
            path_pattern = path_pattern.replace(f"<{variable}>", f"<{variable}__{i}>", 1)
            if f"<{variable}>" not in path_pattern:
                break
        re_pattern = re.compile(path_pattern.replace("__pattern__", pattern))

        # Find each match
        values = set()
        for search_path in search_paths:
            match = re_pattern.search(str(search_path))
            if match:
                matches = set(match.groupdict().values())
                if len(matches) > 1:
                    log.warn(f"Found multiple values for {variable!r} in {search_path}: {', '.join(matches)}")
                values |= matches
        return values


def _log_file_open(file_path, description="", mode="r"):
    """Write a message to the log about a file being opened

    Args:
        file_path (Path/String):  The path to file being opened.
        description (String):     Description used for logging.
        mode (String):            Same as for the built-in open, usually 'r' or 'w'.
    """
    # Add space at end to handle empty descriptions
    description += " " if description else ""

    # Pick a log message based on the mode being used to open the file
    log_text = f"Read {description}from {file_path}"
    if "w" in mode:
        log_text = f"Write {description}to {file_path}"
        if file_path.is_file():
            log_text = f"Overwrite {description}on {file_path}"
    if "a" in mode:
        log_text = f"Append {description}to {file_path}"
    log.debug(log_text)
