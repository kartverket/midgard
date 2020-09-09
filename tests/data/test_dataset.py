""" Tests for the data.dataset module"""
# Standard library imports
import copy
from datetime import datetime, timedelta
import os

# Third party imports
import numpy as np
import pytest

# Midgard imports
from midgard.data import dataset
from midgard.data import position
from midgard.dev import exceptions


@pytest.fixture
def dset(request):
    return request.getfixturevalue(request.param.__name__)


@pytest.fixture
def dset1(request):
    return request.getfixturevalue(request.param.__name__)


@pytest.fixture
def dset2(request):
    return request.getfixturevalue(request.param.__name__)


@pytest.fixture
def dset_null():
    _dset = dataset.Dataset(0)
    return _dset


@pytest.fixture
def dset_empty():
    _dset = dataset.Dataset(5)
    return _dset


@pytest.fixture
def dset_float():
    _dset = dataset.Dataset(5)
    _dset.add_float("numbers", val=[0.1, 0.2, 0.3, 0.4, 0.5], unit="seconds")
    return _dset


@pytest.fixture
def dset_no_collection():
    """Contains all available fieldstypes"""
    _dset = dataset.Dataset(5)
    _dset.add_bool("idx", val=[0, 1, 1, 0, 1])
    _dset.add_float("numbers", val=[1, 2, 3, 4, 5])
    _dset.add_position("sat_pos", val=np.ones((5, 3)), system="trs")
    _dset.add_position("site_pos", val=np.ones((5, 3)) * 2, system="trs", other=_dset.sat_pos)
    _dset.add_position_delta("site_delta", val=np.ones((5, 3)) * 0.5, system="trs", ref_pos=_dset.site_pos)
    _dset.add_posvel("sat_posvel", val=np.ones((5, 6)), system="trs")
    _dset.add_posvel("site_posvel", val=np.ones((5, 6)) * 2, system="trs", other=_dset.sat_posvel)
    _dset.add_posvel_delta("site_posvel_delta", val=np.ones((5, 6)) * 0.5, system="trs", ref_pos=_dset.site_posvel)
    _dset.add_sigma("numbers2", val=[3, 3, 3, 3, 3], sigma=[0.2, 0.2, 0.2, 0.2, 0.2])
    _dset.add_text("text", val=["aaa", "aaa", "aaa", "aaa", "aaa"])
    _dset.add_time("time", val=[datetime(2015, 1, i) for i in range(5, 10)], scale="utc", fmt="datetime")
    _dset.add_time_delta("time_delta", val=[timedelta(seconds=i) for i in range(20, 25)], scale="utc", fmt="timedelta")
    return _dset


