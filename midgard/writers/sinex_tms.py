"""Write timeseries file in SINEX TMS format
"""


# Standard library imports
from collections import namedtuple, OrderedDict
from datetime import datetime
from operator import attrgetter
from pathlib import PosixPath
from typing import List, Union

# Midgard imports
from midgard.dev import log, plugins
from midgard.data.position import Position
from midgard.data.time import Time
from midgard.files import files

_SECTION = "_".join(__name__.split(".")[-1:])

DataType = namedtuple(
    "DataType", ["unit", "format", "description"]
)
DataType.__new__.__defaults__ = (None,) * len(DataType._fields)
DataType.__doc__ = """A convenience class for defining a data type 

    Args:
        unit (str):            Unit of data type
        format (str):          Data type format definition
        description  (str):    Description to given data type acronym
    """

DATA_TYPES = {
    # Date data types
    "GPSWEEK": DataType("", "7s", "Date as GPS week together with GPS day in format wwwwd (e.g. 22644)"),
    "JD": DataType("", "11.1f", "Date as Julian Day (e.g. 2460096.5)"),
    "MJD": DataType("", "9.1f", "Date as Modified Julian Day (e.g. 60096.0)"),
    "YEAR": DataType("y", "12.5f", "Date as decimal year (2023.4137)"),
    "YYYY-DDD": DataType("", "10s", "Date in format year and day of year (e.g. 2023-152)"),
    "YYYY-MM-DD": DataType("", "12s", "Date in format year, month and day (e.g. 2023-06-01)"),
    "HH:MM:SS": DataType("", "10s", "Time in format hour, minute and second (e.g. 01:34:15)"),

    # General data types
    #"STATION": DataType("", "Station name"),
    "EAST": DataType("m", "12.4f", "East component of topocentric site coordinates"),
    "NORTH": DataType("m", "12.4f", "North component of topocentric site coordinates"),
    "UP": DataType("m", "12.4f", "Up component of topocentric site coordinates"),
    "SIG_EAST": DataType("m", "10.4f", "Standard deviation of topocentric East component"),
    "SIG_NORTH": DataType("m", "10.4f", "Standard deviation of topocentric North component"),
    "SIG_UP": DataType("m", "10.4f", "Standard deviation of topocentric Up component"),
    "CORR_EN": DataType("", "10.4f", "Correlation between East and North component"),
    "CORR_EU": DataType("", "10.4f", "Correlation between East and Up component"),
    "CORR_NU": DataType("", "10.4f", "Correlation between North and Up component"),
    "X": DataType("m", "14.4f", "X-coordinate of geocentric site coordinates"),
    "Y": DataType("m", "14.4f", "Y-coordinate of geocentric site coordinates"),
    "Z": DataType("m", "14.4f", "Z-coordinate of geocentric site coordinates"),
    "SIG_X": DataType("m", "10.4f", "Standard deviation of geocentric X-coordinate"),
    "SIG_Y": DataType("m", "10.4f", "Standard deviation of geocentric Y-coordinate"),
    "SIG_Z": DataType("m", "10.4f", "Standard deviation of geocentric Z-coordinate"),
    "CORR_XY": DataType("", "10.4f", "Correlation between X- and Y-coordinate "),
    "CORR_XZ": DataType("", "10.4f", "Correlation between X- and Z-coordinate"),
    "CORR_YZ": DataType("", "10.4f", "Correlation between Y- and Z-coordinate"),
    "NUM_OBS": DataType("", "8d", "Number of observations used by generation of daily site coordinate solution"),
    "RES_EAST": DataType("m", "12.4f", "Residual of topocentric East component, which represent the difference "
                                        "between the East observation and the calculated model (e.g. linear trend) "),
    "RES_NORTH": DataType("m", "12.4f", "Residual of topocentric North component, which represent the difference "
                                        "between the North observation and the calculated model (e.g. linear trend) "),
    "RES_UP": DataType("m", "12.4f", "Residual of topocentric Up component, which represent the difference "
                                        "between the Up observation and the calculated model (e.g. linear trend) "),
    "MOD_EAST": DataType("m", "12.4f", "Calculated model for topocentric East component time-series data"),
    "MOD_NORTH": DataType("m", "12.4f", "Calculated model for topocentric North component time-series data"),
    "MOD_UP": DataType("m", "12.4f", "Calculated model for topocentric Up component time-series data"),
}

