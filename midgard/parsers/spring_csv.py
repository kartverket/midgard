"""A parser for reading Spring CSV output files

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='spring_csv', file_path='ADOP20473_0000.csv')
    data = p.as_dict()

Description:
------------

Reads data from files in Spring CSV output format. The header information of the Spring CSV file is not read (TODO).
"""

# Standard library import
import dateutil.parser

# Midgard imports
from midgard.data import dataset
from midgard.parsers.csv_ import CsvParser
from midgard.dev import plugins


@plugins.register
class SpringCsvParser(CsvParser):
    """A parser for reading Spring CSV output files

    The Spring CSV data header line is used to define the keys of the **data** dictionary. The values of the **data** 
    dictionary are represented by the Spring CSV colum values.

    Depending on the Spring CSV following dataset fields can be available:

    | Field               | Description                                                                           |
    |---------------------|---------------------------------------------------------------------------------------|
    | acquiredsat         | Number of acquired satellites (TODO?)                                                 |
    | gdop                | Geometric dilution of precision                                                       |
    | hdop                | Horizontal dilution of precision                                                      |
    | pdop                | Position (3D) dilution of precision                                                   |
    | satinview           | Number of satellites in view                                                          |
    | system              | GNSS identifier based on RINEX definition (e.g. G: GPS, E: Galileo)                   |
    | tdop                | Time dilution of precision                                                            |
    | time                | Observation time given as Time object                                                 |
    | usedsat             | Number of used satellites                                                             |
    | vdop                | Vertical dilution of precision                                                        |
    | ...                 | ...                                                                                   |
    """

    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            A dataset containing the data.
        """
        # Spring constellation definition
        system_def = {
            "0": "",  # Unknown
            "1": "G",  # GPS
            "2": "R",  # GLONASS
            "3": "S",  # SBAS
            "4": "E",  # Galileo
            "5": "C",  # BeiDou
            "6": "J",  # QZSS
        }

        # Initialize dataset
        dset = dataset.Dataset()
        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(self.data["GPSEpoch"])

        # Add time
        dset.add_time(
            name="time",
            val=[dateutil.parser.parse(v.replace("UTC", "")) for v in self.data["UTCDateTime"]],
            scale="utc",
            fmt="datetime",
            write_level="operational",
        )

        # Add system field based on Constellation column
        if "Constellation" in self.data.keys():
            dset.add_text("system", val=[system_def[str(value)] for value in self.data["Constellation"]])

        # Add satellite field based on PRN column
        if "PRN" in self.data.keys():
            prn_data = []
            for prn in self.data["PRN"]:
                if prn >= 71 and prn <= 140:  # Handling of Galileo satellites
                    prn_data.append("E" + str(prn - 70).zfill(2))
                else:
                    log.fatal(f"Spring PRN number '{prn}' is unknown.")

            dset.add_text("satellite", val=prn_data)

        # Define fields to save in dataset
        remove_time_fields = {"Constellation", "GPSEpoch", "GPSWeek", "GPSSecond", "PRN", "", "UTCDateTime"}
        fields = set(self.data.keys()) - remove_time_fields

        # Add text and float fields
        for field in fields:

            if self.data[field].dtype.kind in {"U", "S"}:  # Check if numpy type is string
                dset.add_text(field.lower(), val=self.data[field])
                continue

            dset.add_float(field.lower(), val=self.data[field])

        return dset
