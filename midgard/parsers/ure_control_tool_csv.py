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
from typing import Callable, List

# External library import
import numpy as np


# Midgard imports
from midgard.data import dataset
from midgard.data import position
from midgard.dev import plugins
from midgard.parsers.csv_ import CsvParser


@plugins.register
class UreControlToolCsvParser(CsvParser):
    """A parser for reading URE Control Tool CSV output files

    The URE Control Tool CSV data header line is used to define the keys of the **data** dictionary. The values of the 
    **data** dictionary are represented by the URE Control Tool CSV colum values.

    """
    
    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        """
        return [
            self._remove_additional_header_lines,
        ]
        
    def _remove_additional_header_lines(self) -> None:
        """Remove additional header lines

        It can happen that URE Control Tool CSV uses additional header lines in the file. These lines will be removed.
        
        TODO: Exists better solution would be, e.g. to take into account these already by reading step csv_.read_data?
        """
        if "IOD" in self.data["IOD"]:
        
            # Get index of additional header lines 
            idx = self.data["IOD"]=="IOD"
            
            # Keep only field lines, which are not header lines [~idx]
            for field in self.data.keys():
                self.data[field] = self.data[field][~idx]


    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            Midgard Dataset where URE Control tool data are stored with following fields (depending if fields are 
            available from on the URE Control tool output):

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
        | used_iode             | IOD         | Used Issue of data                                                     |
        """

        field_ure_control_tool_to_where = {
            "dAC(m)": "sqrt_a2_c2",
            "dB_mean(m)": "clk_diff_dt_mean",
            "dH_mean(m)": "clk_diff_with_dt_mean",
            "dR(m)": "dradial",
            "d3D(m)": "orb_diff_3d",
            "IOD": "used_iode",
            "SVID": "satellite",
            "URE_Av_mean(m)": "sisre",
        }
        
        float_field_def = [
             'AdjBGD-DCB_mean(m)',
             'AdjBGD-DCB_med(m)',
             'IOD',
             'URE_Av_mean(m)',
             'URE_Av_med(m)',
             'URE_WUL_mean(m)',
             'URE_WUL_med(m)',
             'd3D(m)',
             'dAC(m)',
             'dBGD_mean(m)',
             'dBGD_med(m)',
             'dB_mean(m)',
             'dB_med(m)',
             'dH_mean(m)',
             'dH_med(m)',
             'dR(m)',
        ]
        
        # Initialize dataset        
        dset = dataset.Dataset(num_obs=len(self.data["SVID"]))
        dset.meta.update(self.meta)

        # Add time             
        dset.add_time(
            "time",
            val=[
                dateutil.parser.parse(self.data["YY/MM/DD HH:MM:SS"][i])
                for i in range(0, dset.num_obs)
            ],
            scale="gps",
            fmt="datetime",
            write_level="operational",
        )

        # Add system field
        dset.add_text("system", val=[s[0:1] for s in self.data["SVID"]])

        # Add posvel delta field
        ref_pos = position.PosVel(np.repeat(np.array([[0,0,0,0,0,0]]), dset.num_obs, axis=0), system="trs")
        dset.add_posvel_delta(
            name="orb_diff",
            val=np.vstack((
                        self.data["dX(m)"], 
                        self.data["dY(m)"], 
                        self.data["dZ(m)"], 
                        np.repeat(0, dset.num_obs), 
                        np.repeat(0, dset.num_obs), 
                        np.repeat(0, dset.num_obs), 
            )).T,
            system="trs",
            ref_pos=ref_pos,
        )

        # Define fields to save in dataset
        remove_fields = {"YY/MM/DD HH:MM:SS", "dX(m)", "dY(m)", "dZ(m)"}
        fields = set(self.data.keys()) - remove_fields

        # Add text and float fields
        for field in fields:

            where_fieldname = (
                field_ure_control_tool_to_where[field]
                if field in field_ure_control_tool_to_where.keys()
                else field.lower()
            )
            where_fieldname = where_fieldname.replace("(m)", "")  # Remove unit (m) from field name

            if self.data[field].dtype.kind in {"U", "S"} and field not in float_field_def:  # Check if numpy type is string
                dset.add_text(where_fieldname, val=self.data[field])
                continue

            dset.add_float(where_fieldname, val=self.data[field], unit="meter")
            
        return dset
            