@pytest.fixture
def dset_full():
    """Contains all available fieldstypes"""
    _dset = dataset.Dataset(5)
    _dset.add_bool("idx", val=[0, 1, 1, 0, 1])
    _dset.add_float("numbers", val=[1, 2, 3, 4, 5])
    _dset.add_float("numbers_1", val=[2, 2, 2, 2, 2])
    _dset.add_float("numbers_2", val=[3, 3, 3, 3, 3])
    _dset.add_position("sat_pos", val=np.ones((5, 3)), system="trs")
    _dset.add_position("site_pos", val=np.ones((5, 3)) * 2, system="trs", other=_dset.sat_pos)
    _dset.add_position_delta("site_delta", val=np.ones((5, 3)) * 0.5, system="trs", ref_pos=_dset.site_pos)
    _dset.add_posvel("sat_posvel", val=np.ones((5, 6)), system="trs")
    _dset.add_posvel("site_posvel", val=np.ones((5, 6)) * 2, system="trs", other=_dset.sat_posvel)
    _dset.add_posvel_delta("site_posvel_delta", val=np.ones((5, 6)) * 0.5, system="trs", ref_pos=_dset.site_posvel)
    _dset.add_sigma("numbers2", val=[3, 3, 3, 3, 3], sigma=[0.2, 0.2, 0.2, 0.2, 0.2])
    _dset.add_text("text", val=["aaa", "aaa", "aaa", "aaa", "aaa"])
    _dset.add_time("time", val=[datetime(2015, 1, i) for i in range(5, 10)], scale="utc", fmt="datetime")
    _dset.add_time_delta("time_delta", val=[timedelta(seconds=i) for i in range(20, 25)], scale="utc", fmt="timedelta")

    # Collections
    _dset.add_bool("group.idx", val=[0, 0, 0, 0, 0])
    _dset.add_float("group.numbers", val=[6, 7, 8, 9, 10])
    _dset.add_position("group.sat_pos", val=np.ones((5, 3)) * 7, system="trs")
    _dset.add_position("group.site_pos", val=np.ones((5, 3)) * 8, system="trs", other=_dset.group.sat_pos)
    _dset.add_position_delta("group.site_delta", val=np.ones((5, 3)) * 9.5, system="trs", ref_pos=_dset.group.site_pos)
    _dset.add_posvel("group.sat_posvel", val=np.ones((5, 6)) * 6, system="trs")
    _dset.add_posvel("group.site_posvel", val=np.ones((5, 6)) * 5, system="trs", other=_dset.group.sat_posvel)
    _dset.add_posvel_delta(
        "group.site_posvel_delta", val=np.ones((5, 6)) * 1.5, system="trs", ref_pos=_dset.group.site_posvel
    )
    _dset.add_sigma("group.numbers2", val=[1.2, 1.2, 1.2, 1.2, 1.2], sigma=[3.2, 3.2, 3.2, 3.2, 3.2])
    _dset.add_text("group.text", val=["bbb", "bbb", "bbb", "bbb", "bbb"])
    _dset.add_time("group.time", val=[datetime(2015, 1, i) for i in range(10, 15)], scale="utc", fmt="datetime")
    _dset.add_time_delta(
        "group.time_delta", val=[timedelta(seconds=i) for i in range(0, 5)], scale="utc", fmt="timedelta"
    )

    # Nested collections
    _dset.add_bool("group.anothergroup.idx", val=[0, 0, 0, 0, 0])
    _dset.add_float("group.anothergroup.numbers", val=[6, 7, 8, 9, 10])
    _dset.add_position("group.anothergroup.sat_pos", val=np.ones((5, 3)) * 7, system="trs")
    _dset.add_position(
        "group.anothergroup.site_pos", val=np.ones((5, 3)) * 8, system="trs", other=_dset.group.anothergroup.sat_pos
    )
    _dset.add_position_delta(
        "group.anothergroup.site_delta",
        val=np.ones((5, 3)) * 9.5,
        system="trs",
        ref_pos=_dset.group.anothergroup.site_pos,
    )
    _dset.add_posvel("group.anothergroup.sat_posvel", val=np.ones((5, 6)) * 6, system="trs")
    _dset.add_posvel(
        "group.anothergroup.site_posvel",
        val=np.ones((5, 6)) * 5,
        system="trs",
        other=_dset.group.anothergroup.sat_posvel,
    )
    _dset.add_posvel_delta(
        "group.anothergroup.site_posvel_delta",
        val=np.ones((5, 6)) * 1.5,
        system="trs",
        ref_pos=_dset.group.anothergroup.site_posvel,
    )
    _dset.add_sigma("group.anothergroup.numbers2", val=[1.2, 1.2, 1.2, 1.2, 1.2], sigma=[3.2, 3.2, 3.2, 3.2, 3.2])
    _dset.add_text("group.anothergroup.text", val=["bbb", "bbb", "bbb", "bbb", "bbb"])
    _dset.add_time(
        "group.anothergroup.time", val=[datetime(2015, 1, i) for i in range(10, 15)], scale="utc", fmt="datetime"
    )
    _dset.add_time_delta(
        "group.anothergroup.time_delta", val=[timedelta(seconds=i) for i in range(0, 5)], scale="utc", fmt="timedelta"
    )

    _dset.meta.add("dummy", "something")
    _dset.meta.add("testlist", [1, 2])
    _dset.meta.add("testdict", {"a": 2, "b": 3})
    _dset.meta.add("testtuple", ("c", "d"))
    _dset.meta.add("testset", {1, 2})
    _dset.meta.add("testlist2", list())
    _dset.meta.add("testdict2", dict())
    _dset.meta.add("testtuple2", tuple())
    _dset.meta.add("testset2", set())
    _dset.meta.add_event(_dset.time[0], "jump", "something happened")
    return _dset


