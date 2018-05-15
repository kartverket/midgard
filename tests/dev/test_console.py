"""Tests for the dev.console-module

"""
# System library imports
from textwrap import dedent

# Third party imports
import pytest

# Midgard imports
from midgard.dev import console


#
# Test data sets
#
@pytest.fixture
def two_words():
    """A two words text with newlines"""
    return "Short text"


@pytest.fixture
def one_sentence():
    """A one sentence text without newlines"""
    return "Lorem ipsum dolor sit amet, consectetur adipiscing elit."


@pytest.fixture
def one_paragraph_width_80():
    """A one paragraph text with newlines, each line wrapped at 80 characters"""
    return dedent("""
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer condimentum,
        orci at auctor venenatis, dolor orci congue felis, sit amet luctus dolor est in
        felis. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per
        inceptos himenaeos. Ut imperdiet ex sit amet lacinia condimentum. Integer
        aliquam, ligula nec ornare lobortis, urna mi mollis diam, id ultrices lorem
        risus at est. Morbi eu eros ac lorem auctor ultricies nec eu metus. Sed
        ullamcorper erat eget sollicitudin mollis. Sed vehicula orci tincidunt turpis
        rutrum, efficitur dapibus eros mollis. Sed id aliquet justo. Etiam sem justo,
        commodo in vehicula id, maximus id magna. Donec neque quam, vulputate non ex sit
        amet, consectetur finibus purus. Curabitur urna magna, tempus vel porta eu,
        semper malesuada odio.""").strip()


#
# Tests
#
def test_console_height_is_positive():
    """Test that number of lines in the console is positive"""
    assert console.lines() > 0


def test_console_width_is_positive():
    """Test that number of columns in the console is positive"""
    assert console.columns() > 0


def test_fill_short_is_same(two_words):
    """Test that when a short text is filled, the same text is returned (without newline)"""
    filled_text = console.fill(two_words, width=len(two_words) * 2)
    assert filled_text == two_words


def test_fill_one_paragraph(one_paragraph_width_80):
    """Test that one paragraph is filled correctly"""
    non_filled_text = one_paragraph_width_80.replace("\n", " ")
    filled_text = console.fill(non_filled_text, width=80)
    assert filled_text == one_paragraph_width_80


def test_hanging_indent(one_sentence):
    """Test that hanging indents work as expected"""
    width = len(one_sentence) // 2  # Should force fill to three lines
    filled_text = console.fill(one_sentence, width=width, hanging=4)
    num_lines = filled_text.count("\n") + 1
    assert filled_text.count("\n     ") == 0  # 5 spaces indent
    assert filled_text.count("\n    ") == num_lines - 1  # 4 spaces indent
