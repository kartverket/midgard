"""Simpler dealing with the console

Description:
------------

Utilities for using the console. Mainly wrappers around other libraries to make them easier and more intuitive to use.

Size of console: The two functions `lines()` and `columns()` report the current size of the console.

Textwrapping: The function `fill()` can be used to rewrap a text-string so that it fits inside the console.

Color: The sub-module `color` can be used to set the foreground and background colors. Note that the color
functionality depends on the external package `colorama`. If `colorama` is not installed, color gracefully falls back
to not showing any color.

Examples:
---------

>>> from midgard.lib import console
>>> print(console.columns())
86
>>> print(console.fill(a_very_long_string))
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras tempus eleifend feugiat.
Maecenas vitae posuere metus. Sed sit amet fermentum velit. Aenean vitae turpis at
risus sollicitudin fringilla in in nisi. Maecenas vitae ante libero. Aenean ut eros
consequat, ornare erat at, tempus arcu. Suspendisse velit leo, eleifend eget mi non,
vehicula ultricies erat. Vestibulum id nisi eget nisl venenatis dignissim. Duis cursus
quam dui, vel hendrerit nibh lacinia id.
>>> print(console.color.Fore.YELLOW + console.color.Back.BLUE + 'I am YELLOW text on a BLUE background!')
I am YELLOW text on a BLUE background!

"""

# Standard library imports
import shutil
import textwrap
from typing import Any, Optional

# Midgard imports
from midgard.dev import optional

# Use colorama for coloring in the console, graceful fallback to no color if colorama is not installed
_empty_string = optional.EmptyStringMock("_empty_string")
color = optional.optional_import(
    "colorama", attrs=dict(init=lambda **_: None, Back=_empty_string, Fore=_empty_string, Style=_empty_string)
)
color.init(autoreset=True)


def lines() -> int:
    """The height of the console

    Returns:
        The heigth of the console in characters.
    """
    return shutil.get_terminal_size().lines


def columns() -> int:
    """The width of the console

    Returns:
        The width of the console in characters.
    """
    return shutil.get_terminal_size().columns


def fill(text: str, *, width: Optional[int] = None, hanging: Optional[int] = None, **tw_args: Any) -> str:
    """Wrapper around textwrap.fill

    The `tw_args` are passed on to textwrap.fill. See textwrap.TextWrapper for available keyword arguments.

    The default value for `width` is console.columns(), while the new argument `hanging`, if defined, will try
    to set (although not override) the textwrap-arguments `initial_indent` and `subsequent_indent` to create a hanging
    indent (no indent on the first line) of `hanging` spaces.

    Args:
        text (String):            Text that will be wrapped.
        width (Integer):          The maximum width (in characters) of wrapped lines.
        hanging (Integer): Number of characters used for hanging indent.
        tw_args:                  Arguments passed on to `textwrap.fill`.

    Returns:
        String: Wrapped string.

    """
    width = columns() if width is None else width
    if hanging is not None:
        tw_args.setdefault("initial_indent", "")
        tw_args.setdefault("subsequent_indent", " " * hanging)

    return textwrap.fill(text, width=width, **tw_args)