@pytest.mark.parametrize("dset", (dset_float, dset_full), indirect=True)
def test_num_obs_setter(dset):
    with pytest.raises(AttributeError):
        dset.num_obs = 10


@pytest.mark.parametrize("dset", (dset_empty, dset_float, dset_full, dset_no_collection), indirect=True)
def test_subset_1(dset):
    idx = np.array([1, 1, 0, 0, 0], dtype=bool)
    dset.subset(idx)


def test_subset_2(dset_full):
    idx = np.array([1, 1, 0, 0, 0], dtype=bool)
    dset_full.subset(idx)

    assert id(dset_full.site_pos.other) == id(dset_full.sat_pos)
    assert id(dset_full.site_delta.ref_pos) == id(dset_full.site_pos)
    assert id(dset_full.site_posvel.other) == id(dset_full.sat_posvel)
    assert id(dset_full.site_posvel_delta.ref_pos) == id(dset_full.site_posvel)

    assert id(dset_full.group.site_pos.other) == id(dset_full.group.sat_pos)
    assert id(dset_full.group.site_delta.ref_pos) == id(dset_full.group.site_pos)
    assert id(dset_full.group.site_posvel.other) == id(dset_full.group.sat_posvel)
    assert id(dset_full.group.site_posvel_delta.ref_pos) == id(dset_full.group.site_posvel)

    assert id(dset_full.group.anothergroup.site_pos.other) == id(dset_full.group.anothergroup.sat_pos)
    assert id(dset_full.group.anothergroup.site_delta.ref_pos) == id(dset_full.group.anothergroup.site_pos)
    assert id(dset_full.group.anothergroup.site_posvel.other) == id(dset_full.group.anothergroup.sat_posvel)
    assert id(dset_full.group.anothergroup.site_posvel_delta.ref_pos) == id(dset_full.group.anothergroup.site_posvel)

    assert dset_full.num_obs == 2

    # Verify that num_obs for each field is updated correctly
    def test_field(field, num_obs):
        try:
            for collection_field in field.data._fields.values():
                test_field(collection_field, num_obs)
        except AttributeError:
            pass

        assert field.num_obs == num_obs == len(field.data)

    for field in dset_full._fields.values():
        print(f"Testing field {field}")
        test_field(field, dset_full.num_obs)


@pytest.mark.parametrize(
    "dset1, dset2",
    [
        (dset_full, dset_empty),
        (dset_empty, dset_full),
        (dset_full, dset_null),
        (dset_full, dset_full),
        (dset_no_collection, dset_full),
    ],
    indirect=True,
)
def test_extend(dset1, dset2):

    dset1_num_obs = dset1.num_obs
    dset2_num_obs = dset2.num_obs
    dset1.extend(dset2)

    assert id(dset1.site_pos.other) == id(dset1.sat_pos)
    assert id(dset1.site_delta.ref_pos) == id(dset1.site_pos)
    assert id(dset1.site_posvel.other) == id(dset1.sat_posvel)
    assert id(dset1.site_posvel_delta.ref_pos) == id(dset1.site_posvel)

    assert id(dset1.group.site_pos.other) == id(dset1.group.sat_pos)
    assert id(dset1.group.site_delta.ref_pos) == id(dset1.group.site_pos)
    assert id(dset1.group.site_posvel.other) == id(dset1.group.sat_posvel)
    assert id(dset1.group.site_posvel_delta.ref_pos) == id(dset1.group.site_posvel)

    assert dset1.num_obs == dset1_num_obs + dset2_num_obs

    # Verify that num_obs for each field is updated correctly
    def test_field(field, num_obs):
        try:
            for collection_field in field.data._fields.values():
                test_field(collection_field, num_obs)
        except AttributeError:
            pass

        assert field.num_obs == num_obs == len(field.data)

    for field in dset1._fields.values():
        print(f"Testing field {field}")
        test_field(field, dset1.num_obs)


