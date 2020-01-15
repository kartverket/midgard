"""Tests for the config.config-module

"""
# System library imports
from collections import namedtuple
from datetime import date, datetime
import pathlib
import re
import sys

# Third party imports
import pytest

# Midgard imports
from midgard.config import config
from midgard.collections import enums
from midgard.dev import exceptions


#
# Helper functions
#
EntryTestCase = namedtuple("EntryTestCase", ("type", "cfg_value", "value"))


def normalize_whitespace(string):
    """Normalize whitespace in string

    Deletes consecutive spaces and newlines
    """
    return re.sub("\n+", "\n", re.sub(" +", " ", string))


def only_word_characters(string):
    """Filter out only word characters from the string"""
    return re.sub("\W", "", string)


#
# Test configuration
#
@pytest.fixture
def config_file():
    """A test configuration read from file"""
    cfg = config.Configuration("file")
    cfg_path = pathlib.Path(__file__).parent / "test_config.conf"
    cfg.update_from_file(cfg_path)
    cfg_vars = dict(var_1="one", var_2="two")
    cfg.update_vars(cfg_vars)
    return cfg


@pytest.fixture
def config_options():
    """A test configuration based on (mocked) command line options"""
    cfg = config.Configuration("options")
    cfg_argv = [
        sys.argv[0],
        "not_an_option",
        "--section_1:foo=bar",
        "--section_1:pi=3.14",
        "--section_2:foo=baz",
        "--just_a_flag",
        "--non_existing_config:section_1:foo=none",
        "--options:section_3:name=options",
        "--section_1:pi=3.1415",
    ]
    remember_sys_argv, sys.argv = sys.argv, cfg_argv
    cfg.update_from_options(allow_new=True)
    sys.argv = remember_sys_argv
    return cfg


@pytest.fixture
def config_dict(gps_dict):
    """A test configuration based on a dictionary"""
    cfg = config.Configuration("dictionary")
    cfg.update_from_dict(gps_dict, section="gps")
    return cfg


@pytest.fixture
def gps_dict():
    """A dictionary with GPS test data"""
    return dict(gps_f1=1575.42, gps_f2=1227.60, gps_f5=1176.45, gps_name="Global Positioning System")


@pytest.fixture
def config_section(config_dict):
    """A section with test data"""
    return config_dict.gps


#
# Tests
#
def test_read_config_from_file(config_file):
    """Test that reading a configuration from file works"""
    assert len(config_file.sections) > 0
    assert len(config_file.sources) == 1
    assert list(config_file.sources)[0].endswith("test_config.conf")


def test_read_config_from_file_classmethod(config_file):
    """Test that reading a configuration from file works using the classmethod"""
    cfg_path = pathlib.Path(__file__).parent / "test_config.conf"
    cfg = config.Configuration.read_from_file("test", cfg_path)
    assert cfg.as_str() == config_file.as_str()


@pytest.mark.skip(reason="as_str() does not print profiles correctly")
def test_write_config_to_file(config_file, tmpdir):
    """Test that writing a configuration creates a file that is identical to the original"""
    cfg_path = pathlib.Path("".join(config_file.sources))
    out_path = pathlib.Path(tmpdir / "test_config.conf")
    config_file.write_to_file(out_path)

    assert normalize_whitespace(cfg_path.read_text()) == normalize_whitespace(out_path.read_text())


def test_read_config_from_dict(config_dict):
    """Test that reading a configuration from a dict works"""
    assert len(config_dict.sections) > 0
    assert len(config_dict.sources) == 1
    assert list(config_dict.sources)[0] == "dictionary"


def test_read_config_from_options(config_options):
    """Test that reading a configuration from a options works"""
    assert len(config_options.sections) > 0
    assert len(config_options.sources) > 0
    assert all(s.startswith("command line") for s in config_options.sources)


def test_update_config_from_config_section(config_file, config_options):
    """Test that a config section can be copied"""
    assert "section_1" not in config_file.section_names
    config_file.update_from_config_section(config_options.section_1)
    assert "section_1" in config_file.section_names
    assert str(config_file.section_1) == str(config_options.section_1)


def test_update_config_from_options(config_file):
    """Test that a config can be updated from command line options"""
    config_file.master_section = "midgard"
    sections_before = set(config_file.section_names)
    entries_before = set(config_file.midgard.as_list())
    cfg_argv = [
        sys.argv[0],
        "not_an_option",
        "--foo=I am an option",
        "--midgard:pi=4",
        "--new_key=new value",
        "--new_section:pi=3.14",
        "--just_a_flag",
        "--non_existing_config:midgard:foo=none",
        "--file:midgard:spam=more ham",
    ]
    remember_sys_argv, sys.argv = sys.argv, cfg_argv
    config_file.update_from_options(allow_new=True)
    sys.argv = remember_sys_argv

    assert set(config_file.section_names) - sections_before == {"new_section"}
    assert set(config_file.midgard.as_list()) - entries_before == {"new_key"}
    assert config_file.midgard.foo.str == "I am an option"
    assert config_file.midgard.pi.str == "4"
    assert config_file.midgard.spam.str == "more ham"
    assert config_file.midgard.foo.source == "command line (--foo=I am an option)"


