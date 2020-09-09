"""Framework for parsers

Description:
------------

To add a new parser, simply create a new .py-file which defines a class
inheriting from parsers.Parser. The class needs to be decorated with the
`midgard.dev.plugins.register` decorator as follows:

    from midgard.parsers import parser
    from midgard.lib import plugins

    @plugins.register
    class MyNewParser(parser.Parser):
        ...

To use a parser, you will typically use the `parse_file`-function defined below

    from midgard import parsers
    my_new_parser = parsers.parse_file('my_new_parser', 'file_name.txt', ...)
    my_data = my_new_parser.as_dict()

The name used in `parse_file` to call the parser is the name of the module
(file) containing the parser.
"""

# Standard library imports
import pathlib
from typing import Any, Callable, List, Optional, Union

# Midgard imports
from midgard.dev import plugins
from midgard.dev.timer import Timer

# Make base Parser-classes available at package level
from midgard.parsers._parser import Parser  # noqa
from midgard.parsers._parser_chain import ParserDef, ChainParser  # noqa
from midgard.parsers._parser_line import LineParser  # noqa
from midgard.parsers._parser_rinex import RinexParser, RinexHeader  # noqa
from midgard.parsers._parser_sinex import SinexParser, SinexBlock, SinexField  # noqa


def parse_file(
    parser_name: str,
    file_path: Union[str, pathlib.Path],
    encoding: Optional[str] = None,
    timer_logger: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    **parser_args: Any,
) -> Parser:
    """Use the given parser on a file and return parsed data

    Specify `parser_name` and `file_path` to the file that should be parsed. The following parsers are available:

    {doc_parser_names}

    Data can be retrieved either as Dictionaries, Pandas DataFrames or Midgard Datasets by using one of the methods
    `as_dict`, `as_dataframe` or `as_dataset`.

    Example:

        >>> df = parse_file('rinex2_obs', 'ande3160.16o').as_dataframe()  # doctest: +SKIP

    Args:
        parser_name:    Name of parser
        file_path:      Path to file that should be parsed.
        encoding:       Encoding in file that is parsed.
        timer_logger:   Logging function that will be used to log timing information.
        use_cache:      Whether to use a cache to avoid parsing the same file several times. (TODO: implement this)
        parser_args:    Input arguments to the parser

    Returns:
        Parser:  Parser with the parsed data
    """
    # TODO: Cache

    # Create the parser and parse the data
    parser = plugins.call(
        package_name=__name__, plugin_name=parser_name, file_path=file_path, encoding=encoding, **parser_args
    )
    if parser.data_available:
        with Timer(f"Finish {parser_name} ({__name__}) - {file_path} in", logger=timer_logger):
            parser.parse()
    return parser


def names() -> List[str]:
    """List the names of the available parsers

    Returns:
        Names of the available parsers
    """
    return plugins.names(package_name=__name__)