@pytest.mark.parametrize(
    "dset1, dset2", [(dset_full, dset_empty), (dset_empty, dset_full), (dset_full, dset_full)], indirect=True
)
def test_merge(dset1, dset2):
    dset1_num_obs = dset1.num_obs
    dset2_num_obs = dset2.num_obs
    dset1.merge_with(dset2, sort_by="time")

    assert id(dset1.site_pos.other) == id(dset1.sat_pos)
    assert id(dset1.site_delta.ref_pos) == id(dset1.site_pos)
    assert id(dset1.site_posvel.other) == id(dset1.sat_posvel)
    assert id(dset1.site_posvel_delta.ref_pos) == id(dset1.site_posvel)

    assert id(dset1.group.site_pos.other) == id(dset1.group.sat_pos)
    assert id(dset1.group.site_delta.ref_pos) == id(dset1.group.site_pos)
    assert id(dset1.group.site_posvel.other) == id(dset1.group.sat_posvel)
    assert id(dset1.group.site_posvel_delta.ref_pos) == id(dset1.group.site_posvel)

    assert dset1.num_obs == dset1_num_obs + dset2_num_obs

    # Verify that num_obs for each field is updated correctly
    def test_field(field, num_obs):
        try:
            for collection_field in field.data._fields.values():
                test_field(collection_field, num_obs)
        except AttributeError:
            pass

        assert field.num_obs == num_obs == len(field.data)

    for field in dset1._fields.values():
        print(f"Testing field {field}")
        test_field(field, dset1.num_obs)


@pytest.mark.parametrize("dset", (dset_empty, dset_float, dset_full, dset_no_collection), indirect=True)
def test_read_write(dset):
    """Test data equality after write and then read"""
    file_name = "test.hdf5"
    dset.write(file_name)

    dset_new = dataset.Dataset.read(file_name)

    def test_field(field, new_field):
        try:
            if field.data.dtype.type is np.str_:
                assert np.char.equal(field.data, new_field.data).all()
            else:
                assert np.equal(np.asarray(field.data), np.asarray(new_field.data)).all()
        except AttributeError:
            # field is a collection
            for collection_field_name, collection_field in field.data._fields.items():
                new_collection_field = new_field.data._fields[collection_field_name]
                test_field(collection_field, new_collection_field)

    for field_name, field in dset._fields.items():
        print(f"Testing {field_name}")
        new_field = dset_new._fields[field_name]
        test_field(field, new_field)

    os.remove(file_name)


def test_read_write_2(dset_full):
    """Test references after write and then read"""
    file_name = "test.hdf5"
    dset_full.write(file_name)

    dset_new = dataset.Dataset.read(file_name)

    # Test internal references in the dataset
    assert id(dset_new.site_pos.other) == id(dset_new.sat_pos)
    assert id(dset_new.site_delta.ref_pos) == id(dset_new.site_pos)
    assert id(dset_new.site_posvel.other) == id(dset_new.sat_posvel)
    assert id(dset_new.site_posvel_delta.ref_pos) == id(dset_new.site_posvel)

    assert id(dset_new.group.site_pos.other) == id(dset_new.group.sat_pos)
    assert id(dset_new.group.site_delta.ref_pos) == id(dset_new.group.site_pos)
    assert id(dset_new.group.site_posvel.other) == id(dset_new.group.sat_posvel)
    assert id(dset_new.group.site_posvel_delta.ref_pos) == id(dset_new.group.site_posvel)

    # Verify that new dataset have different references than original object
    def test_field(field, new_field):
        try:
            for collection_field_name, collection_field in field.data._fields.items():
                new_collection_field = new_field.data._fields[collection_field_name]
                test_field(collection_field, new_collection_field)
        except AttributeError:
            # field is not a collection
            pass

        assert id(field.data) != id(new_field.data)

    for field_name, field in dset_full._fields.items():
        print(f"Testing {field_name}")
        new_field = dset_new._fields[field_name]
        test_field(field, new_field)

    assert dset_new.meta["dummy"] == "something"
    assert dset_new.meta.get_events("jump") == [(dset_new.time[0], "jump", "something happened")]

    os.remove(file_name)