def test_clearing_config(config_file):
    """Test that clearing a configuration works"""
    config_file.clear()
    assert len(config_file.sections) == 0


def test_set_non_existing_master_section(config_file):
    """Test that setting a non-existing section is ok, but getting from it raises an error"""
    config_file.master_section = "non_existing"
    with pytest.raises(exceptions.MissingSectionError):
        config_file.non_exisiting


def test_access_from_master_section(config_file):
    """Test that accessing entry from master section can be done without referencing section"""
    config_file.master_section = "midgard"
    assert config_file.foo is config_file.midgard.foo


def test_access_with_master_section(config_file):
    """Test accessing an entry that is not in the master section"""
    config_file.master_section = "midgard"
    assert config_file.profile_test.technique.str == "none"


def test_get_from_master_section_without_master_section(config_file):
    """Test that trying to get an entry as if from a master section typically raises an error"""
    with pytest.raises(exceptions.MissingSectionError):
        config_file.foo


def test_get_from_master_section(config_file):
    """Test that get can access entries from a master section"""
    config_file.master_section = "midgard"
    entry = config_file.get("foo", default="baz")
    assert entry is config_file.midgard.foo


def test_profiles_are_not_separate_sections(config_file):
    """Test that profiles are not registered as separate sections"""
    assert len([s for s in config_file.section_names if s.startswith("profile_test")]) == 1


def test_profiles_are_prioritized(config_file):
    """Test that values are taken from the correct profiles, when giving a list of profiles to use"""
    config_file.profiles = ["sisre", "vlbi", None]
    assert config_file.profile_test.technique.str == "gnss"  # from profile sisre
    assert config_file.profile_test.spam.str == "bam"  # from profile vlbi
    assert config_file.profile_test.foo.str == "baz"  # from default profile


def test_automatic_default_profile(config_file):
    """Test that default profile is included automatically"""
    config_file.profiles = ["sisre", "vlbi"]
    assert config_file.profiles == ["sisre", "vlbi", None]


def test_set_non_existing_profiles(config_file):
    """Test that non-existing profiles are ignored (no error)"""
    config_file.profiles = ["non_existing", None]
    assert config_file.profile_test.technique.str == "none"  # from default profile


def test_using_only_default_profile(config_file):
    """Test that default profile can be set simply by assigning None"""
    config_file.profiles = None
    assert config_file.profiles == [None]
    assert config_file.profile_test.technique.str == "none"  # from default profile


def test_get_with_override_value(config_file):
    """Test that get with override value returns override value"""
    entry = config_file.get("foo", section="midgard", value="override")
    assert isinstance(entry, config.ConfigurationEntry)
    assert entry.str == "override"
    assert entry.source == "method call"


def test_get_with_default_value_and_non_existing_section(config_file):
    """Test that get returns default value when nothing is found in configuration"""
    entry = config_file.get("foo", section="non_existing", default="default")
    assert isinstance(entry, config.ConfigurationEntry)
    assert entry.str == "default"
    assert entry.source == "default value"


def test_get_with_default_value_and_non_existing_entry(config_file):
    """Test that get returns default value when nothing is found in configuration"""
    entry = config_file.get("non_existing", section="midgard", default="default")
    assert isinstance(entry, config.ConfigurationEntry)
    assert entry.str == "default"
    assert entry.source == "default value"


def test_get_without_default_value_and_non_existing_section(config_file):
    """Test that get raises error when nothing is found in configuration and no default value is given"""
    with pytest.raises(exceptions.MissingSectionError):
        config_file.get("foo", section="non_existing")


def test_get_without_default_value_and_non_existing_entry(config_file):
    """Test that get raises error when nothing is found in configuration and no default value is given"""
    with pytest.raises(exceptions.MissingEntryError):
        config_file.get("non_existing", section="midgard")


def test_get_from_configuration(config_file):
    """Test that get returns the same entry as regular attribute access"""
    entry = config_file.get("foo", section="midgard", default="baz")
    assert entry is config_file.midgard.foo


def test_get_from_fallback_config(config_file, config_dict):
    """Test that get can access entries in a fallback configuration"""
    config_dict.fallback_config = config_file
    entry = config_dict.get("foo", section="midgard", default="baz")
    assert entry is config_file.midgard.foo


