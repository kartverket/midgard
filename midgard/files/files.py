"""Utilities for working with files

"""
# Standard library imports
import builtins
from contextlib import contextmanager
import gzip
import pathlib
from typing import Any, Iterator, Optional, Union


@contextmanager
def open(
    file_path: Union[str, pathlib.Path],
    create_dirs: bool = False,
    open_as_gzip: Optional[bool] = None,
    **open_args: Any
) -> Iterator:
    """Open a file.

    Can automatically create the necessary directories before writing to a file, as well as handle gzipped files.

    With `open_as_gzip` set to None (default), it will try to detect whether the path is a .gz file simply by looking
    at the path suffix. For more control, you can set the parameter to True or False explicitly.

    Args:
        file_path:     String or pathlib.Path representing the full file path.
        create_dirs:   True or False, if True missing directories are created.
        open_as_gzip:  Use gzip library to open file.
        open_args:     All keyword arguments are passed on to the built-in open.

    Returns:
        File object representing the file.
    """
    file_path = pathlib.Path(file_path).resolve()

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    # Simple detection of .gz-files
    if open_as_gzip is None:
        open_as_gzip = file_path.suffix == ".gz"

    open_func = gzip.open if open_as_gzip else builtins.open

    try:
        with open_func(file_path, **open_args) as fid:
            yield fid
    except Exception:
        raise


def move(from_path: Union[str, pathlib.Path], to_path: Union[str, pathlib.Path], overwrite: bool = True) -> None:
    """Move a file to another path

    With overwrite set to True, to_path may already exist and will be overwritten without warning. Setting overwrite to
    False will raise a FileExistsError if to_path already exists.

    Args:
        from_path:  Path of file to be moved.
        to_path:    Path file will be moved to.
        overwrite:  If True, to_path may already exist. If False, to_path will never be overwritten.
    """
    from_path = pathlib.Path(from_path)
    to_path = pathlib.Path(to_path)

    # Create directories if necessary
    to_path.parent.mkdir(parents=True, exist_ok=True)

    # Be careful not to overwrite destination if overwrite is False
    if overwrite:  # No worries
        from_path.replace(to_path)

    else:  # Be careful, see https://realpython.com/python-pathlib/#moving-and-deleting-files
        with to_path.open(mode="xb") as fid:
            fid.write(from_path.read_bytes())
        from_path.unlink()