# Definition of data type and corresponding dataset field.
DATA_FIELD_TYPES = OrderedDict({
    "YYYY-MM-DD": "time.utc.date",
    "YEAR": "time.utc.decimalyear",
    #"STATION": "station",
    "X": "site_pos.trs.x",
    "Y": "site_pos.trs.y",
    "Z": "site_pos.trs.z",
    "SIG_X": "site_pos_x_sigma",
    "SIG_Y": "site_pos_y_sigma",
    "SIG_Z": "site_pos_z_sigma",
    "CORR_XY": "site_pos_xy_correlation",
    "CORR_XZ": "site_pos_xz_correlation",
    "CORR_YZ": "site_pos_yz_correlation",
    "EAST": "dsite_pos.enu.east",
    "NORTH": "dsite_pos.enu.north",
    "UP": "dsite_pos.enu.up",
    "SIG_EAST": "site_pos_east_sigma",
    "SIG_NORTH": "site_pos_north_sigma",
    "SIG_UP": "site_pos_up_sigma",
    "CORR_EN": "site_pos_en_correlation",
    "CORR_EU": "site_pos_eu_correlation",
    "CORR_NU": "site_pos_nu_correlation",
})


@plugins.register
def sinex_tms(
        dset: "Dataset",
        station: str,
        file_path: PosixPath, 
        contact: str,
        data_agency: str,
        file_agency: str,
        input_: str,
        organization: str,
        software: str,
        version: str,
) -> None:
    """Write timeseries file in SINEX TMS format

    Args:
        dset:  A dataset containing the data.
    """
    log.info(f"Write file {file_path}")

    with files.open(file_path=file_path, create_dirs=True, mode="wt") as fid:
        block = TimeseriesBlocks(dset, fid, station, contact, data_agency, file_agency, input_, organization, software, version)

        # Write the blocks
        block.write_block("header_line")
        block.write_block("file_reference")
        if "EAST" in block.data_field_types.keys():
            block.write_block("timeseries_ref_coordinate")
        block.write_block("timeseries_columns")
        block.write_block("timeseries_data")

    fid.close()


