"""Midgard library module for handling dependencies

Description:
------------

Stores a list of files with a hash/checksum or a timestamp that can be used to detect if a file changes.

Two strategies are available:

- Timestamps: Fast, but not always reliable as timestamps may update without the file actually changing.
- md5 hash/checksum: Slower, since it needs to read through the whole file, but will reliably only trigger when a file
  has changed.
"""

# Standard library imports
import atexit
from datetime import datetime
import hashlib
import pathlib
import re
from typing import Any, Dict, List, Optional, Union

# Midgard imports
from midgard.config.config import Configuration
from midgard.dev import log

# Variables describing current dependency file
_DEPENDENCY_CACHE: Dict[str, Any] = dict()
_CURRENT_DEPENDENCIES: Dict[str, Dict[str, str]] = dict()


def init(file_path: Union[str, pathlib.Path], fast_check: bool = True) -> None:
    """Start a clean list of dependencies

    The file_path is to the file in which dependencies are stored. This is
    cached, so after init() is run, the other functions do not need to specify
    the file_path.

    Args:
        file_path:   Path to dependency file.
        fast_check:  Fast check uses timestamps, slow check uses md5 checksums.
    """
    file_path = pathlib.Path(file_path)

    # Store current dependencies to disk
    write()

    # Update and cache variables
    _DEPENDENCY_CACHE.clear()
    _DEPENDENCY_CACHE["file_path"] = file_path
    _DEPENDENCY_CACHE["fast_check"] = fast_check

    # Delete any existing dependency file
    try:
        file_path.unlink()
        log.debug(f"Removing old dependency file {file_path}")
    except FileNotFoundError:
        pass  # If dependency file does not exist, we don't do anything

    # Register _write in case program exits without writing all dependencies to disk
    atexit.register(_write)


def add(*file_paths: Union[str, pathlib.Path], label: str = "") -> None:
    """Add a list of files to the list of dependencies

    Records the current time stamp or md5 hash of the files specified by file
    paths, and stores as dependencies on the dependency file.

    Before adding dependencies, a call to `init()` has to be done, to set up
    where to store the dependencies.

    Args:
        file_paths:  List of file paths to add to the dependency file.
        label:       Optional label for dependencies.
    """
    # Ignore dependency if no dependency file has been set (init() has not been called)
    if not _DEPENDENCY_CACHE:
        return
    # Add or update dependency information
    fast_check = _DEPENDENCY_CACHE["fast_check"]
    for file_path in file_paths:
        if file_path is not None:
            file_info = _file_info(file_path, fast_check, label=label)
            _CURRENT_DEPENDENCIES[str(file_path)] = file_info
            log.debug(f"Adding dependency: {file_path} ({file_info['checksum']})")


def _file_info(file_path: Union[str, pathlib.Path], fast_check: bool, **info_args: str) -> Dict[str, str]:
    """Get file info for a file path

    The contents of the file info depends on whether we are doing a fast check or not.

    Args:
        file_path:   File path.
        fast_check:  Whether to do a fast check.
        info_args:   Optional arguments that will be added to file info.

    Returns:
        Dictionary with info about file.
    """
    file_info = dict(timestamp=get_timestamp(file_path))
    if fast_check:
        file_info["checksum"] = file_info["timestamp"]
    else:
        file_info["checksum"] = get_md5(file_path)

    file_info.update(info_args)
    return file_info


def write() -> None:
    """Write dependencies to file
    """
    atexit.unregister(_write)
    _write(write_as_crash=False)


