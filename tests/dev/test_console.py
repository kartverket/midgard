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
def text(request):
    return request.getfixturevalue(request.param.__name__)


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
    return dedent(
        """
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
        semper malesuada odio."""
    ).strip()


@pytest.fixture()
def one_paragraph_ragged_left():
    """A one paragraph text with a ragged left margin"""
    return dedent(
        """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
               Integer condimentum, orci at auctor venenatis, dolor
            orci congue felis, sit amet luctus dolor est in felis.
        Class aptent taciti sociosqu ad litora torquent per conubia nostra, per
              inceptos himenaeos. Ut imperdiet ex sit amet lacinia condimentum."""
    ).strip()


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


@pytest.mark.parametrize("text", (one_sentence, one_paragraph_width_80, one_paragraph_ragged_left), indirect=True)
def test_hanging_indent(text):
    """Test that hanging indents work as expected"""
    width = len(text) // 2  # Should force fill to three lines
    filled_text = console.fill(text, width=width, hanging=4)
    num_lines = filled_text.count("\n") + 1
    assert filled_text.count("\n     ") == 0  # 5 spaces indent
    assert filled_text.count("\n    ") == num_lines - 1  # 4 spaces indent


@pytest.mark.parametrize("text", (one_sentence, one_paragraph_width_80, one_paragraph_ragged_left), indirect=True)
def test_dedent(text):
    """Test that dedentation works, indent first so that there are some spaces to dedent"""
    dedented_text = "\n" + console.dedent(console.indent(text, 8), num_spaces=3)
    num_lines = dedented_text.count("\n")
    assert dedented_text.count("\n      ") == text.count("\n ")  # 6 spaces indent
    assert dedented_text.count("\n     ") == num_lines  # 5 spaces indent


def test_dedent_too_much(one_paragraph_ragged_left):
    """If dedenting more than existing spaces, only dedent existing spaces"""
    dedented_text = console.dedent(console.indent(one_paragraph_ragged_left, 2), num_spaces=4)
    assert dedented_text == one_paragraph_ragged_left


def test_dedent_all(one_paragraph_ragged_left):
    """If not specifying num_spaces, dedent all the way"""
    dedented_text = console.dedent(console.indent(one_paragraph_ragged_left, 7))
    assert dedented_text == one_paragraph_ragged_left


@pytest.mark.parametrize("text", (one_sentence, one_paragraph_width_80, one_paragraph_ragged_left), indirect=True)
def test_indent(text):
    """Test that indentation works"""
    indented_text = "\n" + console.indent(text, num_spaces=3)
    num_lines = indented_text.count("\n")
    assert indented_text.count("\n    ") == text.count("\n ")  # 4 spaces indent
    assert indented_text.count("\n   ") == num_lines  # 3 spaces indent