def test_read_write_3():
    """Test references after write and then read when attributes are not dataset fields"""
    _dset = dataset.Dataset(2)
    ref_pos = position.Position([[1, 2, 3], [1, 2, 3]], system="trs")
    ref_pos2 = position.PosVel([[1, 2, 3, 1, 1, 1], [1, 2, 3, 2, 2, 2]], system="trs")
    other = position.Position([[7, 8, 9], [7, 8, 9]], system="trs")
    other2 = position.PosVel([[1, 2, 3, 1, 2, 3], [1, 2, 3, 4, 5, 6]], system="trs")
    _dset.add_position("testpos", [[4, 5, 6], [4, 5, 6]], system="trs", other=other)
    _dset.add_position_delta("testposdelta", [[0.1, 0.1, 0.1], [0.2, 0.2, 0.2]], system="trs", ref_pos=ref_pos)
    _dset.add_posvel("testposvel", [[1, 1, 1, 2, 2, 2], [3, 3, 3, 4, 4, 4]], system="trs", other=other2)
    _dset.add_posvel_delta("testposveldelta", [[4, 4, 4, 1, 1, 1], [5, 5, 5, 2, 2, 2]], system="trs", ref_pos=ref_pos2)
    file_name = "test.hdf5"
    _dset.write(file_name)
    _dset_new = dataset.Dataset.read(file_name)

    def test_field(field, new_field):
        try:
            if field.data.dtype.type is np.str_:
                assert np.char.equal(field.data, new_field.data).all()
            else:
                assert np.equal(np.asarray(field.data), np.asarray(new_field.data)).all()
        except AttributeError:
            # field is a collection
            for collection_field_name, collection_field in field.data._fields.items():
                new_collection_field = new_field.data._fields[collection_field_name]
                test_field(collection_field, new_collection_field)

    for field_name, field in _dset._fields.items():
        print(f"Testing {field_name}")
        new_field = _dset_new._fields[field_name]
        test_field(field, new_field)

    os.remove(file_name)


@pytest.mark.parametrize("dset", (dset_empty, dset_float, dset_full, dset_no_collection), indirect=True)
def test_copy(dset):
    """Test data equality after copy"""
    dset_new = copy.deepcopy(dset)

    def test_field(field, new_field):
        try:
            if field.data.dtype.type is np.str_:
                assert np.char.equal(field.data, new_field.data).all()
            else:
                assert np.equal(np.asarray(field.data), np.asarray(new_field.data)).all()
        except AttributeError:
            # field is a collection
            for collection_field_name, collection_field in field.data._fields.items():
                new_collection_field = new_field.data._fields[collection_field_name]
                test_field(collection_field, new_collection_field)

    for field_name, field in dset._fields.items():
        print(f"Testing {field_name}")
        new_field = dset_new._fields[field_name]
        test_field(field, new_field)


def test_copy_2(dset_full):
    """Test references after copy"""
    dset_new = copy.deepcopy(dset_full)

    # Test internal references in the dataset
    assert id(dset_new.site_pos.other) == id(dset_new.sat_pos)
    assert id(dset_new.site_delta.ref_pos) == id(dset_new.site_pos)
    assert id(dset_new.site_posvel.other) == id(dset_new.sat_posvel)
    assert id(dset_new.site_posvel_delta.ref_pos) == id(dset_new.site_posvel)

    assert id(dset_new.group.site_pos.other) == id(dset_new.group.sat_pos)
    assert id(dset_new.group.site_delta.ref_pos) == id(dset_new.group.site_pos)
    assert id(dset_new.group.site_posvel.other) == id(dset_new.group.sat_posvel)
    assert id(dset_new.group.site_posvel_delta.ref_pos) == id(dset_new.group.site_posvel)

    # Verify that new dataset have different references than original object
    def test_field(field, new_field):
        try:
            for collection_field_name, collection_field in field.data._fields.items():
                new_collection_field = new_field.data._fields[collection_field_name]
                test_field(collection_field, new_collection_field)
        except AttributeError:
            # field is not a collection
            pass

        assert id(field.data) != id(new_field.data)

    for field_name, field in dset_full._fields.items():
        print(f"Testing {field_name}")
        new_field = dset_new._fields[field_name]
        test_field(field, new_field)


