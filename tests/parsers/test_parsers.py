"""Tests for the parsers-package

Tests for individual parsers are in their own files

Note: pytest can be started with commando:
    python -m pytest -s test_parsers.py
    
"""

# Standard library imports
from datetime import datetime
import pathlib

# Third party imports
import numpy as np
import pytest

# Midgard imports
from midgard import parsers


def get_parser(parser_name, example_path = None):
    """Get a parser that has parsed an example file"""
    if not example_path:
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


def test_parser_gnss_android_raw_data():
    """Test that parsing gnss_android_raw_data gives expected output"""
    parser = get_parser("gnss_android_raw_data").as_dict()

    assert len(parser) == 43
    assert "provider" in parser
    assert "gps" in parser["provider"]


def test_parser_antex():
    """Test that parsing antex gives expected output"""
    parser = get_parser("antex").as_dict()

    assert len(parser) == 2
    assert "G01" in parser
    assert datetime(1992, 11, 22) in parser["G01"]
    

def test_parser_api_water_level_norway():
    """Test that parsing api_water_level_norway gives expected output"""
    parser = get_parser("api_water_level_norway").as_dict()

    assert len(parser) == 3
    assert "value" in parser
    assert "weather" in parser["flag"]


def test_parser_bcecmp_sisre():
    """Test that parsing bcecmp_sisre gives expected output"""
    parser = get_parser("bcecmp_sisre").as_dict()

    assert len(parser) == 12
    assert "age_min" in parser
    assert "E26" in parser["satellite"]


def test_parser_bernese_clu():
    """Test that parsing bernese_clu gives expected output"""
    parser = get_parser("bernese_clu").as_dict()

    assert len(parser) == 16
    assert "ales" in parser
    assert "domes" in parser["ales"]


def test_parser_bernese_crd():
    """Test that parsing bernese_crd gives expected output"""
    parser = get_parser("bernese_crd").as_dict()

    assert len(parser) == 5
    assert "aasc" in parser
    assert "domes" in parser["aasc"]


def test_parser_bernese_sta():
    """Test that parsing bernese_sta gives expected output"""
    parser = get_parser("bernese_sta").as_dict()

    assert len(parser) == 1
    assert "argi" in parser
    assert (datetime(2008,9,25), datetime(2016,11,11)) in parser["argi"][0]
    

def test_parser_bernese_trp():
    """Test that parsing bernese_trp gives expected output"""
    parser = get_parser("bernese_trp").as_dict()

    assert len(parser) == 12
    assert "station" in parser
    assert "AASC" in parser["station"]


def test_parser_csv_():
    """Test that parsing csv_ gives expected output"""
    parser = get_parser("csv_").as_dict()

    assert len(parser) == 13
    assert "GPSEpoch" in parser
    assert 2047 in parser["GPSWeek"]


@pytest.mark.skip(reason="TODO: Failure in pandas.io.html.py")
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


def test_parser_gipsyx_gdcov():
    """Test that parsing gipsyx_gdcov gives expected output"""
    parser = get_parser("gipsyx_gdcov").as_dict()

    assert len(parser) == 9
    assert "time_past_j2000" in parser
    assert "correlation" in parser
    assert 376018350.0 in parser["time_past_j2000"]


def test_parser_gipsyx_residual():
    """Test that parsing gipsyx_residual gives expected output"""
    parser = get_parser("gipsyx_residual").as_dict()

    assert len(parser) == 10
    assert "time_past_j2000" in parser
    assert 375969900.0 in parser["time_past_j2000"]


def test_parser_gipsyx_summary():
    """Test that parsing gipsyx_summary gives expected output"""
    parser = get_parser("gipsyx_summary").as_dict()

    assert len(parser) == 3
    assert "residual" in parser
    assert "code_rms" in parser["residual"]
    assert 0.6312075 == parser["residual"]["code_rms"]


def test_parser_gipsyx_tdp():
    """Test that parsing gipsyx_tdp gives expected output"""
    parser = get_parser("gipsyx_tdp").as_dict()

    assert len(parser) == 5
    assert "time_past_j2000" in parser
    assert 375969900.0 in parser["time_past_j2000"]


def test_parser_glab_output():
    """Test that parsing glab_output gives expected output"""
    parser = get_parser("glab_output").as_dict()

    assert len(parser) == 29
    assert "satellite" in parser
    assert 7 in parser["satellite"]

    
def test_parser_gravsoft_grid():
    """Test that parsing gravsoft_grid gives expected output"""
    parser = get_parser("gravsoft_grid").as_dict()

    assert len(parser) == 3
    assert "latitude" in parser
    assert 72.0 in parser["latitude"]


def test_parser_rinex2_nav():
    """Test that parsing rinex2_nav gives expected output"""
    parser = get_parser("rinex2_nav", pathlib.Path(__file__).parent / "example_files" / "rinex2_nav.19n").as_dict()

    assert len(parser) == 33
    assert "system" in parser
    assert "G" in parser["system"]


def test_parser_rinex2_obs():
    """Test that parsing rinex2_obs gives expected output"""
    parser = get_parser("rinex2_obs").as_dict()

    assert len(parser) == 8
    assert "obs" in parser
    assert "C1" in parser["obs"]
    assert 24236245.742 in parser["obs"]["C1"]


def test_parser_rinex3_nav():
    """Test that parsing rinex3_nav gives expected output"""
    parser = get_parser("rinex3_nav").as_dict()

    assert len(parser) == 45
    assert "system" in parser
    assert "G" in parser["system"]


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
    

def test_parser_sinex_discontinuities():
    """Test that parsing sinex_discontinuities gives expected output"""
    parser = get_parser("sinex_discontinuities").as_dict()

    assert len(parser) == 9
    assert "0194" in parser
    assert "solution_discontinuity" in parser["ab06"]
    assert "point_code" in parser["ab06"]["solution_discontinuity"][0]
    

def test_parser_sinex_events():
    """Test that parsing sinex_events gives expected output"""
    parser = get_parser("sinex_events").as_dict()
    
    assert len(parser) == 2
    assert "ande" in parser
    assert "solution_event" in parser["ande"]
    assert "point_code" in parser["ande"]["solution_event"][0]
    

def test_parser_sinex_site():
    """Test that parsing sinex_site gives expected output"""
    parser = get_parser("sinex_site").as_dict()

    assert len(parser) == 3
    assert "aasc" in parser
    assert "site_id" in parser["aasc"]
    assert "site_code" in parser["aasc"]["site_id"]
    assert "AASC" in parser["aasc"]["site_id"]["site_code"]


def test_parser_spring_csv():
    """Test that parsing spring_csv gives expected output"""
    parser = get_parser("spring_csv").as_dict()

    assert len(parser) == 17
    assert "GPSEpoch" in parser
    assert 2047 in parser["GPSWeek"]
    
    
def test_parser_ssc_site():
    """Test that parsing ssc_site gives expected output"""
    parser = get_parser("ssc_site").as_dict()

    assert len(parser) == 4
    assert "toul" in parser
    assert "site_id" in parser["toul"]


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


def test_parser_vlbi_source_names():
    """Test that parsing vlbi_source_names gives expected output"""
    parser = get_parser("vlbi_source_names").as_dict()

    assert "2357-326" in parser
    assert len(parser) == 8
    assert parser["2357-326"]["icrf_name_short"] == "J0000-3221"