def test_exists_with_section(config_file):
    """Test that exists works for both existing and non-existing keys"""
    assert config_file.exists("foo", section="midgard")
    assert not config_file.exists("does_not_exist", section="midgard")
    assert not config_file.exists("foo", section="does_not_exist")


def test_exists_with_master_section(config_file):
    """Test that exists works for both existing and non-existing keys without specifying section"""
    config_file.master_section = "data_types"
    assert config_file.exists("str")
    assert not config_file.exists("does_not_exist")


def test_exists_with_master_section_defined(config_file):
    """Test that exists behaves correctly when master_section is defined and section specified"""
    config_file.master_section = "data_types"
    assert config_file.exists("foo", section="midgard")
    assert not config_file.exists("str", section="str")
    assert not config_file.exists("foo", section="does_not_exist")


def test_getattr_from_fallback_config(config_file, config_dict):
    """Test that attribute access can get entries in fallback configuration"""
    config_dict.fallback_config = config_file
    entry = config_dict.midgard.foo
    assert entry is config_file.midgard.foo


def test_getitem_from_fallback_config(config_file, config_dict):
    """Test that dictionary access can get entries in fallback configuration"""
    config_dict.fallback_config = config_file
    entry = config_dict["midgard"].foo
    assert entry is config_file.midgard.foo


def test_add_single_entry(config_file):
    """Test adding a single new entry"""
    sections_before = set(config_file.section_names)
    config_file.update("new_section", "new_key", "new_value", source="test")
    assert set(config_file.section_names) - sections_before == {"new_section"}
    assert config_file.new_section.new_key.str == "new_value"
    assert config_file.new_section.new_key.source == "test"


def test_updating_existing_entry(config_file):
    """Test updating the value of an existing entry"""
    sections_before = config_file.section_names
    config_file.update("midgard", "foo", "new_value", source="test", allow_new=False)
    assert config_file.section_names == sections_before
    assert config_file.midgard.foo.str == "new_value"
    assert config_file.midgard.foo.source == "test"


def test_updating_non_existing_section(config_file):
    """Test updating the value of an entry in a non-existing section"""
    with pytest.raises(exceptions.MissingSectionError):
        config_file.update("non_existing", "foo", "new_value", source="test", allow_new=False)


def test_updating_non_existing_entry(config_file):
    """Test updating the value of a non-existing entry"""
    with pytest.raises(exceptions.MissingEntryError):
        config_file.update("midgard", "non_existing", "new_value", source="test", allow_new=False)


@pytest.mark.skip(reason="as_str() does not print profiles correctly")
def test_configuration_as_string(config_file):
    """Test that configuration as string is similar to configuration file"""
    path = pathlib.Path(list(config_file.sources)[0])
    with open(path, mode="r") as fid:
        file_str = "".join(l for l in fid if not l.startswith("#"))

    assert normalize_whitespace(file_str) == normalize_whitespace(config_file.as_str())


@pytest.mark.skip(reason="str() does not print profiles correctly")
def test_string_representation_of_configuration(config_file):
    """Test that string representation is similar to configuration file"""
    path = pathlib.Path(list(config_file.sources)[0])
    with open(path, mode="r") as fid:
        file_str = "".join(l for l in fid if not l.startswith("#"))

    assert normalize_whitespace(file_str) == normalize_whitespace(str(config_file))


def test_configuration_as_dict(config_dict, gps_dict):
    """Test that dict representation gives back a sensible dictionary"""
    assert config_dict.as_dict(default_getter="str")["gps"] == {k: str(v) for k, v in gps_dict.items()}


def test_configuration_as_dict_with_getters(config_dict, gps_dict):
    """Test that dict representation gives back a sensible dictionary"""
    getters = {"gps": {k: type(v).__name__ for k, v in gps_dict.items()}}
    assert config_dict.as_dict(getters=getters)["gps"] == gps_dict


def test_attribute_and_item_access(config_file):
    """Test that the same sections are returned whether using attribute or item access"""
    assert config_file.midgard is config_file["midgard"]


def test_deleting_section_as_item(config_file):
    """Test that deleting a section removes it"""
    sections_before = set(config_file.section_names)
    del config_file["midgard"]
    assert sections_before - set(config_file.section_names) == {"midgard"}


def test_deleting_section_as_attribute(config_file):
    """Test that deleting a section removes it"""
    sections_before = set(config_file.section_names)
    del config_file.midgard
    assert sections_before - set(config_file.section_names) == {"midgard"}


def test_dir_return_sections(config_file):
    """Test that sections are included in dir(configuration)"""
    cfg_dir = dir(config_file)
    sections = set(config_file.section_names)
    assert len(sections) > 0
    assert set(cfg_dir) & sections == sections


