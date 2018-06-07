"""Tests for the collections.enums-module

"""
# System library imports
import enum

# Third party imports
import pytest

# Midgard imports
from midgard.collections import enums
from midgard.dev import exceptions


#
# Test data
#
@enums.register_enum("my_enum")
class MyEnum(enum.Enum):
    """Enum used for testing"""

    value_1 = 1
    value_2 = "two"


class NonRegisteredEnum(enum.Enum):
    """Non-registered Enum used for testing"""

    nothing = None


#
# Tests
#
def test_registering_enum_to_list():
    """Test that registering an enum puts name in list, but does not alter enum"""
    enum_name = "my_new_enum"
    list_before = set(enums.enums())
    enums.register_enum(enum_name)(NonRegisteredEnum)
    list_after = set(enums.enums())
    assert (list_after - list_before) == {enum_name}


def test_registering_enum_dont_alter():
    """Test that registering an enum does not alter it"""
    enum_name = "my_new_enum"
    enums.register_enum(enum_name)(NonRegisteredEnum)
    assert enums.get_enum(enum_name) is NonRegisteredEnum


def test_enum_list_not_empty():
    """Test that list of enums finds some registered enums"""
    enum_list = enums.enums()
    assert len(enum_list) > 0


def test_known_enum_in_list():
    """Test that 'my_enum' is in list of enums"""
    enum_list = enums.enums()
    assert "my_enum" in enum_list


def test_getting_known_enum():
    """Test that getting 'my_enum' returns MyEnum"""
    my_enum = enums.get_enum("my_enum")
    assert my_enum is MyEnum


def test_getting_non_existing_enum():
    """Test that getting a non-existing enum raises appropriate error"""
    with pytest.raises(exceptions.UnknownEnumError):
        enums.get_enum("non_existing")


def test_getting_value_1():
    """Test that getting the value_1 from MyEnum returns the expected value"""
    value_1 = enums.get_value("my_enum", "value_1")
    assert value_1 == MyEnum.value_1


def test_getting_value_2():
    """Test that getting the value_2 from MyEnum returns the expected value"""
    value_2 = enums.get_value("my_enum", "value_2")
    assert value_2 == MyEnum.value_2


def test_getting_non_existing_value():
    """Test that getting a non-existing value raises apprioate error"""
    with pytest.raises(ValueError):
        enums.get_value("my_enum", "non_existing")
