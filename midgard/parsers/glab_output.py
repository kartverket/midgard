"""A parser for reading gLAB output files

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='glab_output', file_path='glab_output.txt')
    data = p.as_dict()

Description:
------------


"""
# Standard library imports
from datetime import datetime, timedelta

# External library imports
import numpy as np
import pandas as pd

# Midgard imports
from midgard.collections import enums
from midgard.data import dataset
from midgard.dev import log
from midgard.dev import plugins
from midgard.parsers import Parser


@plugins.register
class GlabOutputParser(Parser):
    """A parser for reading gLAB output files

    The keys of the **data** dictionary are defined depending, which kind of gLAB output file is read. The values of 
    the **data** dictionary are represented by the gLAB colum values.

    Following **meta**-data are available after reading of gLAB files:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |
    """

    def read_data(self) -> None:
        """Read data from the data file

        Uses the pd.read_csv-function to parse the file. 
        """

        # Examples:
        #
        # MODEL    2018 032     0.00 GPS 15 C1C     0.08181  24633619.7730  24633625.9789  -4944029.0692  ...
        # FILTER   2018 032   300.00   3275754.0709    321110.6744   5445044.1853        -3.9960
        # OUTPUT 2018 032   300.00    1.6419   3275754.0709    321110.6744   5445044.1853     0.1589    -0.1907     ...
        #
        # gLAB file column definition
        column_def = {
            "model": [
                "year",
                "doy",
                "seconds",
                "system",
                "satellite",
                "obs_type",
                "flight_time",
                "measurement",
                "calculate",
                "sat_pos_x",
                "sat_pos_y",
                "sat_pos_z",
                "sat_vel_x",
                "sat_vel_y",
                "sat_vel_z",
                "gnss_range",
                "gnss_satellite_clock",
                "gnss_satellite_phase_center_offset",
                "gnss_receiver_phase_center",
                "gnss_receiver_antenna_reference_point",
                "gnss_relativistic_clock",
                "gnss_carrier_phase_wind_up",
                "troposphere_dT",
                "gnss_ionosphere",
                "gnss_relativistic_range",
                "gnss_total_group_delay",
                "solid_tides",
                "elevation",
                "azimuth",
            ],
            "filter": [
                "year",
                "doy",
                "seconds",
                "estimate_gnss_site_pos-x",
                "estimate_gnss_site_pos-y",
                "estimate_gnss_site_pos-z",
                "estimate_gnss_rcv_clock",
            ],
            "output": [
                "year",  # Year
                "doy",  # Day of year
                "seconds",  # Seconds of day
                "rms_cov",  # Square root of the sum of the covariance matrix. This is a measure of the convergence of the filter.
                "site_pos_x",  # Receiver X position [m]
                "site_pos_y",  # Receiver Y position [m]
                "site_pos_z",  # Receiver Z position [m]
                "site_pos_diff_x",  # Receiver X position - Nominal a priori X position [m]
                "site_pos_diff_y",  # Receiver Y position - Nominal a priori Y position [m]
                "site_pos_diff_z",  # Receiver Z position - Nominal a priori Z position [m]
                "sigma_site_pos_x",  # Receiver X formal error [m]
                "sigma_site_pos_y",  # Receiver Y formal error [m]
                "sigma_site_pos_z",  # Receiver Z formal error [m]
                "site_pos_lat",  # Receiver latitude [degrees]
                "site_pos_lon",  # Receiver longitude [degrees]
                "site_pos_height",  # Receiver height [m]
                "site_pos_diff_n",  # Receiver North difference in relation to nominal a priori position [m]
                "site_pos_diff_e",  # Receiver East difference in relation to nominal a priori position [m]
                "site_pos_diff_u",  # Receiver Up difference in relation to nominal a priori position [m]
                "sigma_site_pos_diff_n",  # Receiver formal error in North direction [m]
                "sigma_site_pos_diff_e",  # Receiver formal error in East direction [m]
                "sigma_site_pos_diff_u",  # Receiver formal error in Up direction [m]
                "gdop",  # Geometric Dilution of Precision (GDOP)
                "pdop",  # Positioning Dilution of Precision (PDOP)
                "tdop",  # Time Dilution of Precision (TDOP)
                "hdop",  # Horizontal Dilution of Precision (HDOP)
                "vdop",  # Vertical Dilution of Precision (VDOP)
                # "troposphere_dT",         # Zenith Tropospheric Delay (including nominal value) [m]
                # "troposphere_zwd",        # Zenith Tropospheric Delay (excluding nominal value) [m]
                # "sigma_troposphere_dT",   # Zenith Tropospheric Delay formal error [m]
            ],
        }

        # Read gLAB file
        df = pd.read_csv(self.file_path, sep="\s+", index_col=0, comment="#", skip_blank_lines=True)

        # Add column names depending on given dataframe index
        df.columns = column_def[list(set(df.index))[0].lower()]

        # Update data attribute
        self.data = {k: np.array(v) for k, v in df.to_dict(orient="list").items()}

    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            A dataset containing the data.
        """

        # Initialize dataset
        dset = dataset.Dataset()
        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(self.data["year"])

        # Add time
        epochs = list()
        for year, doy, seconds in zip(self.data["year"], self.data["doy"], self.data["seconds"]):
            epochs.append(datetime.strptime("{:.0f} {:.0f}".format(year, doy), "%Y %j") + timedelta(seconds=seconds))

        dset.add_time(name="time", val=epochs, scale="gps", fmt="datetime", write_level="operational")

        # Add system field
        if "system" in self.data.keys():
            systems = []
            for system in self.data["system"]:
                systems.append(enums.gnss_name_to_id[system.lower()].value)

            dset.add_text("system", val=systems)

        # Add system field
        if "satellite" in self.data.keys():
            satellites = []
            for system, satellite in zip(dset.system, self.data["satellite"]):
                satellites.append(system + str(satellite).zfill(2))

            dset.add_text("satellite", val=satellites)

        # Add text and float fields
        fields = set(self.data.keys()) - {"year", "doy", "seconds", "system", "satellite"}
        for field in fields:
            if self.data[field].dtype.kind in {"U", "S"}:  # Check if numpy type is string
                dset.add_text(field, val=self.data[field])
                continue

            dset.add_float(field, val=self.data[field])

        return dset
