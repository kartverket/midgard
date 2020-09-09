"""Tests for the dev.util-module

"""
# Standard library imports
import re

# Third party imports
import pytest

# Midgard imports
from midgard.dev import log
from midgard.dev import util


#
# Tests
#
# TODO: def test_check_help_and_version()
# TODO: def test_check_options()
# TODO: def test_get_program_info()
# TODO: def test_get_program_name()
# TODO: def test_no_traceback()
# TODO: def test_parse_args()
# TODO: def test_read_option_value()
# TODO: def test_write_requirements()


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_check_help_and_version():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_check_options():
    pass


def test_get_callers():
    """Test if `test_get_callers` function is included."""
    assert re.search("midgard.tests.dev.test_util.test_get_callers", util.get_callers())


def test_get_pid_and_server():
    """Test if process ID is a number and `@`-sign is included."""
    assert re.match("^[0-9]+@[a-zA-Z0-9_]+", util.get_pid_and_server())


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_get_program_info():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_get_program_name():
    pass


def test_get_python_version():
    """Test if Python executable name includes alphanumerical characters and Python version numbers"""
    assert re.match("^[a-zA-Z0-9_]+, version [0-9.]+", util.get_python_version())


def test_not_implemented(capsys):
    """Test if fatal logging message is correct."""
    # TODO: line number should also be tested.
    # Initialize logging
    log.init(log_level="fatal")

    # Run dummy() function by capturing fatal error message
    def dummy():
        util.not_implemented()

    dummy()
    _, stderr = capsys.readouterr()

    assert re.search("FATAL Function dummy()", stderr) and re.search("midgard/tests/dev/test_util.py", stderr)


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_no_traceback():
    pass


def test_options2args():
    """Test if list with arguments are converted correctly to `args` and `kwargs`"""
    args, kwargs = util.options2args(["--arg1", "-arg2", "--arg3=10"])
    assert all(["--arg1" in args, "-arg2" in args, "arg3" in kwargs.keys()])


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parse_args():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_read_option_value():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_write_requirements():
    pass


#
# Test of auxiliary functions
#
# TODO: def test__next_argument()
# TODO: def test__parse_date()
# TODO: def test__parse_doy()
# TODO: def test__parse_float()
# TODO: def test__parse_int()
@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test__next_argument():
    pass


def test__get_doc():
    """Test if docstring is a string with length greater than 0."""
    docstring = util._get_doc("midgard")
    assert isinstance(docstring, str) and len(docstring) > 0


def test__get_program_version():
    """Test if program version is a string with numbers."""
    version = util._get_program_version("midgard")
    assert isinstance(version, str) and re.search("[0-9]", version)


def test__print_version(capsys):
    """Test if printed program version is a string with numbers."""
    util._print_version("midgard")
    version, _ = capsys.readouterr()
    assert isinstance(version, str) and re.search("[0-9]", version)


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test__parse_date():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test__parse_doy():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test__parse_float():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test__parse_int():
    pass
