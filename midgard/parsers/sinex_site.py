"""A parser for reading site related information from SINEX format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='sinex_site', file_path='sinex_site')
    data = p.as_dict()

Description:
------------

Reads station related information (e.g. approximated station coordinates, receiver and antenna type, station 
eccentricities, ...) from files in SINEX format. Following blocks are read:

            FILE/COMMENT   
            SITE/ID
            SITE/RECEIVER
            SITE/ANTENNA
            SITE/ECCENTRICITY
            SOLUTION/EPOCHS
            SOLUTION/ESTIMATE

Note, that FILE/COMMENT block is only used for reading reference frame information ('ref_frame'), which is added to 
SOLUTION/ESTIMATE dictionary.

"""
# Standard library imports
from typing import Callable, List
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.dev import plugins

# Where imports
from midgard.parsers._parser_sinex import SinexParser


@plugins.register
class SinexSiteParser(SinexParser):
    """A parser for reading site related information from SINEX format

    site - Site dictionary, whereby keys are the site identifiers and values are a site entry
           dictionary with the keys 'site_antenna', 'site_eccentricity', 'site_id', 'site_receiver',
           'solution_epoch' and 'solution_estimate'. The site dictionary has following structure:

              self.site[site] = { 'site_antenna':          [],  # SITE/ANTENNA SINEX block information
                                  'site_eccentricity':     [],  # SITE/ECCENTRICITY block information
                                  'site_id':               {},  # SITE/ID block information
                                  'site_receiver':         [],  # SITE/RECEIVER block information
                                  'solution_epoch':        [],  # SOLUTION/EPOCH block information
                                  'solution_estimate':     [],  # SOLUTION/ESTIMATE block information
              }

           with the site entry dictionary entries

              site_antenna[ii]      = { 'site_code':          site_code,
                                        'point_code':         point_code,
                                        'soln':               soln,
                                        'obs_code':           obs_code,
                                        'start_time':         start_time,
                                        'end_time':           end_time,
                                        'antenna_type':       antenna_type,
                                        'radome_type':        radome_type,
                                        'serial_number':      serial_number }

              site_eccentricity[ii] = { 'site_code':          site_code,
                                        'point_code':         point_code,
                                        'soln':               soln,
                                        'obs_code':           obs_code,
                                        'start_time':         start_time,
                                        'end_time':           end_time,
                                        'vector_1':           vector_1,
                                        'vector_2':           vector_2,
                                        'vector_3':           vector_3,
                                        'vector_type':        UNE }

              site_id               = { 'site_code':          site_code,
                                        'point_code':         point_code,
                                        'domes':              domes,
                                        'marker':             marker,
                                        'obs_code':           obs_code,
                                        'description':        description,
                                        'approx_lon':         approx_lon,
                                        'approx_lat':         approx_lat,
                                        'approx_height':      approx_height }

              site_receiver[ii]     = { 'site_code':          site_code,
                                        'point_code':         point_code,
                                        'soln':               soln,
                                        'obs_code':           obs_code,
                                        'start_time':         start_time,
                                        'end_time':           end_time,
                                        'receiver_type':      receiver_type,
                                        'serial_number':      serial_number,
                                        'firmware':           firmware }

              solution_epochs[ii]   = { 'site_code':          site_code,
                                        'point_code':         point_code,
                                        'soln':               soln,
                                        'obs_code':           obs_code,
                                        'start_epoch':        start_epoch,
                                        'end_epoch':          end_epoch,
                                        'mean_epoch':         mean_epoch }

              solution_estimate[ii] = { 'param_idx':          param_idx,
                                        'param_name':         param_name,
                                        'point_code':         point_code,
                                        'site_code':          site_code,
                                        'soln':               soln,
                                        'ref_epoch':          ref_epoch,
                                        'unit':               unit,
                                        'constraint':         constraint,
                                        'estimate':           estimate,
                                        'estimate_std':       estimate_std,
                                        'ref_frame':          ref_frame }  # Note: ref_frame taken from
                                                                           #   FILE/COMMENT block, if exists.

           The counter 'ii' ranges from 0 to n and depends on how many antenna type, receiver type,
           antenna monument and station coordinate changes were done at each site. If the time is defined as
           00:000:00000 in the SINEX file, then the value is saved as 'None' in the Sinex class.

    """

    def setup_parser(self):
        return (
            self.file_comment,
            self.site_id,
            self.site_receiver,
            self.site_antenna,
            self.site_eccentricity,
            self.solution_epochs,
            self.solution_estimate,
        )

    def parse_file_comment(self, data):
        """Parse FILE_COMMENT SINEX block"""
        for d in data:
            if d[0].startswith("LOCAL_GEODETIC_DATUM"):
                ref_frame = d[0].split(":")[1].strip()
                self.data["ref_frame"] = ref_frame

    def parse_site_id(self, data):
        """Parse SITE/ID SINEX block"""
        for d in data:
            site_key = d["site_code"].lower()
            self.data.setdefault(site_key, dict())
            self.data[site_key].setdefault("site_id", dict())
            self.data[site_key]["site_id"] = {n: d[n] for n in d.dtype.names}

    def parse_site_antenna(self, data):
        """Parse SITE/ANTENNA SINEX block"""
        for d in data:
            site_key = d["site_code"].lower()
            # TODO_hjegei: How to remove d['site_code'] from d?
            add_dict = {
                n: d[n] for n in d.dtype.names
            }  # Generate dictionary with all SINEX field entries
            add_dict["antenna_type"], add_dict["radome_type"] = d[
                "antenna_type"
            ].rsplit(" ", maxsplit=1)
            self.data.setdefault(site_key, dict())
            self.data[site_key].setdefault("site_antenna", list())
            self.data[site_key]["site_antenna"].append(add_dict)

    def parse_site_receiver(self, data):
        """Parse SITE/RECEIVER SINEX block"""
        for d in data:
            site_key = d["site_code"].lower()
            # TODO_hjegei: How to remove d['site_code'] from d?
            self.data.setdefault(site_key, dict())
            self.data[site_key].setdefault("site_receiver", list())
            self.data[site_key]["site_receiver"].append(
                {n: d[n] for n in d.dtype.names}
            )

    def parse_site_eccentricity(self, data):
        """Parse SITE/ECCENTRICITY SINEX block"""
        for d in data:
            site_key = d["site_code"].lower()
            # TODO_hjegei: How to remove d['site_code'] from d?
            self.data.setdefault(site_key, dict())
            self.data[site_key].setdefault("site_eccentricity", list())
            self.data[site_key]["site_eccentricity"].append(
                {n: d[n] for n in d.dtype.names}
            )

    def parse_solution_epochs(self, data):
        """Parse SOLUTION/EPOCHS SINEX block"""
        for d in data:
            site_key = d["site_code"].lower()
            # TODO_hjegei: How to remove d['site_code'] from d?
            self.data.setdefault(site_key, dict())
            self.data[site_key].setdefault("solution_epochs", list())
            self.data[site_key]["solution_epochs"].append(
                {n: d[n] for n in d.dtype.names}
            )

    def parse_solution_estimate(self, data):
        """Parse SOLUTION/ESTIMATE SINEX block"""
        for d in data:
            site_key = d["site_code"].lower()
            # TODO_hjegei: How to remove d['site_code'] from d?
            self.data.setdefault(site_key, dict())
            self.data[site_key].setdefault("solution_estimate", list())
            self.data[site_key]["solution_estimate"].append(
                {n: d[n] for n in d.dtype.names}
            )

    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing"""
        return [
            self._add_ref_frame_to_solution_estimate,
        ]

    def _add_ref_frame_to_solution_estimate(self) -> None:
        """Add "ref_frame" to SOLUTION/ESTIMATE block entries

        "ref_frame" is removed from self.data after adding "ref_frame" to SOLUTION/ESTIMATE block entries.
        """

        if "ref_frame" in self.data:
            for key in self.data.keys():
                if len(key) == 4 and type(key) == str:  # check after 4-digit string
                    if "solution_estimate" in self.data[key]:
                        for idx in range(0, len(self.data[key]["solution_estimate"])):
                            self.data[key]["solution_estimate"][idx][
                                "ref_frame"
                            ] = self.data["ref_frame"]

            del self.data["ref_frame"]

    def as_dataset(self) -> "Dataset":
        """Store output in a dataset

        Returns:
            Midgard Dataset containing the following information

        | Field            | Type          | Description |
        | :--------------- | :------------ | :------------------------------------------ |
        | site_pos         | Position      | x, y and z station coordinates              |
        | site_pos_x_sigma | numpy.ndarray | Standard deviation for x station coordinate |
        | site_pos_y_sigma | numpy.ndarray | Standard deviation for y station coordinate |
        | site_pos_z_sigma | numpy.ndarray | Standard deviation for z station coordinate |
        | station          | numpy.ndarray | Station name list                           |
        | time             | Time          | Parameter time given as TimeTable object    |


            and following Dataset `meta` data:

       |  Entry              | Type  | Description                                                                    |
       | :------------------ | :---- | :----------------------------------------------------------------------------- |
       | \__data_path__      | str   | File path                                                                      |
       | \__parser_name__    | str   | Parser name                                                                    |
       | create_agency       | str   | Agency creating the file                                                       |
       | create_epoch        | str   | Creation time of file in ISO format (e.g. 2025-01-14T00:00:00)                 |
       | data_agency         | str   | Agency providing the data in SINEX TMS format                                  |
       | end_epoch           | str   | End time of timeseries solution as date in ISO format                          |
       |                     |       | (e.g. 2025-01-14T00:00:00)                                                     |
       | obs_code            | str   | Observation code consistent with IERS convention                               |
       | snx_version         | float | SINEX TMS version                                                              |
       | start_epoch         | str   | Start time of timeseries solution as date in ISO format                        |
       |                     |       | (e.g. 2025-01-18T00:00:00)                                                     |

        """

        num_stations = len(self.data.keys())
        dset = dataset.Dataset(num_obs=num_stations)

        # Save selected parts of meta information
        dset.meta.update(self.meta)
        for key in ["constraint_code", "num_param", "solution_contents"]:
            del dset.meta[key]
        for key in ["create_epoch", "start_epoch", "end_epoch"]:  # Convert datetime to str
            dset.meta[key] = dset.meta[key].isoformat()

        # Same epoch for all stations
        time_array = [
            self.data[sta]["solution_epochs"][0]["mean_epoch"]
            for sta in self.data.keys()
        ]
        dset.add_time("time", time_array, scale="utc", fmt="datetime")

        pos_array = []
        sigma_x_array = []
        sigma_y_array = []
        sigma_z_array = []
        stations = []

        for station in self.data.keys():
            pos_station = np.array(
                (
                    self.data[station]["solution_estimate"][0]["estimate"],
                    self.data[station]["solution_estimate"][1]["estimate"],
                    self.data[station]["solution_estimate"][2]["estimate"],
                )
            )
            pos_array.append(pos_station)
            sigma_x = self.data[station]["solution_estimate"][0]["estimate_std"]
            sigma_y = self.data[station]["solution_estimate"][1]["estimate_std"]
            sigma_z = self.data[station]["solution_estimate"][2]["estimate_std"]
            sigma_x_array.append(sigma_x)
            sigma_y_array.append(sigma_y)
            sigma_z_array.append(sigma_z)
            stations.append(station)

        # Add position information
        dset.add_position("site_pos", pos_array, system="trs")
        dset.add_float("site_pos_x_sigma", sigma_x_array, unit="meter")
        dset.add_float("site_pos_y_sigma", sigma_y_array, unit="meter")
        dset.add_float("site_pos_z_sigma", sigma_z_array, unit="meter")
        dset.add_text("station", stations)

        return dset
