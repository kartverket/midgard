"""Tests for the parsers-package

Tests for individual parsers are in their own files
"""

# Standard library imports
import pathlib

# Third party imports
import numpy as np
import pytest

# Midgard imports
from midgard import parsers


def get_parser(parser_name):
    """Get a parser that has parsed an example file"""
    example_path = pathlib.Path(__file__).parent / "example_files" / parser_name
    return parsers.parse_file(parser_name, example_path)


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


def test_parser_bcecmp_sisre():
    """Test that parsing bcecmp_sisre gives expected output"""
    parser = get_parser("bcecmp_sisre").as_dict()

    assert len(parser) == 12
    assert "age_min" in parser
    assert "E26" in parser["satellite"]


def test_parser_csv_():
    """Test that parsing csv_ gives expected output"""
    parser = get_parser("csv_").as_dict()

    assert len(parser) == 13
    assert "GPSEpoch" in parser
    assert 2047 in parser["GPSWeek"]


def test_parser_discontinuities_snx():
    """Test that parsing discontinuities_snx gives expected output"""
    parser = get_parser("discontinuities_snx").as_dict()

    assert len(parser) == 9
    assert "0194" in parser
    assert "solution_discontinuity" in parser["ab06"]
    assert "point_code" in parser["ab06"]["solution_discontinuity"][0]


def test_parser_galileo_constellation_html():
    """Test that parsing galileo_constellation_html gives expected output"""
    parser = get_parser("galileo_constellation_html")
    data = parser.as_dict()
    events = parser.meta["events"]

    assert parser.satellite_name("GSAT0101")["sv_id"] == "E11"
    assert parser.satellite_id("E01")["satellite_name"] == "GSAT0210"
    assert "clock" in data
    assert len(data["active_nagu"]) == 26
    assert len(events) == 6
    assert events[0]["date_of_publication_utc"] == "2016-08-02 07:25"


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_galileo_constellation_html_download():
    """Test that parsing galileo_constellation_html gives expected output"""
    assert False


def test_parser_gipsy_tdp():
    """Test that parsing gipsy_tdp gives expected output"""
    parser = get_parser("gipsy_tdp").as_dict()

    assert len(parser) == 5
    assert "time_past_j2000" in parser
    assert "TRPAZSINZIMM" in parser["name"]


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_gipsyx_gdcov():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_gipsyx_residual():
    pass


def test_parser_gipsyx_series():
    """Test that parsing gipsyx_series gives expected output"""
    parser = get_parser("gipsyx_series").as_dict()

    assert len(parser) == 17
    assert "north_sigma" in parser
    assert parser["east_sigma"][0] == 0.000698


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_gipsyx_summary():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_gipsyx_tdp():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_glab_output():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_android_raw_data():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_antex():
    pass


def test_parser_gnss_bernese_crd():
    """Test that parsing gnss_bernese_crd gives expected output"""
    parser = get_parser("gnss_bernese_crd").as_dict()

    assert len(parser) == 5
    assert "aasc" in parser
    assert "num" in parser["aasc"]


def test_gnss_sinex_igs():
    """Test that parsing gnss_sinex_igs gives expected output"""
    parser = get_parser("gnss_sinex_igs").as_dict()

    assert len(parser) == 8
    assert "abmf" in parser
    assert "site_id" in parser["abmf"]
    assert "site_code" in parser["abmf"]["site_id"]
    assert "abmf" in parser["abmf"]["site_id"]["site_code"]


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_rinex2_nav():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_rinex2_obs():
    pass


@pytest.mark.skip(reason="TODO: Tests not yet implemented")
def test_parser_rinex3_nav():
    pass


@pytest.mark.skip(reason="New Rinex3 parser not yet implemented")
def test_parser_wip_rinex3_obs():
    """Test that parsing rinex3_obs gives expected output"""
    parser = get_parser("rinex3_obs")
    data = parser.as_dict()
    header = parser.header

    expected_obs_e = ["C1X", "L1X", "D1X", "S1X", "C5X", "L5X", "S5X", "C8X", "L8X", "S8X", "C7X", "L7X", "S7X"]

    assert header["rinex_version"] == "3.03"
    assert header["receiver_type"] == "TRIMBLE NETR9"
    assert "receiver_version" not in header
    assert header["obs_types"]["E"] == expected_obs_e

    assert "epoch" in data
    for obs_type in expected_obs_e:
        assert obs_type in data
    assert len(data["satellite"]) == 10
    assert data["C6X"][0] == 40600783.887
    assert data["C1C"][0] == np.nan

    assert header["time_of_first_obs"] == data["epoch"][0]


@pytest.mark.skip(reason="TODO: Has to be moved from Where to Midgard")
def test_parser_spring_csv():
    """Test that parsing spring_csv gives expected output"""
    parser = get_parser("spring_csv").as_dict()

    assert len(parser) == 17
    assert "GPSEpoch" in parser
    assert 2047 in parser["GPSWeek"]


def test_parser_terrapos_position():
    """Test that parsing terrapos_position gives expected output"""
    parser = get_parser("terrapos_position").as_dict()

    assert len(parser) == 19
    assert "lat" in parser
    assert 1972 in parser["gpsweek"]


def test_parser_terrapos_residual():
    """Test that parsing terrapos_residual gives expected output"""
    parser = get_parser("terrapos_residual").as_dict()

    assert len(parser) == 9
    assert "residual_code" in parser
    assert "G01" in parser["satellite"]
    assert "G" in parser["system"]


def test_parser_timeseries_env():
    """Test that parsing timeseries_env gives expected output"""
    parser = get_parser("timeseries_env").as_dict()

    assert len(parser) == 8
    assert "date" in parser
    assert "14AUG31" in parser["date"]


def test_parser_timeseries_residuals():
    """Test that parsing timeseries_residuals gives expected output"""
    parser = get_parser("timeseries_residuals").as_dict()

    assert len(parser) == 5
    assert "year" in parser
    assert 0.66 in parser["residual"]

def test_parser_timeseries_tsview():
    """Test that parsing timeseries_tsview gives expected output"""
    parser = get_parser("timeseries_tsview").as_dict()

    assert len(parser) == 4
    assert "mjd" in parser
    assert 51058.5 in parser["mjd"]


def test_parser_vlbi_source_names():
    """Test that parsing vlbi_source_names gives expected output"""
    parser = get_parser("vlbi_source_names").as_dict()

    assert "2357-326" in parser
    assert len(parser) == 8
    assert parser["2357-326"]["icrf_name_short"] == "J0000-3221"
