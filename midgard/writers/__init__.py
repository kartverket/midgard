"""Framework for writing output in different formats

Description:
------------

Each output format / output destination should be defined in a separate .py-file. The function inside the .py-file that
should be called need to be decorated with the :func:`~midgard.dev.plugins.register` decorator as follows::

    from midgard.dev import plugins

    @plugins.register
    def write_as_fancy_format(arg_1, arg_2):
        ...

"""
# Standard library imports
from typing import Any, List

# Midgard imports
from midgard.dev import plugins


def names() -> List[str]:
    """List the names of the available writers

    Returns:
        List of strings with the names of the available writers.
    """
    return plugins.names(package_name=__name__)


def write(writer: str, **writer_args: Any) -> None:
    """Call one writer

    Args:
        writer:       Name of writer.
        writer_args:  Arguments passed on to writer.
    """
    plugins.call(package_name=__name__, plugin_name=writer, **writer_args)