def _write(write_as_crash: bool = True) -> None:
    """Write dependencies to file

    This function is called either when starting a new list of dependencies
    (with a call to `init`) or when the program exits (including with an
    error). If `write_as_crash` is True, a special dependency is stored that
    will force `changed` to return True. This will in particular make sure that
    a stage is rerun if it crashed the previous time it ran.

    Args:
        write_as_crash (Boolean):   Whether to note that the current dependendee crashed.
    """
    # Ignore dependency if no dependency path is set (init() has not been called)
    if not _DEPENDENCY_CACHE:
        return

    # Store timestamp of crash, this will also force the current stage to be rerun next time
    if write_as_crash:
        _CURRENT_DEPENDENCIES["CRASHED"] = _file_info("CRASHED", fast_check=True, checksum="CRASHED", label="CRASHED")

    # No need to open and close files if there are no dependencies to store
    if not _CURRENT_DEPENDENCIES:
        return

    # Open dependency file or start from a fresh configuration/dictionary
    dependencies = Configuration.read_from_file("dependecies", _DEPENDENCY_CACHE["file_path"])

    # Update dependency information and clear list of current dependencies
    for file_path, info in _CURRENT_DEPENDENCIES.items():
        dependencies.update_from_dict(info, section=file_path)

    _CURRENT_DEPENDENCIES.clear()

    # Write to dependency file
    dependencies.write_to_file(_DEPENDENCY_CACHE["file_path"])


def changed(file_path: Union[str, pathlib.Path], fast_check: bool = True) -> bool:
    """Check if the dependencies have changed

    Returns True if any of the files listed in the dependency file have
    changed, or if the dependency file itself does not exist.

    Args:
        file_path:   Path to dependency file.
        fast_check:  Fast check uses timestamps, slow check uses md5 checksums.

    Returns:
        True if any file has changed or if the dependecy file does not exist, False otherwise.
    """
    # Make sure dependency file exists
    file_path = pathlib.Path(file_path)
    if not file_path.exists():
        log.debug(f"Dependency file {file_path} does not exist")
        return True

    # Check if any dependencies have changed
    dependencies = Configuration.read_from_file("dependencies", file_path)
    for file_path in dependencies.section_names:
        previous_checksum = dependencies[file_path].checksum.str
        current_checksum = _file_info(file_path, fast_check=fast_check)["checksum"]
        if current_checksum != previous_checksum:
            log.debug(f"Dependency {file_path} changed from {previous_checksum} to {current_checksum}")
            return True

    return False


def get_paths_with_label(file_path: Union[str, pathlib.Path], label_pattern: str) -> List[pathlib.Path]:
    """Find all paths with the given label

    Args:
        file_path:      Path to dependency file.
        label_pattern:  String with label or regular expression (e.g. 'gnss_rinex_nav_[MGE]' or 'gnss_rinex_nav_.').

    Returns:
        List:  List of file paths.
    """
    label_re = re.compile(f"^{label_pattern}$")  # ^ and $ is used to match the whole string

    # Make sure dependency file exists
    file_path = pathlib.Path(file_path)
    if not file_path.exists():
        log.debug(f"Dependency file {file_path} does not exist")
        return []

    # Find dependencies with the given label
    dependencies = Configuration.read_from_file("dependencies", file_path)
    paths = list()
    for file_path in dependencies.section_names:
        label = dependencies[file_path].label.str
        if label_re.match(label):
            paths.append(pathlib.Path(file_path))
    return paths


def get_timestamp(file_path: Union[str, pathlib.Path]) -> str:
    """Return a textual timestamp from the modification date of a file

    Args:
        file_path:  Path to file.

    Returns:
        String representing the modification date of the file.
    """
    file_path = pathlib.Path(file_path)

    try:
        mod_time = file_path.stat().st_mtime
    except FileNotFoundError:
        return "File does not exist"

    return datetime.fromtimestamp(mod_time).isoformat()


def get_md5(file_path: Union[str, pathlib.Path]) -> str:
    """Return a md5 checksum based on a file.

    Args:
        file_path: Path to file.

    Returns:
        Hex-string representing the contents of the file.
    """
    md5 = hashlib.md5()
    block_size = 128 * md5.block_size  # Chunk file to avoid memory problems

    try:
        with open(file_path, mode="rb") as fid:
            for chunk in iter(lambda: fid.read(block_size), b""):
                md5.update(chunk)
        return md5.hexdigest()
    except FileNotFoundError:
        return "File does not exist"
