"""Tests for the parsers-package

Tests for individual parsers are in their own files
"""

# Standard library imports
from datetime import datetime
import pathlib

# Third party imports
import pytest

# Midgard imports
from midgard import parsers
from midgard.parsers import Parser


@pytest.fixture
def tmpfile(tmpdir):
    """A temporary file that can be read"""
    file_path = tmpdir.join("test")
    file_path.write("Temporary test file")

    return file_path


#
# Tests
#
def test_list_of_parsers():
    """Test that names of parsers can be listed"""
    assert len(parsers.names()) > 0


# def test_calling_parser(tmpfile):
#     """Test that calling a parser returns a parser instance"""
#     parser_name = parsers.names()[0]
#     parser = parsers.parse_file(parser_name, file_path=tmpfile)
#     assert isinstance(parser, Parser)


@pytest.mark.skip(reason="Caching not yet implemented")
def test_caching_parser():
    """Test that caching results from parser works"""
    assert False


@pytest.mark.skip(reason="Caching not yet implemented")
def test_non_caching_parser():
    """Test that calling parser without caching results works"""
    assert False


def test_parser_vlbi_source_names():
    """Test that calling a parser on an example file gives expected output"""
    parser_name = "vlbi_source_names"
    example_path = pathlib.Path(__file__).parent / "example_files" / parser_name
    parser = parsers.parse_file(parser_name, example_path).as_dict()

    assert "2357-326" in parser
    assert len(parser) == 8
    assert parser["2357-326"]["icrf_name_short"] == "J0000-3221"


def test_parser_gnss_antex():
    """Test that calling a parser on an example file gives expected output"""
    parser_name = "gnss_antex"
    example_path = pathlib.Path(__file__).parent / "example_files" / parser_name
    parser = parsers.parse_file(parser_name, example_path).as_dict()

    assert len(parser) == 2
    assert "AERAT1675_120   SPKE" in parser
    assert "neu" in parser["AERAT1675_120   SPKE"]["G01"]

    assert "G01" in parser
    satellite_info = parser["G01"][datetime(1992, 11, 22)]
    assert satellite_info["G01"]["noazi"][0] == -.8