def test_filter():
    _dset = dataset.Dataset(7)
    _dset.add_text("text_1", list("abcdefg"))
    _dset.add_text("text_2", list("gfedcba"))
    _dset.add_time("time", [datetime(2015, 1, 1, i) for i in range(0, 7)], fmt="datetime", scale="utc")
    _dset.add_text("group.text_1", list("hijklmn"))
    _dset.add_text("group.text_2", list("nmlkjih"))

    # Normal filter with and without collection
    idx1 = _dset.filter(text_1="a")
    idx2 = _dset.filter(**{"group.text_1": "h"})
    idx22 = _dset.filter(text_1="h", collection="group")  # Same filer, different syntax
    assert np.equal(idx2, idx22).all()
    idx3 = _dset.filter(time=datetime(2015, 1, 1, 0))
    idx = np.array([True, False, False, False, False, False, False], dtype=bool)
    assert np.equal(idx1, idx).all()
    assert np.equal(idx2, idx).all()
    assert np.equal(idx3, idx).all()

    # Underscore filter with and without collection
    idx1 = _dset.filter(text="a")
    idx2 = _dset.filter(**{"group.text": "h"})
    idx22 = _dset.filter(text="h", collection="group")  # Same filer, different syntax
    assert np.equal(idx2, idx22).all()
    idx = np.array([True, False, False, False, False, False, True], dtype=bool)
    assert np.equal(idx1, idx).all()
    assert np.equal(idx2, idx).all()

    # Wrong field
    with pytest.raises(AttributeError):
        _dset.filter(tull="a")


def test_suffix():
    _dset = dataset.Dataset(2)
    _dset.add_float("numbers_1", [1, 1], multiplier=10)
    _dset.add_float("numbers_2", [2, 2], multiplier=-10)
    _dset.add_float("group.numbers_1", [3, 3], multiplier=10)
    _dset.add_float("group.numbers_2", [4, 4], multiplier=-10)

    answer = np.array([[10, 10], [-20, -20]])
    for i, multiplier in enumerate(_dset.for_each_suffix("numbers")):
        assert np.equal(answer[i], multiplier * _dset.numbers).all()

    answer2 = np.array([[30, 30], [-40, -40]])
    for i, multiplier in enumerate(_dset.group.for_each_suffix("numbers")):
        assert np.equal(answer2[i], multiplier * _dset.group.numbers).all()

    # Same test but with different syntax
    answer2 = np.array([[30, 30], [-40, -40]])
    for i, multiplier in enumerate(_dset.for_each_suffix("group.numbers")):
        assert np.equal(answer2[i], multiplier * _dset.group.numbers).all()


def test_unique():
    _dset = dataset.Dataset(10)
    _dset.add_text("text", list("abcabcabca"))
    _dset.add_time("time", [58000] * 2 + [58001] * 6 + [58002] * 2, fmt="mjd", scale="utc")
    _dset.add_float("numbers_1", [1, 2, 1, 2, 1, 2, 1, 2, 1, 2])
    _dset.add_float("numbers_2", [3, 4, 3, 4, 3, 4, 3, 4, 3, 4])
    _dset.add_time("group.time_1", [58000] * 10, fmt="mjd", scale="utc")
    _dset.add_time("group.time_2", [58001] * 10, fmt="mjd", scale="utc")
    _dset.add_text("group.text", list("defdefdefd"))
    _dset.add_float("group.numbers", range(0, 10))

    assert np.char.equal(_dset.unique("text"), np.array(list("abc"))).all()
    assert np.equal(_dset.unique("time"), np.array([58000, 58001, 58002])).all()
    assert np.equal(_dset.unique("numbers"), [1, 2, 3, 4]).all()
    assert np.equal(_dset.unique("group.time"), np.array([58000, 58001])).all()
    assert np.char.equal(_dset.unique("group.text"), np.array(list("def"))).all()
    assert np.equal(_dset.unique("group.numbers"), np.arange(0, 10)).all()


def test_difference_1():
    _dset1 = dataset.Dataset(2)
    _dset1.add_float("numbers", [1, 2], unit="meter")
    _dset1.add_time("t", [datetime(2009, 1, 1), datetime(2009, 2, 1)], scale="utc", fmt="datetime")
    _dset1.add_bool("flag", [True, False])
    _dset1.add_text("letters", list("ab"))
    _dset1.add_position("pos", [[1, 2, 3], [3, 2, 1]], system="trs")
    _dset1.add_float("group.more", [5, 5])

    _dset2 = dataset.Dataset(2)
    _dset2.add_float("numbers", [4, 5], unit="meter")
    _dset2.add_time("t", [datetime(2009, 1, 1), datetime(2009, 2, 2)], scale="utc", fmt="datetime")
    _dset2.add_bool("flag", [False, True])
    _dset2.add_text("letters", list("cd"))
    _dset2.add_position("pos", [[4, 5, 6], [6, 5, 4]], system="trs")
    _dset2.add_float("group.more", [4, 3])

    _dset3 = _dset1.difference(_dset2)
    assert np.equal(_dset3.numbers, [-3, -3]).all()
    assert np.equal(np.asarray(_dset3.pos), [[-3, -3, -3], [-3, -3, -3]]).all()
    assert np.equal(_dset3.group.more, [1, 2]).all()


