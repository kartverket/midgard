"""A parser for reading NASA JPL GipsyX time dependent parameter (TDP) file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_tdp', file_path='final.tdp')
    data = p.as_dict()

Description:
------------

Reads data from files in GipsyX time dependent parameter (TDP) format.

"""
# Standard library imports
from collections import namedtuple
from typing import Any, Dict

# External library imports
import numpy as np

# Midgard imports
from midgard.collections import enums
from midgard.data import dataset
from midgard.data.time import Time
from midgard.dev import log
from midgard.dev import plugins
from midgard.math.unit import Unit
from midgard.parsers import LineParser


DatasetField = namedtuple("DatasetField", ["name", "category", "dtype"])
DatasetField.__new__.__defaults__ = (None,) * len(DatasetField._fields)
DatasetField.__doc__ = """A convenience class for defining a dataset field properties

    Args:
        name  (str):             Dataset field name
        category (str):          Category of parameter (e.g. station or satellite parameter)
        dtype (str):             Dataset data type
    """


@plugins.register
class GipsyxTdpParser(LineParser):
    """A parser for reading GipsyX time dependent parameter (TDP) file

    Following **data** are available after reading GipsyX TDP output file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | apriori              | Nominal value. This field contains the last value used by the model.                 |
    | name                 | Parameter name. An arbitrary sequence of letters [A-Z,a-z], digits[0-9], and "."     |
    |                      | without spaces.                                                                      |
    | sigma                | Standard deviation of the parameter.                                                 |
    | time_past_j2000      | Time given in GPS seconds past J2000, whereby GipsyX uses following definition:      |
    |                      | J2000 is continuous seconds past Jan. 1, 2000 11:59:47 UTC.                          |
    | value                | Parameter value at the given time                                                    |

    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |
    """

    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8-
        # -189259500 -1.996741822282272e+04 -1.996741822282272e+04  0.000000000000000e+00 .Satellite.GPS09.Clk.Bias
        # -189259500  2.030700000000000e+00  2.030700000000000e+00  0.000000000000000e+00 .Satellite.GPS09.Antennas.Antenna1.MapCenterOffset.All.Z
        # -189259500  0.000000000000000e+00  0.000000000000000e+00  0.000000000000000e+00 .Satellite.GPS09.Antennas.Antenna1.MapCenterOffset.All.Y
        # -189259500  2.100000000000000e-01  2.100000000000000e-01  0.000000000000000e+00 .Satellite.GPS09.Antennas.Antenna1.MapCenterOffset.All.X
        # 375969900  3.759699000000000e+08  2.529488563752587e+08 -1.000000000000000e+00 Source.ID,nnriap026,/opt/GipsyX-Rc0.01/bin/rtgx,26160,/opt/GipsyX-Rc0.01/verify/bin/test/gd2e,iter3_Smoother.tdp
        # 375969900  1.000000000000000e-01  7.886203918776680e-02  2.421341208733073e-03 .Station.USN3.Trop.WetZ
        # 375969900  0.000000000000000e+00 -1.094752489564426e-04  3.578620059761463e-04 .Station.USN3.Trop.GradNorth
        # 375969900  0.000000000000000e+00  1.284821366066943e-04  2.947498515551939e-04 .Station.USN3.Trop.GradEast
        # 375969900  2.284140166572955e+00  2.284140166572955e+00  0.000000000000000e+00 .Station.USN3.Trop.DryZ
        # 375969900  0.000000000000000e+00  2.408635425085482e-02  2.044131803300346e-02 .Station.USN3.Clk.Bias
        # 375969900  7.577430000000000e-11  7.577430000000000e-11  0.000000000000000e+00 .Station.USN3.State.Vel.Z
        # 375969900  4.611710000000000e-13  4.611710000000000e-13  0.000000000000000e+00 .Station.USN3.State.Vel.Y
        # 375969900 -4.760540000000000e-10 -4.760540000000000e-10  0.000000000000000e+00 .Station.USN3.State.Vel.X
        # 375969900  3.985496028738000e+06  3.985496029611300e+06  1.247592374291492e-03 .Station.USN3.State.Pos.Z
        # 375969900 -4.842853529639000e+06 -4.842853530993107e+06  1.555844558271541e-03 .Station.USN3.State.Pos.Y
        # 375969900  1.112162034854000e+06  1.112162030692846e+06  6.422311946865588e-04 .Station.USN3.State.Pos.X
        # 375969900  3.633302454571610e+04  3.633302454571610e+04  0.000000000000000e+00 .Satellite.GPS63.Clk.Bias
        # 375969900  1.561300000000000e+00  1.561300000000000e+00  0.000000000000000e+00 .Satellite.GPS63.Antennas.Antenna1.MapCenterOffset.All.Z
        # 375969900  0.000000000000000e+00  0.000000000000000e+00  0.000000000000000e+00 .Satellite.GPS63.Antennas.Antenna1.MapCenterOffset.All.Y
        # 375969900  3.940000000000000e-01  3.940000000000000e-01  0.000000000000000e+00 .Satellite.GPS63.Antennas.Antenna1.MapCenterOffset.All.X
        # 375969900  8.729059297499520e+03  8.729059297499520e+03  0.000000000000000e+00 .Satellite.GPS62.Clk.Bias
        return dict(
            names=("time_past_j2000", "apriori", "value", "sigma", "name"),
            delimiter=(10, 23, 23, 23, 200),
            dtype=("f8", "f8", "f8", "f8", "U200"),
            autostrip=True,
        )

    #
    # WRITE DATA
    #
    def as_dataset(self) -> "Dataset":
        """Store Gipsy time dependent parameter data in a dataset

        Returns:
            Midgard Dataset where time dependent parameter data are stored with following fields:


       | Field               | Type              | Description                                                        |
       |---------------------|-------------------|--------------------------------------------------------------------|
       | receiver_clock      | numpy.ndarray     | Receiver clock parameter                                           |
       | satellite           | numpy.ndarray     | Satellite PRN number together with GNSS identifier (e.g. G07)      |
       | satellite_clock     | numpy.ndarray     | Satellite clock parameter                                          |
       | satellite_ant_pco   | PositionTable     | Satellite antenna phase center offset                              |
       | site_posvel         | PosVel            | Station coordinates and velocities                                 |
       | source_id           | numpy.ndarray     | Source ID                                                          |
       | station             | numpy.ndarray     | Station name list                                                  |
       | system              | numpy.ndarray     | GNSS identifier (e.g. G or E)                                      |
       | time                | Time              | Parameter time given as TimeTable object                           |
       | troposphere_zhd     | numpy.ndarray     | Zenith hydrostatic troposphere delay parameter                     |
       | troposphere_zwd     | numpy.ndarray     | Zenith hydrostatic troposphere delay parameter                     |
       | troposphere_ge      | numpy.ndarray     | Horizontal delay gradient in the East direction                    |
       | troposphere_gn      | numpy.ndarray     | Horizontal delay gradient in the North direction                   |
       
       The fields above are given for 'apriori', 'value' and 'sigma' Dataset collections.
        
        """
        # TODO: Handling of unit. Should be added to dataset fields.

        field = {
            "Clk Bias": DatasetField(None, None, "float"),  # can be either receiver or satellite clock bias
            "Antennas Antenna1 MapCenterOffset All Z": DatasetField("satellite_ant_pco", "Satellite", "position"),
            "State Pos Z": DatasetField("site_posvel", "Station", "posvel"),
            "Source": DatasetField("source_id", "Source", "float"),
            "Trop GradEast": DatasetField("troposphere_ge", "Station", "float"),
            "Trop GradNorth": DatasetField("troposphere_gn", "Station", "float"),
            "Trop DryZ": DatasetField("troposphere_zhd", "Station", "float"),
            "Trop WetZ": DatasetField("troposphere_zwd", "Station", "float"),
        }

        not_used_parameter = [
            "Antennas Antenna1 MapCenterOffset All X",
            "Antennas Antenna1 MapCenterOffset All Y",
            "State Pos X",
            "State Pos Y",
            "State Vel X",
            "State Vel Y",
            "State Vel Z",
        ]

        dset = dataset.Dataset(num_obs=len(self.data["time_past_j2000"]))
        dset.meta.update(self.meta)

        # Note: GipsyX uses continuous seconds past Jan. 1, 2000 11:59:47 UTC time format in TDP files. That means,
        #       GipsyX does not follow convention of J2000:
        #           1.01.2000 12:00:00     TT  (TT = GipsyX(t) + 13s)
        #           1.01.2000 11:59:27.816 TAI (TAI = TT - 32.184s)
        #           1.01.2000 11:58:55.816 UTC (UTC = TAI + leap_seconds = TAI - 32s)
        #           1.01.2000 11:59:08.816 GPS (GPS = TAI - 19s)
        #
        #       Therefore Time object initialized with TT time scale has to be corrected about 13 seconds.
        #
        # TODO: Introduce j2000 = 2451545.0 as constant or unit?
        dset.add_time(
            "time",
            val=Time((self.data["time_past_j2000"] + 13.0) * Unit.second2day + 2451545.0, scale="tt", fmt="jd").gps,
        )
        keep_idx = np.ones(dset.num_obs, dtype=bool)
        collections = ["apriori", "value", "sigma"]

        # Loop over all existing parameter names
        for name in set(self.data["name"]):
            category, identifier, parameter = name.replace(".", " ").split(maxsplit=2)

            if parameter in not_used_parameter:
                continue

            # Add station and satellite field to Dataset by first occurence
            if "Satellite" in category:
                if "satellite" not in dset.fields:
                    dset.add_text("satellite", val=np.repeat(None, dset.num_obs))
                    dset.add_text("system", val=np.repeat(None, dset.num_obs))

            if "Station" in category:
                if "station" not in dset.fields:
                    dset.add_text("station", val=np.repeat(identifier.lower(), dset.num_obs))

            if "Source" in category:
                idx = name == self.data["name"]

                for collection in collections:
                    field_name = f"{collection}.{field['Source'].name}"
                    dset.add_float(field_name, val=np.full(dset.num_obs, np.NaN))
                    dset[field_name][idx] = self.data["value"][idx]
                continue

            # Add parameter solution to Dataset
            if parameter in field.keys():

                idx = name == self.data["name"]

                if category == "Satellite":
                    sys = enums.get_value("gnss_3digit_id_to_id", identifier[0:3])
                    dset.system[idx] = sys
                    dset.satellite[idx] = sys + identifier[3:5]

                # Loop over 'apriori', 'value' and 'sigma' solutions, which are saved in separated Dataset collections
                for collection in collections:
                    field_name = f"{collection}.{field[parameter].name}"
                    log.debug(
                        f"Add dataset field '{field_name}' for parameter '{parameter}' and identifier '{identifier}'."
                    )

                    # Add float fields to Dataset
                    if field[parameter].dtype == "float":

                        # Note: "Clk Bias" parameter exists for receiver and satellite, therefore it has to be
                        #       distinguished based on the length of the 'identifier' (e.g. USNO or GPS64).
                        if parameter == "Clk Bias":
                            field_name = (
                                f"{collection}.satellite_clock"
                                if len(identifier) == 5
                                else f"{collection}.receiver_clock"
                            )

                        if field_name not in dset.fields:
                            dset.add_float(field_name, val=np.full(dset.num_obs, np.NaN))
                            dset[field_name][idx] = self.data[collection][idx]

                    # Add position fields to Dataset
                    elif field[parameter].dtype == "position":

                        if field_name not in dset.fields:
                            dset.add_position(
                                field_name, time=dset.time, system="trs", val=np.full((dset.num_obs, 3), np.NaN)
                            )

                        # Fill position field with data
                        tmp_sol = dict()

                        for item in [".X", ".Y", ".Z"]:
                            idx_item = name.replace(".Z", item) == self.data["name"]
                            tmp_sol[item] = self.data["value"][idx_item]
                            # Note: Only .Z dataset indices are used for saving position field in Dataset. .X and .Y are
                            #       not necessary anymore and are removed from Dataset by using "keep_idx" variable.
                            if not item == ".Z":
                                keep_idx[idx_item] = False

                        dset[field_name][idx] = np.vstack((tmp_sol[".X"], tmp_sol[".Y"], tmp_sol[".Z"])).T

                    # Add posvel fields to Dataset
                    elif field[parameter].dtype == "posvel":

                        if field_name not in dset.fields:
                            dset.add_posvel(
                                field_name, time=dset.time, system="trs", val=np.full((dset.num_obs, 6), np.NaN)
                            )

                        # Fill position field with data
                        tmp_sol = dict()
                        for item in [
                            "State.Pos.X",
                            "State.Pos.Y",
                            "State.Pos.Z",
                            "State.Vel.X",
                            "State.Vel.Y",
                            "State.Vel.Z",
                        ]:
                            idx_item = name.replace("State.Pos.Z", item) == self.data["name"]
                            tmp_sol[item] = self.data["value"][idx_item]
                            if not item == "State.Pos.Z":
                                keep_idx[idx_item] = False

                        dset[field_name][idx] = np.vstack(
                            (
                                tmp_sol["State.Pos.X"],
                                tmp_sol["State.Pos.Y"],
                                tmp_sol["State.Pos.Z"],
                                tmp_sol["State.Vel.X"],
                                tmp_sol["State.Vel.Y"],
                                tmp_sol["State.Vel.Z"],
                            )
                        ).T

            else:
                log.fatal(f"Parameter {parameter} is not defined.")

        dset.subset(keep_idx)  # Remove unnecessary entries (e.g. '.X' and '.Y' )

        return dset
