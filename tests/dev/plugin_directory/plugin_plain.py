"""Module doc-string
"""

from midgard.dev import plugins


@plugins.register
def plugin_plain():
    """A plain plugin

    This is the plain docstring.
    """
    return "plain"