def test_difference_2():
    _dset1 = dataset.Dataset(3)
    _dset1.add_float("numbers", [1, 2, 3], unit="meter")
    _dset1.add_time(
        "t", [datetime(2009, 1, 1), datetime(2009, 1, 2), datetime(2009, 2, 2)], scale="utc", fmt="datetime"
    )
    _dset1.add_bool("flag", [True, False, True])
    _dset1.add_text("letters", list("abc"))
    _dset1.add_position("pos", [[1, 2, 3], [3, 2, 1], [2, 2, 2]], system="trs")
    _dset1.add_float("group.more", [5, 5, 5])
    _dset1.add_text("group.even_more", list("fgh"))

    _dset2 = dataset.Dataset(4)
    _dset2.add_float("numbers", [3, 4, 5, 6], unit="meter")
    _dset2.add_time(
        "t",
        [datetime(2009, 1, 1), datetime(2009, 2, 1), datetime(2009, 2, 2), datetime(2009, 3, 3)],
        scale="utc",
        fmt="datetime",
    )
    _dset2.add_bool("flag", [False, False, True, True])
    _dset2.add_text("letters", list("cdef"))
    _dset2.add_position("pos", [[4, 5, 6], [6, 5, 4], [7, 8, 9], [2, 3, 4]], system="trs")
    _dset2.add_float("group.more", [4, 3, 4, 3])
    _dset2.add_text("group.even_more", list("jilh"))

    _dset3 = _dset1.difference(_dset2, index_by="t")

    assert np.equal(_dset3.numbers, [-2, -2]).all()
    assert np.equal(np.asarray(_dset3.pos), [[-3, -3, -3], [-5, -6, -7]]).all()
    assert np.equal(_dset3.group.more, [1, 1]).all()
    assert np.equal(_dset3.t, [datetime(2009, 1, 1), datetime(2009, 2, 2)]).all()

    _dset4 = _dset1.difference(_dset2, index_by="t, flag")
    assert np.equal(_dset4.numbers, [-2]).all()
    assert np.equal(np.asarray(_dset4.pos), [[-5, -6, -7]]).all()
    assert np.equal(_dset4.group.more, [1]).all()
    assert np.equal(_dset4.t, [datetime(2009, 2, 2)]).all()
    assert np.equal(_dset4.flag, [True]).all()

    _dset5 = _dset1.difference(_dset2, index_by="t, flag", copy_self_on_error=True, copy_other_on_error=True)
    assert np.char.equal(_dset5.letters_self, list("c")).all()
    assert np.char.equal(_dset5.letters_other, list("e")).all()
    assert np.char.equal(_dset5.group.even_more_self, list("h")).all()
    assert np.char.equal(_dset5.group.even_more_other, list("l")).all()


def test_difference_3():
    _dset1 = dataset.Dataset(3)
    _dset1.add_float("numbers", [1, 2, 3], unit="meter")

    _dset2 = dataset.Dataset(3)
    _dset2.add_float("numbers", [1, 2, 3], unit="cm")

    _dset3 = _dset1.difference(_dset2)
    assert np.equal(_dset3.numbers, [0.99, 1.98, 2.97]).all()
    assert _dset3.unit("numbers") == ("meter",)

    _dset4 = dataset.Dataset(3)
    _dset4.add_float("numbers", [1, 2, 3], unit="second")

    # Incompatible units
    with pytest.raises(ValueError):
        _dset1.difference(_dset4)

    _dset5 = dataset.Dataset(1)
    _dset5.add_float("numbers", [1], unit="meter")

    # Different length datasets (without specifying index_by)
    with pytest.raises(ValueError):
        _dset1.difference(_dset5)


