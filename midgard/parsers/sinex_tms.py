"""A parser for reading SINEX timeseries format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='sinex_tms', file_path='sinex_tms')
    data = p.as_dict()

Description:
------------

Following SINEX timeseries blocks are read:

            FILE/REFERENCE 
            SITE/ID
            SITE/RECEIVER
            SITE/ANTENNA
            SITE/ECCENTRICITY
            TIMESERIES/REF_COORDINATE
            TIMESERIES/COLUMNS
            TIMESERIES/DATA
"""

# Standard library imports
from collections import namedtuple, OrderedDict
from datetime import datetime, timedelta
from typing import List, Tuple

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.data.position import Position
from midgard.data.time import Time
from midgard.dev import plugins
from midgard.parsers._parser_sinex import SinexParser, SinexBlock, SinexField
from midgard.site_info.site_info import SiteInfo

FieldDef = namedtuple(
    "FieldDef", ["field", "unit"]
)
FieldDef.__new__.__defaults__ = (None,) * len(FieldDef._fields)
FieldDef.__doc__ = """A convenience class for defining dataset fields 

    Args:
        field (str):             Dataset field name
        unit (str):              Unit of field
    """

@plugins.register
class SinexTmsParser(SinexParser):
    """A parser for reading SINEX timeseries format
    """

    def __init__(self, file_path, encoding=None):
        """Set up the basic information needed by the parser

        Args:
            file_path (String/Path):    Path to file that will be read.
            encoding (String):          Encoding of file that will be read.
        """
        super().__init__(file_path, encoding)

    def setup_parser(self):
        return [
            self.file_reference, 
            self.site_id,
            self.site_receiver,
            self.site_antenna,
            self.site_eccentricity,
            self.timeseries_ref_coordinate, 
            self.timeseries_columns, 
            self.timeseries_data,
    ]
    

    #
    # Overwrite SINEX class methods
    #     
    def parse_file_reference(self, data):
        """Parser for FILE/REFERENCE data
         
        Args:
            data (numpy.array):  Input data, raw data for FILE/REFERENCE block.
        """
        self.data.setdefault("file_reference", dict())
        for d in data:
            self.data["file_reference"].update({d[0].split()[0].lower(): d[1]})

                       
    # TODO: Should original _parser_sinex.parse_lines be overwritten with following parse_line function?   
    def parse_lines(self, lines: List[bytes], fields: Tuple[SinexField, ...]) -> np.array:
        """Parse lines in a Sinex file
        
        If SinexField "converter" is set to "list", then np.genfromtxt reads automatically line without specifying
        column names or data types.

        Args:
            lines:   Lines to parse.
            fields:  Definition of sinex fields in lines.

        Returns:
            Data contained in lines.
        """
        # Get maximal number of line characters (relevant for defining last delimiter)
        max_char = 0
        for line in lines:
            if len(line) > max_char:
                max_char = len(line)      
        
        # Set up for np.genfromtxt to parse the Sinex block  #TODO: Could it be also handled via a converter function?
        if fields[0].converter == "list": # parse line without field definition as list
            delimiter = None # consecutive whitespace 
            names = None
            usecols = None
            dtype = None
            converters = None
        else:
            delimiter = np.diff(np.array([0] + [f.start_col for f in fields] + [max_char]))  # Length of each field  
            names = [f.name for f in fields if f.dtype]  # Names, only fields with dtype set
            usecols = [i for i, f in enumerate(fields, start=1) if f.dtype]  # Skip 0th and fields without dtype
            dtype = [f.dtype for f in fields if f.dtype]  # Types of fields
            converters = {
                i: getattr(self, "_convert_{}".format(f.converter))  # Converters
                for i, f in enumerate(fields, start=1)
                if f.converter
            }
        
        return np.genfromtxt(
            lines,
            names=names,
            delimiter=delimiter,
            dtype=dtype,
            usecols=usecols,
            converters=converters,
            autostrip=True,
            encoding=self.file_encoding or "bytes",  # TODO: Use None instead
        )


    #
    # CONVERTERS
    #
    def _convert_yyyydddsssss(self, field: bytes) -> datetime:
        """Convert epoch field to ISO format

        The epoch is given in YYYY:DDD:SSSSS format with::

            YY    = 4-digits of the year,
            DDD   = 3-digits day of year,
            SSSSS = 5-digits seconds of day.

        Args:
            field:  Original field with time epoch in YYYY:DDD:SSSSS format.

        Returns:
            Field converted to ISO format.
        """
        field_str = field.decode(self.file_encoding or "utf-8")

        if field_str == "0000:000:00000":
            field_str = "9999:364:99999"  # 0000:000:00000 means the current time. Therefore value set a time in 
                                          # the future.

        date = datetime.strptime(field_str[:8], "%Y:%j")
        time = timedelta(seconds=int(field_str[9:]))

        return (date + time).isoformat()

    #
    # HEADER
    #
    @property
    def header_fields(self) -> Tuple[SinexField, ...]:
        """Fields in header line of Sinex file

        The header line is the first line of the file, and not a proper Sinex
        block. It must start with the 5 characters `%=TMS`.

        Example:
            %=SNX 2.02 IGN 15:314:37740 IGN 00:000:00000 00:000:00000 R   142 2 S
            %=TMS  1.0 NMA 2025:008:36155 NMA 2023:152:43185 2023:156:43185 P 0ABI
            0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8---
        """
        return (
            SinexField("snx_version", 5, "f8"),
            SinexField("create_agency", 10, "U3"),
            SinexField("create_epoch", 14, "O", "yyyydddsssss"),
            SinexField("data_agency", 29, "U3"),
            SinexField("start_epoch", 33, "O", "yyyydddsssss"),
            SinexField("end_epoch", 48, "O", "yyyydddsssss"),
            SinexField("obs_code", 63, "U1"),
            SinexField("solution_contents", 65, "U30"), #TODO: This should be improved to '*'.
        )

    def parse_header_line(self, header_line: bytes) -> None:
        """Parse header of Sinex file

        Header information is stored in `self.meta`.

        Args:
            header_line:  First line of Sinex file.
        """
        if not header_line.startswith(b"%=TMS"):
            log.warn(
                f"The file '{self.file_path}' does not contain a valid SINEX header: {header_line.decode().strip()!r}"
            )
            return

        # Add header information to self.meta
        header_data = self.parse_lines([header_line], self.header_fields)
        self.meta.update({n: header_data[n][()] for n in header_data.dtype.names})


    #
    # SINEX BLOCK
    # 
    @property
    def site_id(self) -> SinexBlock:
        """General information for each site containing estimated parameters.

        Example:
            +SITE/ID
            *STATION__ PT __DOMES__ T _LONGITUDE _LATITUDE_ _HEIGHT_ __STATION DESCRIPTION
             zimm       A 14001M004 P    7.46528   46.87708  956.400 Zimmerwald, Switzerland
            0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8---
            -SITE/ID

        """
        return SinexBlock(
            marker="SITE/ID",
            fields=(
                SinexField("site_code", 1, "U9"),
                SinexField("point_code", 10, "U2"),
                SinexField("domes", 13, "U9"),
                SinexField("obs_code", 23, "U1"),
                SinexField("approx_lon", 25, "f8"),
                SinexField("approx_lat", 36, "f8"),
                SinexField("approx_height", 47, "f8"),
                SinexField("description", 56, "U100", "utf8"), #TODO: Define unlimited character
            ),
            parser=self.parse_site_id,
        ) 
    
    def parse_site_id(self, data):
        """Parse SITE/ID SINEX block"""
        data = data[np.newaxis] if data.ndim == 0 else data
        self.data.setdefault("site_id", list())
        for d in data:
            self.data["site_id"].append(
                {n: d[n] for n in d.dtype.names}
            )
        
    @property
    def site_receiver(self) -> SinexBlock:
        """Information about receivers used for the observations

        Example:        
            +SITE/RECEIVER
                *STATION__ PT SOLN T __DATA_START__ __DATA_END____ DESCRIPTION_________ S/N_________________ FIRMWARE___
                 zimm       A ---- P 1993:121:00000 1997:218:00000 TRIMBLE 4000SSE      3310A                6.12       
                 zimm       A ---- P 1997:218:00000 0000:000:00000 TRIMBLE 4000SSI      3310A                7.25 
                 0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+
            -SITE/RECEIVER
        """
        return SinexBlock(
            marker="SITE/RECEIVER",
            fields=(
                SinexField("site_code", 1, "U9"),
                SinexField("point_code", 11, "U2"),
                SinexField("soln", 14, "U4"),
                SinexField("obs_code", 18, "U1"),             
                SinexField("start_time", 20, "O", "yyyydddsssss"),
                SinexField("end_time", 35, "O", "yyyydddsssss"),
                SinexField("receiver_type", 50, "U20"),
                SinexField("serial_number", 71, "U20"),
                SinexField("firmware", 92, "U11"),
            ),
            parser=self.parse_site_receiver,
        )

    def parse_site_receiver(self, data):
        """Parse SITE/RECEIVER SINEX block"""
        data = data[np.newaxis] if data.ndim == 0 else data
        self.data.setdefault("site_receiver", list())
        for d in data:
            self.data["site_receiver"].append(
                {n: d[n] for n in d.dtype.names}
            )
    
    @property
    def site_antenna(self) -> SinexBlock:
        """Information about antennas at the sites
        
        Example:
            +SITE/ANTENNA
            *STATION__ PT SOLN T __DATA_START__ __DATA_END____ DESCRIPTION_________ S/N_________________
             zimm       A ---- P 1993:121:00000 1998:310:00000 TRM14532.00     NONE 3311A
             zimm       A ---- P 1998:310:00000 0000:000:00000 TRM29659.00     NONE 99390
             0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8---
            -SITE/ANTENNA
        """
        return SinexBlock(
            marker="SITE/ANTENNA",
            fields=(
                SinexField("site_code", 1, "U9"),
                SinexField("point_code", 11, "U2"),
                SinexField("soln", 14, "U4"),
                SinexField("obs_code", 18, "U1"),             
                SinexField("start_time", 20, "O", "yyyydddsssss"),
                SinexField("end_time", 35, "O", "yyyydddsssss"),
                SinexField("antenna_type", 50, "U20"),
                SinexField("serial_number", 71, "U20"),
            ),
            parser=self.parse_site_antenna,
        )
    
    def parse_site_antenna(self, data):
        """Parse SITE/ANTENNA SINEX block"""
        data = data[np.newaxis] if data.ndim == 0 else data
        self.data.setdefault("site_antenna", list())
        for d in data:
            add_dict = {
                n: d[n] for n in d.dtype.names
            }  # Generate dictionary with all SINEX field entries
            add_dict["antenna_type"], add_dict["radome_type"] = d[
                "antenna_type"
            ].split()
            self.data["site_antenna"].append(add_dict)
    
    @property
    def site_eccentricity(self) -> SinexBlock:
        """List of antenna eccentricities

        Antenna eccentricities from the Marker to the Antenna Reference Point
        (ARP) or to the intersection of axis.
        
        
        Example:
            +SITE/ECCENTRICITY
            *                                                     UP______ NORTH___ EAST____
            *STATION__ PT SOLN T __DATA_START__ __DATA_END____ AXE ARP->BENCHMARK(M)_________
             zimm       A ---- P 1993:121:00000 2000:000:00000 UNE   0.0000   0.0000   0.0000
             0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8---
            -SITE/ECCENTRICITY
        """
        return SinexBlock(
            marker="SITE/ECCENTRICITY",
            fields=(
                SinexField("site_code", 1, "U9"),
                SinexField("point_code", 11, "U2"),
                SinexField("soln", 14, "U4"),
                SinexField("obs_code", 18, "U1"),             
                SinexField("start_time", 20, "O", "yyyydddsssss"),
                SinexField("end_time", 35, "O", "yyyydddsssss"),
                SinexField("vector_type", 50, "U3"),
                SinexField("vector_1", 54, "f8"),
                SinexField("vector_2", 63, "f8"),
                SinexField("vector_3", 72, "f8"),
            ),
            parser=self.parse_site_eccentricity,
        )
    
    def parse_site_eccentricity(self, data):
        """Parse SITE/ECCENTRICITY SINEX block"""
        data = data[np.newaxis] if data.ndim == 0 else data
        self.data.setdefault("site_eccentricity", list())
        for d in data:
            self.data["site_eccentricity"].append(
                {n: d[n] for n in d.dtype.names}
            )
                
    @property
    def timeseries_ref_coordinate(self):
        """Custom made block describing the solution.
        
        Is a list of keywords and values

        Example:
            +TIMESERIES/REF_COORDINATE
            *STATION__ PT SOLN T __REF_EPOCH___ __REF_X______ __REF_Y______ __REF_Z______ SYSTEM
             ZIMM       A ---- P 2023:001:00000  4331296.8151   567556.2009  4633134.1423  IGb14
            -TIMESERIES/REF_COORDINATE
            0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8---
                      
        """
        return SinexBlock(
            marker="TIMESERIES/REF_COORDINATE",
            fields=(
                SinexField("site_code", 1, "U9"),
                SinexField("point_code", 11, "U2"),
                SinexField("soln", 14, "U4"),
                SinexField("obs_code", 19, "U1"),
                SinexField("epoch", 21, "O", "yyyydddsssss"),
                SinexField("ref_x", 35, "f8"),
                SinexField("ref_y", 49, "f8"),
                SinexField("ref_z", 64, "f8"),
                SinexField("system", 77, "U9"),               
            ),
            parser=self.parse_timeseries_ref_coordinate,
        )

    def parse_timeseries_ref_coordinate(self, data):
        """Parser for TIMESERIES/REF_COORDINATE data
         
        Args:
            data (numpy.array):  Input data, raw data for TIMESERIES/REF_COORDINATE block.
        """
        self.data.setdefault("ref_coordinate", dict())
        for type_, data in zip(data.dtype.names, data.item()):
            self.data["ref_coordinate"].update({type_: data})
            
            
    @property
    def timeseries_columns(self):
        """Custom made block describing the solution.
        
        Is a list of keywords and values

        Example:
            +TIMESERIES/COLUMNS
            *__COL __NAME______________ __UNIT______________ __DESCRIPTION________________________________________
                 1 YYYY-MM-DD                                Date in format year, month and day (e.g. 2023-06-01)
                 2 YEAR                 y                    Date as decimal year (2023.4137)
                 3 X                    m                    X-coordinate of geocentric site coordinates
                 4 Y                    m                    Y-coordinate of geocentric site coordinates
                 5 Z                    m                    Z-coordinate of geocentric site coordinates
                 6 SIG_X                m                    Standard deviation of geocentric X-coordinate
                 7 SIG_Y                m                    Standard deviation of geocentric Y-coordinate
                 8 SIG_Z                m                    Standard deviation of geocentric Z-coordinate
            -TIMESERIES/COLUMNS
            0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0
                      
        """
        return SinexBlock(
            marker="TIMESERIES/COLUMNS",
            fields=(
                SinexField("col", 1, "f8"),
                SinexField("name", 6, "U20"),
                SinexField("unit", 27, "U21"),
                SinexField("description", 49, "U100", "utf8"), #TODO: Define unlimited character
            ),
            parser=self.parse_timeseries_columns,
        )


    def parse_timeseries_columns(self, data):
        """Parser for TIMESERIES/COLUMNS data
         
        Args:
            data (numpy.array):  Input data, raw data for TIMESERIES/COLUMNS block.
        """
        self.data["timeseries_columns"] = data
        
        
    @property
    def timeseries_data(self):
        """Custom made block describing the solution.
        
        Is a list of keywords and values

        Example:
            +TIMESERIES/DATA
            * _YYYY-MM-DD _YEAR______ _X___________ _Y___________ _Z___________ _SIG_X___ _SIG_Y___ _SIG_Z___ _EAST______ _NORTH_____ _UP________ _SIG_EAST _SIG_NORTH _SIG_UP__
             2023-05-22    2023.38767  4331296.8156   567556.2118  4633134.1526    0.0008    0.0003    0.0010      0.0108      0.0056      0.0088    0.0003    0.0009    0.0009
             2023-05-23    2023.39041  4331296.8147   567556.2087  4633134.1452    0.0008    0.0003    0.0010      0.0078      0.0015      0.0026    0.0003    0.0009    0.0009
             2023-05-24    2023.39315  4331296.8121   567556.2097  4633134.1462    0.0010    0.0004    0.0012      0.0091      0.0040      0.0017    0.0004    0.0011    0.0011
           -TIMESERIES/DATA
            0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0
                      
        """
        return SinexBlock(
            marker="TIMESERIES/DATA",
            fields=(
                SinexField("data", 1, "O", "list"),
            ),
            parser=self.parse_timeseries_data,
        )


    def parse_timeseries_data(self, data):
        """Parser for TIMESERIES/DATA data
         
        Args:
            data (numpy.array):  Input data, raw data for TIMESERIES/DATA block.
        """
        self.data.setdefault("timeseries_data", dict())
        
        # Define column data type, which are not float
        dtype_str = ["YYYY-MM-DD", "YYYY-DDD"]  
        
        # Conversion from np.void to np.ndarray array
        data = np.array(data.tolist()) 

        # Add dimension to one-dimension arrays
        if data.ndim == 1:
            data = np.array([data])
        
        for name, col in zip(self.data["timeseries_columns"]["name"], data.T):           
            dtype = str if name in dtype_str else float
            self.data["timeseries_data"][name.lower()] = col.astype(dtype)
                
    
    #
    # GENERATE DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Store SINEX timeseries data block entries in a dataset

        Returns:
            Midgard Dataset whereby following SINEX timeseries data block entries could be stored (depending on input 
            data):


       | Field                    | Type              | Description                                                   |
       | :----------------------- | :---------------- | :------------------------------------------------------------ |
       | site_pos                 | Position          | x, y and z station coordinates                                |
       | dsite_pos                | PositionDelta     | Position delta object referred to a reference position        |
       | site_pos_east_sigma      | numpy.ndarray     | Standard deviation of topocentric East-coordinate             |
       | site_pos_north_sigma     | numpy.ndarray     | Standard deviation of topocentric North-coordinate            |
       | site_pos_up_sigma        | numpy.ndarray     | Standard deviation of topocentric Up-coordinate               |
       | site_pos_en_correlation  | numpy.ndarray     | Correlation between East and North component of topocentric   |
       |                          |                   | coordinates                                                   |
       | site_pos_eu_correlation  | numpy.ndarray     | Correlation between East and Up component of topocentric      |
       |                          |                   | coordinates                                                   |
       | site_pos_nu_correlation  | numpy.ndarray     | Correlation between North and Up component of topocentric     |
       |                          |                   | coordinates                                                   | 
       | site_pos_xy_correlation  | numpy.ndarray     | Correlation between X- and Y-coordinate                       |
       | site_pos_xz_correlation  | numpy.ndarray     | Correlation between X- and Z-coordinate                       |
       | site_pos_yz_correlation  | numpy.ndarray     | Correlation between Y- and Z-coordinate                       |
       | site_pos_x_sigma         | numpy.ndarray     | Standard deviation of geocentric X-coordinate                 |
       | site_pos_y_sigma         | numpy.ndarray     | Standard deviation of geocentric Y-coordinate                 |
       | site_pos_z_sigma         | numpy.ndarray     | Standard deviation of geocentric Z-coordinate                 |
       | station                  | numpy.ndarray     | Station name                                                  |
       | time                     | Time              | Parameter time given as TimeTable object                      |
       
       TODO: Description of meta data        
        """
        dset = dataset.Dataset(num_obs=len(self.data["timeseries_data"]["yyyy-mm-dd"]))
        dset.meta.update(self.meta)
        dset.meta["station"] = self.meta["solution_contents"].lower() if "solution_contents" in self.meta.keys() else "none"
        
        # Add site_info dictionary to meta variable
        for block in ["site_id", "site_receiver", "site_antenna", "site_eccentricity"]:
            if block in self.data.keys():
                dset.meta.setdefault("site_info", dict()).update({block: self.data[block]})
        
        # Add time field to dataset
        time_format_def = OrderedDict({
                "yyyy-mm-dd": "datetime",
                "yyyy-ddd": "datetime",
                "jd": "jd",
                "mjd": "mjd",
                "year": "decimalyear",
                #TODO: gpsweek
                #TODO: hh:mm:ss
        })
        
        time_type = None
        for type_, fmt in time_format_def.items():
            if type_ in self.data["timeseries_data"].keys():
                time_type = type_
                break
  
        if time_type:       
            if time_type == "yyyy-mm-dd":
                time = [datetime.strptime(d, "%Y-%m-%d") for d in self.data["timeseries_data"][time_type]]
            elif type_ == "yyyy-ddd":
                time = [datetime.strptime(d, "%Y-%j") for d in self.data["timeseries_data"][time_type]]
            else:
                time = self.data["timeseries_data"][time_type]
        
            dset.add_time("time", val=time, scale="utc", fmt=time_format_def[time_type])
                     
        # Add position field to dataset
        if "x" in self.data["timeseries_data"].keys():
            dset.add_position(
                "site_pos",
                val=np.vstack((
                            self.data["timeseries_data"]["x"], 
                            self.data["timeseries_data"]["y"], 
                            self.data["timeseries_data"]["z"]),
                ).T,
                #val=np.squeeze(
                #        np.vstack((
                #            self.data["timeseries_data"]["x"], 
                #            self.data["timeseries_data"]["y"], 
                #            self.data["timeseries_data"]["z"]),
                #        ).T
                #),
                system="trs",
            )
            
        # Add position_delta field to dataset
        if "east" in self.data["timeseries_data"].keys():

            ref_pos = Position(
                val = np.repeat(
                        np.array([ 
                            self.data["ref_coordinate"]["ref_x"],
                            self.data["ref_coordinate"]["ref_y"],
                            self.data["ref_coordinate"]["ref_z"],
                        ])[None, :],
                        dset.num_obs,
                        axis=0
                ),
                system="trs",
            )
            
            dset.add_position_delta(
                "dsite_pos",
                val= np.vstack((
                            self.data["timeseries_data"]["east"], 
                            self.data["timeseries_data"]["north"], 
                            self.data["timeseries_data"]["up"]),
                ).T,
                #val=np.squeeze(
                #        np.vstack((
                #            self.data["timeseries_data"]["east"], 
                #            self.data["timeseries_data"]["north"], 
                #            self.data["timeseries_data"]["up"]),
                #        ).T
                #),
                system="enu",
                ref_pos=ref_pos,
            )
            
        # Add float field to dataset
        field_def = {
            "sig_x": FieldDef("site_pos_x_sigma", "meter"),
            "sig_y": FieldDef("site_pos_y_sigma", "meter"),
            "sig_z": FieldDef("site_pos_z_sigma", "meter"),
            "corr_xy": FieldDef("site_pos_xy_correlation", ""),
            "corr_xz": FieldDef("site_pos_xz_correlation", ""),
            "corr_yz": FieldDef("site_pos_yz_correlation", ""),
            "sig_east": FieldDef("site_pos_east_sigma", "meter"),
            "sig_north": FieldDef("site_pos_north_sigma", "meter"),
            "sig_up": FieldDef("site_pos_up_sigma", "meter"),
            "corr_en": FieldDef("site_pos_en_correlation", ""),
            "corr_eu": FieldDef("site_pos_eu_correlation", ""),
            "corr_nu": FieldDef("site_pos_nu_correlation", ""),
        }
        
        for type_, def_ in field_def.items():
            if type_ in self.data["timeseries_data"].keys():
                dset.add_float(def_.field, val=self.data["timeseries_data"][type_], unit=def_.unit)

        # Add text field to dataset
        dset.add_text("station", val=np.repeat(dset.meta["station"].lower(), dset.num_obs, axis=0))
                
        # Add events to dataset
        if "site_antenna" in self.data.keys() or "site_receiver" in self.data.keys():
            self._add_events(dset)

        return dset
    
    #
    # AUXILIARY FUNCTIONS
    # 
    def _add_events(self, dset: "Dataset") -> None:
        """Add events to Dataset
    
        Read site information for getting information about antenna, receiver and firmware changes. These equipment changes
        are added as events to the Dataset.
    
        Args:
            dset:       A dataset containing the data.
    
        """
        date_from = min(dset.time.datetime)
        date_to = max(dset.time.datetime)

        # Get station dictionary of SiteInfo instance 
        info = SiteInfo.get_history(
                    source="snx", 
                    source_data={dset.meta["station"].lower(): dset.meta["site_info"]},
                    stations=dset.meta["station"],
                    source_path=dset.meta["__data_path__"],
        )
        
        # Add antenna, receiver and firmware events
        anth = info[dset.meta["station"].lower()]["antenna"].history
        for period, ant in anth.items():
            date = ant.date_from
            if date >= date_from and date <= date_to:
                dset.meta.add_event(Time(val=date, fmt="datetime", scale="utc"), "antenna", dset.meta["station"])
                
        rcvh = info[dset.meta["station"].lower()]["receiver"].history
        for period, rcv in rcvh.items():
            date = rcv.date_from
            if date >= date_from and date <= date_to:
                dset.meta.add_event(Time(val=date, fmt="datetime", scale="utc"), "receiver", dset.meta["station"])

    
                
