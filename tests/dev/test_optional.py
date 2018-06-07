"""Tests for the dev.optional-module

"""
# System library imports
import sys

# Third party imports
import pytest

# Midgard imports
from midgard.dev import optional


#
# Test data sets
#
@pytest.fixture
def two_words():
    """A two words text with newlines"""
    return "Short text"


#
# Tests
#
def test_optional_import_of_existing_module():
    """Test that optional import of existing module returns module"""
    optional_sys = optional.optional_import("sys")
    assert optional_sys is sys.modules["sys"]


def test_optional_import_of_non_existing_module():
    """Test that optional import of non-existing module returns a SimpleMock"""
    non_existing = optional.optional_import("non_existing_module")
    assert isinstance(non_existing, optional.SimpleMock)


def test_non_existing_module_raises_error():
    """Test that a non-existing module raises an ImportError when used"""
    non_existing = optional.optional_import("non_existing_module")
    with pytest.raises(ImportError):
        non_existing.should_raise_error


def test_non_existing_module_raises_error_only_once():
    """Test that a non-existing module raises the ImportError only once"""
    non_existing = optional.optional_import("non_existing_module")
    try:
        non_existing.should_raise_error
    except ImportError:
        pass
    assert isinstance(non_existing.should_not_raise_error_anymore, optional.SimpleMock)


def test_non_existing_module_with_attrs():
    """Test that a non-existing module still returns given attributes"""
    attrs = {"one": 1, "pi": 3.14, "numbers": [1, 2, 3]}
    non_existing = optional.optional_import("non_existing_module", attrs=attrs)
    for attr, value in attrs.items():
        assert getattr(non_existing, attr) is value


def test_SimpleMock_repr():
    """Test that the SimpleMock returns a nice repr"""
    from midgard.dev.optional import SimpleMock  # noqa  Import SimpleMock to be able to use eval on the repr

    simple_mock_repr = "SimpleMock('nice_repr')"
    simple_mock = eval(simple_mock_repr)
    assert repr(simple_mock) == simple_mock_repr


def test_calling_a_SimpleMock_returns_itself():
    """Test that calling a SimpleMock returns itself"""
    simple_mock = optional.SimpleMock("time_to_call", raise_error=False)
    new_simple_mock = simple_mock()
    assert new_simple_mock is simple_mock


def test_attr_on_SimpleMock_is_consistent():
    """Test that asking for the same attribute twice returns the same object"""
    simple_mock = optional.SimpleMock("consistent", raise_error=False)
    attr_1st = simple_mock.read_attribute
    attr_2nd = simple_mock.read_attribute
    assert attr_1st is attr_2nd


def test_EmptyStringMock_returns_empty_string():
    """Test that the EmptyStringMock always returns the empty string"""
    empty_string = optional.EmptyStringMock("empty_string")
    assert empty_string.anything == ""