class TimeseriesBlocks:
    """
    This class takes care of the writing of the different blocks in the SINEX TMS files
    """

    def __init__(
                self, 
                dset: "Dataset", 
                fid: "FileHandle", 
                station: str, 
                contact: str, 
                data_agency: str, 
                file_agency: str, 
                input_: str = "", 
                organization: str = "", 
                software: str = "", 
                version: str="001",
                data_field_types: Union[None, OrderedDict[str, str]] = None,
    ):
        """Set up a new TimeseriesBlock object

        Args:
            dset:              A dataset containing the data
            fid:               File handle
            station:           Station name
            contact:           Address of the relevant contact e-mail
            data_agency:       3-digit acronym of data agency, which provides the SINEX files with data
            file_agency:       3-digit acronym of file agency, which generates the timeseries file
            input_:            Brief description of the input used to generate this solution
            organization:      Full name of organization(s) gathering/altering the file contents
            software:          Name of software, which has generated the file
            version:           Unique 3-digit version number identifier of the product
            data_field_types:  Ordered dictionary with definition of data type and corresponding dataset field, e.g.:
                                        data_field_types = OrderedDict({
                                            YEAR = "time.utc.decimalyear",
                                            YYYY-MM-DD = "time.utc.date",
                                            X = "site_pos.trs.x",
                                            Y = "site_pos.trs.y",
                                            Z = "site_pos.trs.z",
                                        })
        """
        self.dset = dset
        self.fid = fid
        self.station = station
        self.contact = contact
        self.data_agency = data_agency
        self.file_agency = file_agency
        self.input = input_
        self.organization = organization
        self.software = software
        self.version = version

        # Get data type and corresponding dataset fields, which should be written to file
        data_field_types = DATA_FIELD_TYPES if data_field_types is None else data_field_types        
        self.data_field_types = self._get_existing_fields(data_field_types, dset.fields)
        

    def header_line(self):
        """Mandatory header line"""
        version = 1.00
        now = Time(datetime.now(), scale="utc", fmt="datetime").yyyydddsssss
        start = self.dset.time.min.yyyydddsssss
        end = self.dset.time.max.yyyydddsssss

        obs_code = "P"
        solution = self.station.upper()
        
        self.fid.write(f"%=TMS {version} {self.file_agency:<3s} {now} {self.data_agency:<3s} {start} {end} "
                       f"{obs_code:<1s} {solution}\n")

    def end_line(self):
        """Mandatory end of file line"""
        self.fid.write("%ENDTMS\n")

    def write_block(self, block_name: str, *args):
        """Call the given block so it writes itself"""
        try:
            block_func = getattr(self, block_name)
        except AttributeError:
            log.error(f"Sinex block '{block_name}' is unknown")
            return

        block_func(*args)

    def file_reference(self):
        """Mandatory block"""
        self.fid.write("+FILE/REFERENCE\n")
        self.fid.write(
            "*INFO_TYPE________: INFO___________________________________________________________________________________\n"
        )
        self.fid.write(f" {'DESCRIPTION':<18} {self.organization}\n")
        self.fid.write(f" {'OUTPUT':<18} {'GNSS station coordinate timeseries solution':<60}\n")
        self.fid.write(f" {'CONTACT':<18} {self.contact:<60}\n")
        self.fid.write(f" {'SOFTWARE':<18} {self.software:<60}\n")
        self.fid.write(f" {'INPUT':<18} {self.input:<60}\n")
        self.fid.write(f" {'VERSION NUMBER':<18} {self.version:<60}\n")
        self.fid.write("-FILE/REFERENCE\n")
        

    def timeseries_ref_coordinate(self):
        """
        Write the TIMESERIES/REF_COORDINATE block
        """    
        ref_pos = self._get_ref_pos()
        self.fid.write("+TIMESERIES/REF_COORDINATE\n")
        self.fid.write("*STATION__ PT SOLN T __REF_EPOCH___ __REF_X______ __REF_Y______ __REF_Z______ SYSTEM\n")
        self.fid.write(f" {self.station.upper():<9s}  A ---- P "
                       f"{Time(datetime.fromisoformat(self.dset.meta['reference_epoch']), scale='utc', fmt='datetime').yyyydddsssss} "
                       f"{ref_pos.trs.x:13.4f} "
                       f"{ref_pos.trs.y:13.4f} "
                       f"{ref_pos.trs.z:13.4f} "
                       f"{self.dset.meta['reference_frame']:>6}\n"
	    )
        self.fid.write("-TIMESERIES/REF_COORDINATE\n")


    def timeseries_columns(self):
        """
        Write the TIMESERIES/COLUMNS block
        """
        self.fid.write("+TIMESERIES/COLUMNS\n")
        self.fid.write("*__COL __NAME______________ __UNIT______________ __DESCRIPTION__________________________________________________\n")
        for idx, name in enumerate(self.data_field_types.keys()):
            self.fid.write(f" {idx+1:5d} {name:<20s} {DATA_TYPES[name].unit:<20s} {DATA_TYPES[name].description}\n")
        self.fid.write("-TIMESERIES/COLUMNS\n")


    def timeseries_data(self):
        """
        Write the TIMESERIES/DATA block
        """
        self.fid.write("+TIMESERIES/DATA\n")

        # Write column header
        header = "*"
        for name in self.data_field_types.keys():

            # Get format of column name
            fmt = DATA_TYPES[name].format
            fmt = int(f"{DATA_TYPES[name].format.split('.', 1)[0]}") if "." in fmt else int(DATA_TYPES[name].format.replace("s", "").replace("d", ""))
            fmt = fmt - 2

            # Add column name by adjusting with sign "_"
            header += f" _{{:{str(fmt)}s}}".format(name.ljust(fmt,"_"))
        self.fid.write(f"{header}\n")

        # Write data
        idx_sta = self.dset.filter(station=self.station)
        for idx, time in enumerate(self.dset.time[idx_sta]):
            line = " "
            for name, field in self.data_field_types.items():
                #if DATA_TYPES[name].format: 
                line += f"{{:{DATA_TYPES[name].format}}}".format(attrgetter(field)(self.dset)[idx_sta][idx])
                #else:
                #    line += f"{attrgetter(field)(self.dset)[idx_sta][idx]} "

            self.fid.write(f"{line}\n")
        self.fid.write("-TIMESERIES/DATA\n")


    # 
    # AUXILIARY FUNCTIONS OF CLASS
    #
    @staticmethod
    def _get_existing_fields(data_field_types_def: OrderedDict[str, str], fields: List[str]) -> OrderedDict[str, str]:
        """Get existing dataset fields which corresponds to definition of data types

        Args:
            data_field_types_def: Ordered dictionary with definition of data type and corresponding dataset field
            fields:               Given dataset fields

        Return:
            Ordered dictionary with definition of data type and existing dataset field
        """
        data_field_types = OrderedDict()
        for type_, field in data_field_types_def.items():
            if field.split(".")[0] in fields:  # Check first field entry
                data_field_types[type_] = field
        return data_field_types
    
    
    def _get_ref_pos(self) -> "Position":
        """Get reference coordinate position for the given station
        
        Returns:
            Reference coordinate position as Position object
        """
        idx = self.dset.filter(station=self.station)
        if self.dset.dsite_pos.ref_pos[idx].shape[0] == 1: # only one reference station coordinate entry are given
            ref_pos = Position(self.dset.dsite_pos.ref_pos[idx][0], system="trs")
        else: 
            ref_pos = self.dset.dsite_pos.ref_pos[idx][0]

        return ref_pos



