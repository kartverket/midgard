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

    assert dset_full.num_obs == 2

    for field in dset_full._fields.values():
        try:
            assert field.num_obs == dset_full.num_obs == len(field.data)
        except AttributeError:
            for group_field in field._fields.values():
                assert group_field.num_obs == dset_full.num_obs == len(group_field.data)


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

    for field in dset1._fields.values():
        try:
            assert field.num_obs == dset1.num_obs == len(field.data)
        except AttributeError:
            for group_field in field.data._fields.values():
                assert group_field.num_obs == dset1.num_obs == len(group_field.data)


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

    for field in dset1._fields.values():
        try:
            assert field.num_obs == dset1.num_obs == len(field.data)
        except AttributeError:
            for group_field in field.data._fields.values():
                assert group_field.num_obs == dset1.num_obs == len(group_field.data)


@pytest.mark.parametrize("dset", (dset_empty, dset_float, dset_full, dset_no_collection), indirect=True)
def test_read_write(dset):
    """Test data equality after write and then read"""
    file_name = "test.hdf5"
    dset.write(file_name)

    dset_new = dataset.Dataset.read(file_name)

    for field_name, field in dset._fields.items():
        print(f"Testing {field_name}")
        try:
            if field.data.dtype.type is np.str_:
                assert np.char.equal(field.data, dset_new._fields[field_name].data).all()
            else:
                assert np.equal(field.data, dset_new._fields[field_name].data).all()
        except AttributeError:
            for group_field_name, group_field in field.data._fields.items():
                if group_field.data.dtype.type is np.str_:
                    assert np.char.equal(
                        group_field.data, dset_new._fields[field_name].data._fields[group_field_name].data
                    ).all()
                else:
                    assert np.equal(
                        group_field.data, dset_new._fields[field_name].data._fields[group_field_name].data
                    ).all()

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
    for field_name, field in dset_full._fields.items():
        assert id(field.data) != id(dset_new._fields[field_name].data)
        try:
            for group_field_name, group_field in field.data._fields.items():
                assert id(group_field.data) != id(dset_new._fields[field_name].data._fields[group_field_name].data)
        except AttributeError:
            # Field is not a group
            pass

    os.remove(file_name)


@pytest.mark.parametrize("dset", (dset_empty, dset_float, dset_full, dset_no_collection), indirect=True)
def test_copy(dset):
    """Test data equality after copy"""
    dset_new = copy.deepcopy(dset)

    for field_name, field in dset._fields.items():
        print(f"Testing {field_name}")
        try:
            if field.data.dtype.type is np.str_:
                assert np.char.equal(field.data, dset_new._fields[field_name].data).all()
            else:
                assert np.equal(field.data, dset_new._fields[field_name].data).all()
        except AttributeError:
            for group_field_name, group_field in field.data._fields.items():
                if group_field.data.dtype.type is np.str_:
                    assert np.char.equal(
                        group_field.data, dset_new._fields[field_name].data._fields[group_field_name].data
                    ).all()
                else:
                    assert np.equal(
                        group_field.data, dset_new._fields[field_name].data._fields[group_field_name].data
                    ).all()


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
    for field_name, field in dset_full._fields.items():
        assert id(field.data) != id(dset_new._fields[field_name].data)
        try:
            for group_field_name, group_field in field.data._fields.items():
                assert id(group_field.data) != id(dset_new._fields[field_name].data._fields[group_field_name].data)
        except AttributeError:
            # Field is not a group
            pass


def test_filter():
    _dset = dataset.Dataset(7)
    _dset.add_text("text_1", list("abcdefg"))
    _dset.add_text("text_2", list("gfedcba"))
    _dset.add_time("time", [datetime(2015, 1, 1, i) for i in range(0, 7)], fmt="datetime", scale="utc")
    _dset.add_text("group.text_1", list("hijklmn"))
    _dset.add_text("group.text_2", list("nmlkjih"))

    # Normal filter with and without group
    idx1 = _dset.filter(text_1="a")
    idx2 = _dset.filter(text_1="h", collection="group")
    idx3 = _dset.filter(time=datetime(2015, 1, 1, 0))
    idx = np.array([True, False, False, False, False, False, False], dtype=bool)
    assert np.equal(idx1, idx).all()
    assert np.equal(idx2, idx).all()
    assert np.equal(idx3, idx).all()

    # Underscore filter with and without group
    idx1 = _dset.filter(text="a")
    idx2 = _dset.filter(text="h", collection="group")
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
    for i, multiplier in enumerate(_dset.for_each_suffix("group.numbers")):
        assert np.equal(answer2[i], multiplier * _dset.group.numbers).all()


def test_unique():
    _dset = dataset.Dataset(10)
    _dset.add_text("text", list("abcabcabca"))
    _dset.add_time("time", [58000] * 2 + [58001] * 6 + [58002] * 2, fmt="mjd", scale="utc")
    _dset.add_text("group.text", list("defdefdefd"))
    _dset.add_float("group.numbers", range(0, 10))

    assert np.char.equal(_dset.unique("text"), np.array(list("abc"))).all()
    assert np.equal(_dset.unique("time"), np.array([58000, 58001, 58002])).all()
    assert np.char.equal(_dset.unique("text", collection="group"), np.array(list("def"))).all()
    assert np.equal(_dset.unique("group.numbers"), np.arange(0, 10)).all()
    assert np.equal(_dset.unique("numbers", collection="group"), np.arange(0, 10)).all()
