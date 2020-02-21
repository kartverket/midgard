"""A parser for reading URE Control Tool CSV output files

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='ure_control_tool_csv', file_path='G_GAL258_E1E5a_URE-AllPRN_190301.csv')
    data = p.as_dict()

Description:
------------

Reads data from files in URE Control Tool CSV output format. The header information of the URE Control Tool CSV file is
not read (TODO).
"""

# Standard library import
import dateutil.parser

# External library import
import numpy as np


# Midgard imports
from midgard.dev import log
from midgard.dev import plugins
from midgard.parsers.csv_ import CsvParser


@plugins.register
class UreControlToolCsvParser(CsvParser):
    """A parser for reading URE Control Tool CSV output files

    The URE Control Tool CSV data header line is used to define the keys of the **data** dictionary. The values of the 
    **data** dictionary are represented by the URE Control Tool CSV colum values.

    """

    def write_to_dataset(self, dset) -> "Dataset":
        """Return the parsed data as a Dataset

        Args:
            dset (Dataset): The Dataset. Depending on the Spring CSV following dataset fields can be available:

        | Field                 | Former name | Description                                                            |
        |-----------------------|--------------------------------------------------------------------------------------|
        | adjbgd-dcb_mean       |             |                                                                        |
        | adjbgd-dcb_med        |             |                                                                        |
        | clk_diff_dt_mean      | dB_mean     | MEAN clock offset determined in each epoch                             |
        | clk_diff_with_dt_mean | dH_mean     | Satellite clock correction difference corrected for satellite bias and |
        |                       |             | the MEAN constellation clock offset in each epoch                      |    
        | dr                    |             | Satellite coordinate difference between broadcast and precise ephemeris|
        |                       |             | in radial direction in [m]                                             |
        | dx                    |             | Satellite coordinate difference between broadcast and precise ephemeris|
        |                       |             | for x-coordinate                                                       |
        | dy                    |             | Satellite coordinate difference between broadcast and precise ephemeris|
        |                       |             | for y-coordinate                                                       |
        | dz                    |             | Satellite coordinate difference between broadcast and precise ephemeris|
        |                       |             | for z-coordinate                                                       |
        | dh_med                |             | Satellite clock correction difference corrected for satellite bias and |
        |                       |             | the MEDIAN clock offset in each epoch                                  |
        | db_med                |             | MEDIAN constellation clock offset determined in each epoch             |
        | dbgd_mean             |             |                                                                        |
        | dbgd_med              |             |                                                                        |
        | orb_diff_3d           | d3D         | 3D orbit difference                                                    |
        | satellite             | SVID        | Satellite number                                                       |
        | sqrt_a2_c2            | dAC         | sqrt(a^2 + c^2)                                                        |
        | system                |             | System identifier                                                      |
        | sisre                 | URE_Av_mean | Global average user range error (signal-in-space range error) with use |
        |                       |             | of MEAN constellation clock offset                                     |
        | ure_av_med            |             | Global average user range error (signal-in-space range error) with use |
        |                       |             | of MEDIAN constellation clock offset                                   |
        | ure_wul_mean          |             | Global average user range error for worst user location with use of    |
        |                       |             | MEAN constellation clock offset                                        |
        | ure_wul_med           |             | Global average user range error for worst user location with use of    |
        |                       |             | MEDIAN constellation clock offset                                      |
        """

        field_ure_control_tool_to_where = {
            "dAC(m)": "sqrt_a2_c2",
            "dB_mean(m)": "clk_diff_dt_mean",
            "dH_mean(m)": "clk_diff_with_dt_mean",
            "dR(m)": "dradial",
            "d3D(m)": "orb_diff_3d",
            "SVID": "satellite",
            "URE_Av_mean(m)": "sisre",
        }

        # Initialize dataset
        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(self.data["dX(m)"])

        # Add time
        dset.add_time(
            "time",
            val=[
                dateutil.parser.parse(self.data["YYYY/MM/DD"][i] + " " + self.data["HH:MM:SS"][i])
                for i in range(0, dset.num_obs)
            ],
            scale="gps",
            fmt="datetime",
            write_level="operational",
        )

        # Add system field
        dset.add_text("system", val=[s[0:1] for s in self.data["SVID"]])

        # Add position field
        dset.add_position(
            "orb_diff", itrs=np.vstack((self.data["dX(m)"], self.data["dY(m)"], self.data["dZ(m)"])).T, time="time"
        )

        # Define fields to save in dataset
        remove_fields = {"YYYY/MM/DD", "HH:MM:SS", "dX(m)", "dY(m)", "dZ(m)"}
        fields = set(self.data.keys()) - remove_fields

        # Add text and float fields
        for field in fields:

            where_fieldname = (
                field_ure_control_tool_to_where[field]
                if field in field_ure_control_tool_to_where.keys()
                else field.lower()
            )
            where_fieldname = where_fieldname.replace("(m)", "")  # Remove unit (m) from field name

            if self.data[field].dtype.kind in {"U", "S"}:  # Check if numpy type is string
                dset.add_text(where_fieldname, val=self.data[field])
                continue

            dset.add_float(where_fieldname, val=self.data[field], unit="meter")