def test_nested_collections():
    _dset = dataset.Dataset(2)
    _dset.add_float("group.group.tall", [5, 6])

    assert np.equal(_dset.group.group.tall, [5, 6]).all()

    idx = np.array([True, False], dtype=bool)
    _dset.subset(idx)

    assert np.equal(_dset.group.group.tall, [5]).all()

    _dset1 = dataset.Dataset(2)
    _dset1.add_float("group.group.tall", [5, 6])

    _dset2 = dataset.Dataset(3)
    _dset2.add_float("group.group.tall", [1, 2, 3])

    _dset1.extend(_dset2)
    assert np.equal(_dset1.group.group.tall, [5, 6, 1, 2, 3]).all()


def test_unit():
    _dset1 = dataset.Dataset(3)
    _dset1.add_float("numbers_1", [1, 2, 3], unit="meter")
    _dset1.add_float("numbers_2", [1, 2, 3], unit="second")
    _dset1.add_bool("idx", [True, False, True])
    _dset1.add_float("group.numbers", [1, 2, 3], unit="watt")
    _dset1.add_sigma("sigma", [1, 2, 3], sigma=[0.1, 0.2, 0.3], unit="meter")

    assert _dset1.unit("numbers_1") == ("meter",)
    assert _dset1.unit("numbers_2") == ("second",)
    assert _dset1.unit("group.numbers") == ("watt",)
    with pytest.raises(exceptions.UnitError):
        _dset1.unit("idx")
    assert _dset1.unit_short("numbers_1") == ("m",)
    assert _dset1.unit_short("numbers_2") == ("s",)
    with pytest.raises(exceptions.UnitError):
        _dset1.unit_short("idx")
    assert _dset1.unit_short("group.numbers") == ("W",)
    assert _dset1.unit("sigma") == ("meter",)
    assert _dset1.unit("sigma.sigma") == ("meter",)
    assert _dset1.unit_short("sigma") == ("m",)
    assert _dset1.unit_short("sigma.sigma") == ("m",)

    _dset1.set_unit("sigma", "seconds")

    assert _dset1.unit("sigma") == ("seconds",)
    assert _dset1.unit("sigma.sigma") == ("seconds",)
    assert _dset1.unit_short("sigma") == ("s",)
    assert _dset1.unit_short("sigma.sigma") == ("s",)

def test_functions(dset_full):
    dset_full.as_dict()
    dset_full.as_dataframe()
    for field in dset_full.plot_fields:
        dset_full.plot_values(field)


def test_delete(dset_full):
    # Deletion of dataset "rows" is not allowed
    with pytest.raises(IndexError):
        del dset_full[0]

    # Delete a field with __delattr__
    assert "numbers" in dset_full.fields
    dset_full.numbers

    del dset_full.numbers
    assert "numbers" not in dset_full.fields
    with pytest.raises(AttributeError):
        dset_full.numbers

    # Delete a field in a collection with __delattr__
    assert "group.numbers" in dset_full.fields
    dset_full.group.numbers

    del dset_full.group.numbers
    assert "group.numbers" not in dset_full.fields
    with pytest.raises(AttributeError):
        dset_full.group.numbers

    # Delete a field in a nested collection with __delattr__
    assert "group.anothergroup.numbers" in dset_full.fields
    dset_full.group.anothergroup.numbers

    del dset_full.group.anothergroup.numbers
    assert "group.anothergroup.numbers" not in dset_full.fields
    with pytest.raises(AttributeError):
        dset_full.group.anothergroup.numbers

    # Delete a field with __delitem__
    assert "time" in dset_full.fields
    dset_full.time

    del dset_full["time"]
    assert "time" not in dset_full.fields
    with pytest.raises(AttributeError):
        dset_full.time

    # Delete a field in a collection with __delitem__
    assert "group.time" in dset_full.fields
    dset_full.group.time

    del dset_full["group.time"]
    assert "group.time" not in dset_full.fields
    with pytest.raises(AttributeError):
        dset_full.group.time

    # Delete a field with suffix with __delattr__
    assert "numbers_1" in dset_full.fields
    dset_full.numbers_1
    dset_full.numbers_2

    for _ in dset_full.for_each_suffix("numbers"):
        del dset_full.numbers
    assert "numbers_1" not in dset_full.fields
    assert "numbers_2" not in dset_full.fields
    with pytest.raises(AttributeError):
        dset_full.numbers_1
    with pytest.raises(AttributeError):
        dset_full.numbers_2
