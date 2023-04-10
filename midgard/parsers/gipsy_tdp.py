"""A parser for reading NASA JPL Gipsy time dependent parameter (TDP) file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsy_tdp', file_path='final.tdp')
    data = p.as_dict()

Description:
------------

Reads data from files in Gipsy time dependent parameter (TDP) format.

"""
# Standard library imports
from collections import namedtuple
from typing import Any, Dict

# Third party imports
import numpy as np

# Midgard imports
from midgard.collections import enums
from midgard.data import dataset
from midgard.data.time import Time
from midgard.dev import log, plugins
from midgard.math.unit import Unit
from midgard.parsers import LineParser


DatasetField = namedtuple("DatasetField", ["name", "dtype"])
DatasetField.__new__.__defaults__ = (None,) * len(DatasetField._fields)
DatasetField.__doc__ = """A convenience class for defining a dataset field properties

    Args:
        name  (str):             Dataset field name
        dtype (str):             Dataset data type
    """


@plugins.register
class GipsyTdpParser(LineParser):
    """A parser for reading Gipsy time dependent parameter (TDP) file

    Following **data** are available after reading Gipsy TDP output file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | apriori              | Nominal value. This field contains the last value used by the model.                 |
    | name                 | Parameter name.                                                                      |
    | sigma                | The sigma associated with the value of the parameter. A negative value indicates it  |
    |                      | should be used for interpolation by the file reader read_time_variation in           |
    |                      | $GOA/libsrc/time_variation. If no sigmas are computed by the smapper, a 1.0 will be  |
    |                      | placed here.                                                                         |
    | time_past_j2000      | Time given in GPS seconds past J2000.                                                |
    | value                | Accumulated value of the parameter at time and includes any nominal, or iterative    |
    |                      | correction. This is the only entry used by the model.                                |

    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |
    """

    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        TODO: Station name should be separated from parameter name.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8-
        #  564168900.0000   0.00000000000000     -8.944780025556555E-11  5.000E-04  TRPAZSINABSA
        #  564168900.0000   0.00000000000000     -9.807976019950053E-11  5.000E-04  TRPAZCOSABSA
        #  564190800.0000  9.542362619170887E-02  9.542423063851302E-02  0.500      WETZTROPABSA
        #  564190800.0000   0.00000000000000       286.902875647374       388.      STA BIASABSA
        #  564168899.7950   0.00000000000000     -3.338311367575861E-04  -1.00      PB GPS65  ABSA
        #  564168899.8000   0.00000000000000     -3.338311367575861E-04  4.091E-04  PB GPS65  ABSA
        return dict(
            names=("time_past_j2000", "apriori", "value", "sigma", "name"),
            delimiter=(15, 23, 23, 11, 20),
            dtype=("f8", "f8", "f8", "f8", "U20"),
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
       | :------------------ | :---------------- | :----------------------------------------------------------------- |
       | receiver_clock      | numpy.ndarray     | Receiver clock parameter                                           |
       | satellite           | numpy.ndarray     | Satellite SVN number together with GNSS identifier (e.g. G62)      |
       |                     |                   | related to ambiguity                                               |
       | ambiguity           | numpy.ndarray     | Ambiguity (phase bias) given for satellite vehicle number (SVN)    |                             |
       | site_posvel         | PosVel            | Station coordinates and velocities (not given and set to NaN for   |
       |                     |                   | consistency reason related to GipsyX TDP format)                   |
       | station             | numpy.ndarray     | Station name list                                                  |
       | system              | numpy.ndarray     | GNSS identifier (e.g. G or E)                                      |
       | time                | Time              | Parameter time given as TimeTable object                           |
       | trop_zenith_model   | numpy.ndarray     | Zenith hydrostatic/dry troposphere delay parameter                 |
       | trop_zenith_wet     | numpy.ndarray     | Zenith wet troposphere delay parameter                             |
       | trop_gradient_east  | numpy.ndarray     | Troposphere horizontal delay gradient in the East direction        |
       | trop_gradient_north | numpy.ndarray     | Troposphere horizontal delay gradient in the North direction       |
       
       The fields above are given for 'apriori', 'value' and 'sigma' Dataset collections.
        
        """
        # TODO: Handling of unit. Should be added to dataset fields.       
        field = {
            "PB": DatasetField("ambiguity", "float"),  
            "STA BIAS": DatasetField("receiver_clock", "float"),
            "STA X": DatasetField("site_posvel", "posvel"),
            "TRPAZCOS": DatasetField("trop_gradient_east", "float"),
            "TRPAZSIN": DatasetField("trop_gradient_north", "float"),
            "DRYZTROP": DatasetField("trop_zenith_dry", "float"),
            "WETZTROP": DatasetField("trop_zenith_wet", "float"),
        }

        not_used_parameter = [
            "DUM",
            "STA Y",
            "STA Z",
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
            if "station" not in dset.fields:
                station = name[-4:]
                dset.add_text("station", val=np.repeat(station.lower(), dset.num_obs))
            parameter = name.replace(station, "").strip() # Remove station identifier from to get parameter name

            if parameter in not_used_parameter:
                continue

            ## Add station and satellite field to Dataset by first occurence
            if parameter.startswith("PB"):
                if "satellite" not in dset.fields:
                    dset.add_text("satellite", val=np.repeat(None, dset.num_obs))
                    dset.add_text("system", val=np.repeat(None, dset.num_obs))
                
                sat = parameter.split()[1]
                sys = enums.get_value("gnss_3digit_id_to_id", sat[0:3])
                parameter = "PB"   #Note: Needed to check for 'float' field.
                    
            # Add parameter solution to Dataset
            if parameter in field.keys():

                idx = name == self.data["name"]
                
                if parameter == "PB":
                    dset.system[idx] = sys
                    dset.satellite[idx] = sys + sat[3:5]

                # Loop over 'apriori', 'value' and 'sigma' solutions, which are saved in separated Dataset collections
                for collection in collections:
                    field_name = f"{collection}.{field[parameter].name}"
                    log.debug(
                        f"Add dataset field '{field_name}' for parameter '{parameter}'."
                    )

                    
                    # Add float fields to Dataset
                    if field[parameter].dtype == "float":

                        if field_name not in dset.fields:
                            dset.add_float(field_name, val=np.full(dset.num_obs, np.NaN))
                            dset[field_name][idx] = self.data[collection][idx]

                    # Add posvel fields to Dataset
                    elif field[parameter].dtype == "posvel":

                        if field_name not in dset.fields:
                            dset.add_posvel(
                                field_name, time=dset.time, system="trs", val=np.full((dset.num_obs, 6), np.NaN)
                            )

                            # Fill position field with data
                            tmp_sol = dict()
                            for item in [
                                "STA X",
                                "STA Y",
                                "STA Z",
                                "VEL DUMMY 1", # Note: Velocity parameters are not defined in Gipsy TDP format, but they
                                "VEL DUMMY 2", #       are available in GipsyX TDP format. For consistency reason are
                                "VEL DUMMY 3", #       also (empty) velocity parameters defined.
                            ]:
                                idx_item = name.replace("STA X", item) == self.data["name"]
                                if self.data["value"][idx_item].size == 0:
                                    tmp_sol[item] = np.repeat(np.NaN, tmp_sol["STA X"].size)
                                else:
                                    tmp_sol[item] = self.data["value"][idx_item]
                                if not item == "STA X":
                                    keep_idx[idx_item] = False
    
                            dset[field_name][idx] = np.vstack(
                                (
                                    tmp_sol["STA X"],
                                    tmp_sol["STA Y"],
                                    tmp_sol["STA Z"],
                                    tmp_sol["VEL DUMMY 1"],
                                    tmp_sol["VEL DUMMY 2"],
                                    tmp_sol["VEL DUMMY 3"],
                                )
                            ).T


            else:
                log.fatal(f"Parameter {parameter} is not defined.")

        dset.subset(keep_idx)  # Remove unnecessary entries (e.g. '.X' and '.Y' )

        return dset