def test_dir_return_master_section(config_file):
    """Test that entries in master section are included in dir(configuration)"""
    config_file.master_section = "midgard"
    cfg_dir = dir(config_file)
    entries = set(config_file.midgard.as_list())
    assert len(entries) > 0
    assert set(cfg_dir) & entries == entries


def test_repr_of_configuration(config_file):
    """Test that repr of configuration is sensible"""
    assert repr(config_file) == "Configuration(name='file')"


def test_section_as_string(config_section, gps_dict):
    """Test that string representation of section looks reasonable"""
    assert only_word_characters(config_section.as_str()) == only_word_characters("gps" + str(gps_dict))


def test_section_as_list(config_section, gps_dict):
    """Test that the list representation of section equals list of keys"""
    assert config_section.as_list() == list(gps_dict.keys())


def test_section_as_dict(config_section, gps_dict):
    """Test that the dict representation of section equals original dict"""
    assert config_section.as_dict(default_getter="str") == {k: str(v) for k, v in gps_dict.items()}


def test_section_as_dict_with_getters(config_section, gps_dict):
    """Test that the dict representation of section equals original dict"""
    getters = {k: type(v).__name__ for k, v in gps_dict.items()}
    assert config_section.as_dict(getters=getters) == gps_dict


def test_dir_return_entries(config_section):
    """Test that entries are included in dir(section)"""
    cfg_dir = dir(config_section)
    entries = set(config_section.as_list())
    assert len(entries) > 0
    assert set(cfg_dir) & entries == entries


def test_repr_of_section(config_section):
    """Test that repr of section is sensible"""
    assert repr(config_section) == "ConfigurationSection(name='gps')"


entry_data = [
    EntryTestCase("str", "Curiouser and curiouser!", "Curiouser and curiouser!"),
    EntryTestCase("int", "42", 42),
    EntryTestCase("float", "3.14", 3.14),
    EntryTestCase("bool", "on", True),
    EntryTestCase("bool", "no", False),
    EntryTestCase("date", "2018-05-30", date(2018, 5, 30)),
    EntryTestCase("datetime", "2017-01-28 15:12:30", datetime(2017, 1, 28, 15, 12, 30)),
    EntryTestCase("path", "test_config.conf", pathlib.Path("test_config.conf")),
    EntryTestCase("list", "vlbi, slr, gnss, doris", ["vlbi", "slr", "gnss", "doris"]),
    EntryTestCase("tuple", "one two three", ("one", "two", "three")),
    EntryTestCase("dict", "one:en, two:to, three:tre", {"one": "en", "two": "to", "three": "tre"}),
]


@pytest.mark.parametrize("test_case", entry_data)
def test_access_entry(test_case):
    """Test getting values of entries through accessors"""
    entry = config.ConfigurationEntry("test", test_case.cfg_value)
    assert getattr(entry, test_case.type) == test_case.value
    assert getattr(entry, f"as_{test_case.type}")() == test_case.value


@pytest.mark.parametrize("test_case", entry_data)
def test_entry_is_used(test_case):
    """Test that entry is marked as used when accessing value"""
    entry = config.ConfigurationEntry("test", test_case.cfg_value)
    assert entry.is_used is False
    getattr(entry, test_case.type)
    assert entry.is_used is True


def test_access_enum():
    """Test getting the value of an entry as an enum (has no property access)"""
    entry = config.ConfigurationEntry("test", "info")
    assert entry.as_enum("log_level") is enums.get_value("log_level", "info")


def test_enum_is_used():
    """Test that entry is marked as used when accessed as enum"""
    entry = config.ConfigurationEntry("test", "info")
    assert entry.is_used is False
    entry.as_enum("log_level")
    assert entry.is_used is True


def test_entry_with_type(config_file):
    """Test that type hints of an entry can be accessed"""
    assert config_file.midgard.foo.type == "str"


def test_entry_with_help(config_file):
    """Test that help texts of an entry can be accessed"""
    assert config_file.midgard.foo.help == "How to foodazzle"


def test_metadata_of_entry(config_file):
    """Test that metadata of entry can be accessed"""
    assert len(config_file.midgard.foo.meta.keys()) > 0
    assert config_file.midgard.foo.meta["type"] is config_file.midgard.foo.type
    assert config_file.midgard.foo.meta["help"] is config_file.midgard.foo.help


def test_bool_of_entry():
    """Test the bool value of an entry"""
    entry = config.ConfigurationEntry("key", "value")
    assert entry


def test_bool_of_empty_entry():
    """Test that the bool value of an empty entry is False"""
    entry = config.ConfigurationEntry("empty", "")
    assert not entry


def test_repr_of_entry():
    """Test that the repr of an entry is sensible"""
    entry = config.ConfigurationEntry("key", "value")
    assert repr(entry) == "ConfigurationEntry(key='key', value='value')"
