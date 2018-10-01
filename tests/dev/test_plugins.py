"""Tests for the dev.plugins-module

"""
# Standard library imports
import pathlib

# Third party imports
import pytest

# Midgard imports
from midgard.dev import exceptions
from midgard.dev import plugins
from midgard.parsers._parser import Parser


@pytest.fixture
def tmpfile(tmpdir):
    """A temporary file that can be read"""
    file_path = tmpdir.join("test")
    file_path.write("Temporary test file")

    return file_path


@pytest.fixture
def plugin_package():
    """Name of the test plugin package"""
    plugins = pathlib.Path(__file__).parent / "plugin_directory"
    relative = plugins.relative_to(pathlib.Path.cwd())

    return ".".join(relative.parts)


#
# Tests
#
def test_package_not_empty(plugin_package):
    """Test that names() finds some plugins in package"""
    parsers = plugins.names(plugin_package)
    assert len(parsers) > 0


def test_package_empty():
    """Test that names() does not find any plugins in midgard.dev-package"""
    lib_plugins = plugins.names("midgard.dev")
    assert len(lib_plugins) == 0


def test_package_non_existing():
    """Test that a non-existent package raises an appropriate error"""
    with pytest.raises(exceptions.UnknownPackageError):
        plugins.names("midgard.non_existent")


def test_plugin_exists():
    """Test that an existing plugin returns True for exists()"""
    package_name = "midgard.parsers"
    plugin_name = plugins.names(package_name)[0]
    assert plugins.exists(package_name, plugin_name)


@pytest.mark.parametrize("plugin_name", ["exceptions", "non_existent"])
def test_plugin_not_exists(plugin_name):
    """Test that a non-existing plugin returns False for exists()

    Tests both for an existing module (midgard.dev.exceptions) and a non-existent module
    (midgard.dev.non_existent).
    """
    assert not plugins.exists("midgard.dev", plugin_name)


def test_call_existing_plugin(tmpfile):
    """Test that calling a parser-plugin works, and returns a Parser instance"""
    package_name = "midgard.parsers"
    plugin_name = plugins.names(package_name)[0]
    parser = plugins.call(package_name, plugin_name, file_path=tmpfile)
    assert isinstance(parser, Parser)


def test_call_non_existing_plugin():
    """Test that calling a non-existing plugin raises an error"""
    with pytest.raises(exceptions.UnknownPluginError):
        plugins.call("midgard.dev", "non_existent")


def test_load_plugin_with_prefix():
    """Test that a plugin can be called using a prefix"""
    package_name = "midgard.parsers"
    plugin_name = [p for p in plugins.names(package_name) if "_" in p][0]
    prefix, _, plugin = plugin_name.partition("_")

    expected_name = plugin_name
    assert plugins.load(package_name, plugin, prefix=prefix) == expected_name


def test_load_non_existing_plugin_with_prefix():
    """Test that calling a non-existing plugin fails also when using prefix"""
    with pytest.raises(exceptions.UnknownPluginError):
        plugins.call("midgard.dev", "non_existent", prefix="prefix")


def test_ordered_plugin(plugin_package):
    """Test that order of plugins can be customized"""
    plugin_names = plugins.names(plugin_package)
    assert plugin_names[0] == "plugin_first"
    assert plugin_names[-1] == "plugin_last"


def test_default_part(plugin_package):
    """Test that first registered function in a plugin is called by default"""
    plugin_name = "plugin_parts"
    default = plugins.call(plugin_package, plugin_name)
    explicit = plugins.call(plugin_package, plugin_name, part="plugin_default")
    assert default == explicit


def test_named_parts(plugin_package):
    """Test that a named part inside a plugin can be called"""
    plugin_name = "plugin_parts"
    part_name = "named_part"
    assert plugins.call(plugin_package, plugin_name, part=part_name) == "named"


def test_named_part_not_in_parts(plugin_package):
    """Test that named parts are kept separate from unnamed parts"""
    plugin_name = "plugin_parts"
    part_name = "named_part"
    assert part_name not in plugins.parts(plugin_package, plugin_name)


def test_all_plugins(plugin_package):
    """Test that call_all calls all plugins"""
    results = plugins.call_all(plugin_package)
    assert isinstance(results, dict)
    assert len(results) > 1


def test_call_non_existing_part(plugin_package):
    """Test that calling a non-existing part raises an error"""
    plugin_name = "plugin_parts"
    part_name = "non_existent"
    with pytest.raises(exceptions.UnknownPluginError):
        plugins.call(plugin_package, plugin_name, part=part_name)


def test_logger(capsys, plugin_package):
    """Test that using a logger prints to stdout"""
    plugin_name = "plugin_plain"
    plugins.call(plugin_package, plugin_name, plugin_logger=print)
    stdout, stderr = capsys.readouterr()

    assert len(stdout) > 0
    assert stderr == ""


def test_short_doc(plugin_package):
    """Test that we can retrieve the short docstring from a plugin"""
    plugin_name = "plugin_plain"
    doc = plugins.doc(plugin_package, plugin_name, long_doc=False)
    assert doc == "A plain plugin"


def test_long_doc(plugin_package):
    """Test that we can retrieve the long docstring from a plugin"""
    plugin_name = "plugin_plain"
    doc = plugins.doc(plugin_package, plugin_name)
    assert doc == "This is the plain docstring."


def test_all_docs(plugin_package):
    """Test that we can retrieve the docstrings from all plugins"""
    docs = plugins.doc_all(plugin_package, long_doc=False)
    assert len(docs) > 1

    plugin_name = "plugin_plain"
    assert plugin_name in docs
    assert docs[plugin_name] == "A plain plugin"
