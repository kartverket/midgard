"""Simpler dealing with the console

Description:
------------

Utilities for using the console. Mainly wrappers around other libraries to make them easier and more intuitive to use.

Size of console: The two functions `lines()` and `columns()` report the current size of the console.

Textwrapping: The function `fill()` can be used to rewrap a text-string so that it fits inside the console.



Examples:
---------

    >>> from midgard.dev import console
    >>> console.columns()  # doctest: +SKIP
    86

    >>> print(console.fill(a_very_long_string))  # doctest: +SKIP
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras tempus eleifend feugiat.
    Maecenas vitae posuere metus. Sed sit amet fermentum velit. Aenean vitae turpis at
    risus sollicitudin fringilla in in nisi. Maecenas vitae ante libero. Aenean ut eros
    consequat, ornare erat at, tempus arcu. Suspendisse velit leo, eleifend eget mi non,
    vehicula ultricies erat. Vestibulum id nisi eget nisl venenatis dignissim. Duis cursus
    quam dui, vel hendrerit nibh lacinia id.

    >>> print(console.color.Fore.YELLOW + console.color.Back.BLUE + 'I am YELLOW text on BLUE backdrop!')  # doctest: +SKIP
    I am YELLOW text on a BLUE background!

"""

# Standard library imports
import colorama
import shutil
import textwrap
from typing import Any, Optional


colorama.init(autoreset=True)


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
        text:     Text that will be wrapped.
        width:    The maximum width (in characters) of wrapped lines.
        hanging:  Number of characters used for hanging indent.
        tw_args:  Arguments passed on to `textwrap.fill`.

    Returns:
        Wrapped string.
    """
    width = columns() if width is None else width
    if hanging is not None:
        tw_args.setdefault("initial_indent", "")
        tw_args.setdefault("subsequent_indent", " " * hanging)

    return textwrap.fill(text, width=width, **tw_args)


def dedent(text: str, num_spaces: Optional[int] = None) -> str:
    """Wrapper around textwrap.dedent

    Dedents at most num_spaces. If num_spaces is not specified, dedents as much as possible.

    Args:
        text:        Text that will be dedented.
        num_spaces:  Number of spaces that will be used for dedentation.

    Returns:
        Dedented string.
    """
    # Dedent the text all the way
    dedented_text = textwrap.dedent(text)
    if num_spaces is None:
        return dedented_text

    # Indent it back if necessary
    num_indents = (num_leading_spaces(text) - num_leading_spaces(dedented_text)) - num_spaces
    if num_indents > 0:
        return indent(dedented_text, num_spaces=num_indents)
    else:
        return dedented_text


def indent(text: str, num_spaces: int, **tw_args: Any) -> str:
    """Wrapper around textwrap.indent

    The `tw_args` are passed on to textwrap.indent.

    Args:
        text:        Text that will be indented.
        num_spaces:  Number of spaces that will be used for indentation.

    Returns:
        Indented string.
    """
    tw_args["prefix"] = " " * num_spaces
    return textwrap.indent(text, **tw_args)


def num_leading_spaces(text: str, space_char: str = " ") -> int:
    """Count number of leading spaces in a string

    Args:
        text:        String to count.
        space_char:  Which characters count as spaces.

    Returns:
        Number of leading spaces.
    """
    return len(text) - len(text.lstrip(space_char))


def progress_bar(iteration: int, total: int, prefix: str = ""):
    """
    Call in a loop to create terminal progress bar

    Args:
        iteration    current iteration
        total        total iterations
        prefix       prefix string
    """
    progress = iteration / total
    limit = int(progress * 10) - int((iteration - 1) / total * 10)
    if limit != 0:
        # Only print results for each 10 percent to avoid too much computational overhead
        text = f" {prefix} [{'#'*int(progress*10)}] {progress:.2%}"
        width = len(prefix) + 20
        print(f"{text:<{width}}", end="\r")

    if iteration == total:
        print(f" ", end="\r")
