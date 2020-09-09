"""A parser for reading NASA JPL GipsyX residual file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_residual', file_path='finalResiduals.out')
    data = p.as_dict()

Description:
------------

Reads data from files in GipsyX residual format.

"""
# Standard library imports
from typing import Callable, List

# External library imports
import numpy as np

# Midgard imports
from midgard.collections import enums
from midgard.data import dataset
from midgard.data.time import Time
from midgard.dev import plugins
from midgard.files import files
from midgard.math.unit import Unit
from midgard.parsers import Parser


@plugins.register
class GipsyxResidualParser(Parser):
    """A parser for reading GipsyX residual file

    Following **data** are available after reading GipsyX residual output file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | azimuth              | Azimuth from receiver                                                                |
    | azimuth_sat          | Azimuth from satellite                                                               |
    | data_type            | Data type (e.g. IonoFreeC_1P_2P, IonoFreeL_1P_2P)                                    |
    | deleted              | Residuals are deleted, marked with True or False.                                    |
    | elevation            | Elevation from receiver                                                              |
    | elevation_sat        | Elevation from satellite                                                             |
    | residual             | Post-fit residual                                                                    |
    | satellite            | Satellite name                                                                       |
    | station              | Station name                                                                         |
    | time_past_j2000      | Time given in GPS seconds past J2000, whereby GipsyX uses following definition:      |
    |                      | J2000 is continuous seconds past Jan. 1, 2000 11:59:47 UTC.                          |


    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |
    """

    def read_data(self) -> None:
        """Read data from the data file
        """

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8----+----+---
        # 634737600 {TRO1(1)-GPS63(1)} IonoFreeL_1W_2W -0.00474853620107751 28.6008 264.741 77.7496 254.441
        # 634737600 {TRO1(1)-GPS51(1)} IonoFreeL_1W_2W 0.0312436036183499 28.4875 72.4179 77.7914 317.321 DELETED
        # 634737600 {TRO1(1)-GPS46(1)} IonoFreeL_1W_2W 0.00156999072351027 54.4754 253.075 81.8949 103.653
        # 634737600 {TRO1(1)-GPS44(1)} IonoFreeL_1W_2W -0.00224204588448629 28.7255 325.576 78.0873 41.2581

        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            self._parse_file(fid)

    def _parse_file(self, fid: "_io.TextIOWrapper") -> None:
        """Parse file
        
        Args:
            fid: File handle
        """
        names = [
            "time_past_j2000",
            "station_satellite",
            "data_type",
            "residual",
            "elevation",
            "azimuth",
            "elevation_sat",
            "azimuth_sat_deleted",
        ]
        for line in fid:
            words = line.split(maxsplit=7)
            for name, word in zip(names, words):
                word = word if name in ["station_satellite", "data_type", "azimuth_sat_deleted"] else float(word)
                self.data.setdefault(name, list()).append(word)

    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        
        Returns:
            List with postprocessor function calls
        """
        return [self._separate_station_from_satellite, self._separate_azimuth_sat_from_deleted]

    def _separate_station_from_satellite(self) -> None:
        """Separate station from satellite names in variable 'station_satellite'
        """

        # Read entries such {TRO1(1)-GPS63(1)} and extract station and satellite name of it
        for entry in self.data["station_satellite"]:
            station, satellite = entry.split("-", 1)
            self.data.setdefault("station", list()).append(station[1:5].lower())
            self.data.setdefault("satellite", list()).append(satellite[0:5])

        del self.data["station_satellite"]

    def _separate_azimuth_sat_from_deleted(self) -> None:
        """Separate satellite azimuth from deleted entry
        """

        # Read entries such '21.9746 DELETED' and separate this two entries from each other
        for entry in self.data["azimuth_sat_deleted"]:
            words = entry.split(maxsplit=1)
            azimuth_sat, deleted = (words[0], True) if len(words) > 1 else (words[0], False)
            self.data.setdefault("azimuth_sat", list()).append(azimuth_sat)
            self.data.setdefault("deleted", list()).append(deleted)

        del self.data["azimuth_sat_deleted"]

    #
    # WRITE DATA
    #
    def as_dataset(self) -> "Dataset":
        """Store Gipsy residual data in a dataset

        Returns:
            Midgard Dataset where residual data are stored with following fields:


       | Field               | Type              | Description                                                        |
       |---------------------|-------------------|--------------------------------------------------------------------|
       | azimuth             | numpy.ndarray     | Azimuth from receiver                                              |
       | azimuth_sat         | numpy.ndarray     | Azimuth from satellite                                             |
       | elevation           | numpy.ndarray     | Elevation from receiver                                            |
       | elevation_sat       | numpy.ndarray     | Elevation from satellite                                           |
       | data_type           | numpy.ndarray     | Data type (e.g. IonoFreeC_1P_2P, IonoFreeL_1P_2P)                  |
       | residual            | numpy.ndarray     | Post-fit residual                                                  |
       | satellite           | numpy.ndarray     | Satellite PRN number together with GNSS identifier (e.g. G07)      |
       | station             | numpy.ndarray     | Station name list                                                  |
       | system              | numpy.ndarray     | GNSS identifier (e.g. G or E)                                      |
       | time                | Time              | Parameter time given as TimeTable object                           |
        
        """
        # TODO: Handling of unit. Should be added to dataset fields.

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
            val=Time(
                (np.array(self.data["time_past_j2000"]) + 13.0) * Unit.second2day + 2451545.0, scale="tt", fmt="jd"
            ).gps,
        )

        # Loop over Dataset fields
        for field in self.data.keys():
            if field == "time_past_j2000":
                continue

            if field in ["data_type", "satellite", "station"]:

                if field == "satellite":
                    dset.add_text("satellite", val=np.repeat(None, dset.num_obs))
                    dset.add_text("system", val=np.repeat(None, dset.num_obs))
                    for sat in set(self.data["satellite"]):
                        idx = sat == np.array(self.data["satellite"])
                        sys = enums.get_value("gnss_3digit_id_to_id", sat[0:3])
                        dset.system[idx] = sys
                        dset.satellite[idx] = sys + sat[3:5]
                else:
                    dset.add_text(field, val=self.data[field])

            elif field == "deleted":
                dset.add_bool(field, val=self.data[field])

            else:
                dset.add_float(field, val=self.data[field])

        return dset
