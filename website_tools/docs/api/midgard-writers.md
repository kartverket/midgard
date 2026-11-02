# midgard.writers
Framework for writing output in different formats

**Description:**

Each output format / output destination should be defined in a separate .py-file. The function inside the .py-file that
should be called need to be decorated with the :func:`~midgard.dev.plugins.register` decorator as follows::

    from midgard.dev import plugins

    @plugins.register
    def write_as_fancy_format(arg_1, arg_2):
        ...



### **names**()

Full name: `midgard.writers.names`

Signature: `() -> List[str]`

List the names of the available writers

**Returns:**

List of strings with the names of the available writers.


### **write**()

Full name: `midgard.writers.write`

Signature: `(writer: str, **writer_args: Any) -> None`

Call one writer

**Args:**

- `writer`:       Name of writer.
- `writer_args`:  Arguments passed on to writer.


## midgard.writers._writers
Basic functionality for writing files

Description:

This module contains functions for writing files.


### **get_existing_fields**()

Full name: `midgard.writers._writers.get_existing_fields`

Signature: `(dset: 'Dataset', writers_in: Tuple[ForwardRef('WriterField'), ...]) -> Tuple[ForwardRef('WriterField'), ...]`

Get existing writer fields, which are given in Dataset.

**Args:**

- `dset`:         Dataset, a dataset containing the data.
- `writers_in`:   Writer fields.

**Returns:**

Existing writer fields


### **get_existing_fields_by_attrs**()

Full name: `midgard.writers._writers.get_existing_fields_by_attrs`

Signature: `(dset: 'Dataset', writers_in: Tuple[ForwardRef('WriterField'), ...]) -> Tuple[ForwardRef('WriterField'), ...]`

Get existing writer fields, which are given in Dataset.

**Args:**

- `dset`:         Dataset, a dataset containing the data.
- `writers_in`:   Fields to write/plot.

**Returns:**

Existing writer fields


### **get_field**()

Full name: `midgard.writers._writers.get_field`

Signature: `(dset: 'Dataset', field: str, attrs: Tuple[str], unit: str | None = None) -> numpy.ndarray`

Get field values of a Dataset specified by the field attributes

If necessary the unit of the data fields are corrected to the defined 'output' unit.

**Args:**

- `dset`:     Dataset, a dataset containing the data.
- `field`:    Field name.
- `attrs`:    Field attributes (e.g. for Time object: (<scale>, <time format>)).
- `unit`:     Unit used for output.

**Returns:**

Array with Dataset field values


### **get_field_by_attrs**()

Full name: `midgard.writers._writers.get_field_by_attrs`

Signature: `(dset: 'Dataset', attrs: Tuple[str], unit: str) -> numpy.ndarray`

Get field values of a Dataset specified by the field attributes

If necessary the unit of the data fields are corrected to the defined 'output' unit.

**Args:**

- `dset`:     Dataset, a dataset containing the data.
- `attrs`:    Field attributes (e.g. for Time object: (<scale>, <time format>)).
- `unit`:     Unit used for output.

**Returns:**

Array with Dataset field values


### **get_header**()

Full name: `midgard.writers._writers.get_header`

Signature: `(fields: List[str], pgm_version: None | str = None, run_by: str = '', summary: None | str = None, add_description: None | str = None, lsign: str = '') -> str`

Get header

**Args:**

- `fields`:             List with fields to write.
- `pgm_version`:        Name and version (e.g. where 1.0.0) of program, which has created the output.
- `run_by`:             Information about who has created this file (e.g. NMA).
- `summary`:            Short description of output file
- `add_description`:    Additional description lines
- `lsign`:              Leading comment sign

**Returns:**

Header lines


### **get_value_by_keys**()

Full name: `midgard.writers._writers.get_value_by_keys`

Signature: `(dict_: Dict[str, Any], keys: Tuple[str], format_=None, unit=None) -> Any | List[Any]`

Get value of a dictionary specified by keys

If option `format_` is defined, then formatted string is returned instead of original value.

**Args:**

- `dict_`:   Dictionary with data
- `keys`:    Dictionary keys
- `format_`: Format definition
- `unit`:    Unit definition in format <from_unit>2<to_unit> (e.g. meter2millimeter)

**Returns:**

Original dictionary value or string formatted value


## midgard.writers.bernese_abb
Write Bernese abbreviation file in *.ABB format

**Description:**



### ascii_lowercase (str)
`ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'`


### **bernese_abb**()

Full name: `midgard.writers.bernese_abb.bernese_abb`

Signature: `(file_path: pathlib.PosixPath, site_info: Dict[str, Any], agency: str = 'UNKNOWN') -> None`

Write Bernese abbreviation file in *.ABB format

**Args:**

- `file_path`:             File path of Bernese *.ABB output file
- `site_info`:             Dictionary with station information, whereby station name is the key and a dictionary
                           with site information the value.
- `agency`:                Abbreviation of agency producing the file (e.g. IGS)


## midgard.writers.bernese_clu
Write a-priori Bernese station cluster file in *.CLU format

**Description:**



### **bernese_clu**()

Full name: `midgard.writers.bernese_clu.bernese_clu`

Signature: `(file_path: pathlib.PosixPath, site_info: Dict[str, Any], agency: str = 'UNKNOWN') -> None`

Write a-priori Bernese station cluster file in *.CLU format

**Args:**

- `file_path`:             File path of Bernese *.CLU output file
- `site_info`:             Dictionary with station information, whereby station name is the key and a dictionary
                           with site information the value.
- `agency`:                Abbreviation of agency producing the file (e.g. IGS)


## midgard.writers.bernese_crd
Write a-priori Bernese station coordinate file in *.CRD format

**Description:**



### **bernese_crd**()

Full name: `midgard.writers.bernese_crd.bernese_crd`

Signature: `(file_path: pathlib.PosixPath, site_info: Dict[str, Any], datum: str = 'UNKNOWN', epoch: datetime.datetime | None = None, agency: str = 'UNKNOWN', write_nan_site_coord: bool = False) -> None`

Write a-priori Bernese station coordinate file in *.CRD format

**Args:**

- `file_path`:             File path of Bernese *.CRD output file
- `site_info`:             Dictionary with station information, whereby station name is the key and a dictionary
                           with site information the value.
- `datum`:                 Reference system name of site coordinates (e.g. IGb14)
- `epoch`:                 Reference epoch of site coordinates in format yyyy-mm-dd HH:MM:SS (e.g. 
                           2015-01-01 00:00:00)
- `agency`:                Abbreviation of agency producing the file (e.g. IGS)
- `write_nan_site_coord`:  Write site coordinates, which has Not a Number (NaN) as value.


## midgard.writers.bernese_sta
Write Bernese station information file in *.STA format

**Description:**



### **bernese_sta**()

Full name: `midgard.writers.bernese_sta.bernese_sta`

Signature: `(file_path: pathlib.PosixPath, site_info: Dict[str, Any], rename_station: Dict[str, str] = {}, event_path: pathlib.PosixPath | None = None, agency: str = 'UNKNOWN', skip_firmware: bool = False, use_first_common_date: bool = True) -> None`

Write Bernese station information file in *.STA format

**Args:**

- `file_path`:       File path of Bernese *.STA output file
- `site_info`:       Dictionary with station information, whereby station name is the key and a dictionary with 
                     site information the value.
- `rename_station`:  Dictionary with official 4-digit station name as key and the alternative name as value. This 
                     information is used in the "RENAMING OF STATIONS" section in Bernese *.STA file. This can be
                     necessary if the used 4-digit station names are not unique.
- `event_path`:      File path of event file with additional event 
- `agency`:          Agency which uses this Bernese station information file for processing
- `skip_firmware`:   Skip firmware changes by generating "TYPE 002: STATION INFORMATION" block
- `use_first_common_date`: Use first common date entry given by receiver, antenna and eccentricity properties. It  
                     can happen, that the first date entry is inconsistent for these properties. In this case the
                     first common date entry of one of these properties is used in the BERNESE STA file. The 
                     alternative is to skip date entries, which does not fit into the given date period. 


## midgard.writers.bernese_sta_v52
Write Bernese station information file in *.STA v5.2 format

**Description:**



### **bernese_sta_v52**()

Full name: `midgard.writers.bernese_sta_v52.bernese_sta_v52`

Signature: `(file_path: pathlib.PosixPath, site_info: Dict[str, Any], rename_station: Dict[str, str] = {}, event_path: pathlib.PosixPath | None = None, agency: str = 'UNKNOWN', skip_firmware: bool = False) -> None`

Write Bernese station information file in *.STA v5.2 format

**Args:**

- `file_path`:       File path of Bernese *.STA output file
- `site_info`:       Dictionary with station information, whereby station name is the key and a dictionary with 
                     site information the value.
- `rename_station`:  Dictionary with official 4-digit station name as key and the alternative name as value. This 
                     information is used in the "RENAMING OF STATIONS" section in Bernese *.STA file. This can be
                     necessary if the used 4-digit station names are not unique.
- `event_path`:      File path of event file with additional event 
- `agency`:          Agency which uses this Bernese station information file for processing
- `skip_firmware`:   Skip firmware changes by generating "TYPE 002: STATION INFORMATION" block


## midgard.writers.bernese_vel
Write a-priori Bernese station velocity file in *.VEL format

**Description:**



### **bernese_vel**()

Full name: `midgard.writers.bernese_vel.bernese_vel`

Signature: `(file_path: pathlib.PosixPath, site_info: Dict[str, Any], datum: str = 'UNKNOWN', agency: str = 'UNKNOWN', write_nan_site_vel: bool = False) -> None`

Write a-priori Bernese station velocity file in *.VEL format

**Args:**

- `file_path`:             File path of Bernese *.VEL output file
- `site_info`:             Dictionary with station information, whereby station name is the key and a dictionary
                           with site information the value.
- `datum`:                 Reference system name of site coordinates (e.g. IGb14)
- `agency`:                Abbreviation of agency producing the file (e.g. IGS)
- `write_nan_site_vel`:    Write site velocities, which has Not a Number (NaN) as value.


## midgard.writers.csv_
Write dataset fields in CSV file format


### **csv_**()

Full name: `midgard.writers.csv_.csv_`

Signature: `(dset: 'Dataset', file_path: str | pathlib.PosixPath, fields: OrderedDict[str, str]) -> None`

Write dataset fields in CSV file format


Field names of dataset, which should be written in CSV file, are defined via the 'fields' argument. The keys of the
'fields' dictionary represents the field names and optional the format of the field can be defined via dictionary  
values (e.g. '%.2f'). If the format is not defined (dictionary values is ''), than the specifier 's' is used as 
default. For more information about possible format specifiers, check option 'fmt' of numpy savetxt function, which  
is used to write the CSV files. 

Example for 'fields' dictionary:

    fields = {
         'date': '%s',
         'time.gps.mjd': '%.6f',
         'time.gps.gps_ws.week': '%d',
         'time.gps.gps_ws.seconds': '%.3f',
         'satellite': '%s',
         'frequency': '%s',
         'amplitude': '%.2f',
         'peak2noise': '%.2f',
         'reflection_height': '%.2f',
         'reflection_height_referenced': '%.2f',
         'water_level': '%.2f',
         'water_level_referenced': '%.2f',
    }

**Args:**

- `dset`:       A dataset containing the data.
- `file_path`:  File path of CSV file.
- `fields`:     Dictionary with field name as key and format specifiers as values


## midgard.writers.gamit_apr_eq
Write apr and eq file for GAMIT

**Description:**




### **gamit_apr_eq**()

Full name: `midgard.writers.gamit_apr_eq.gamit_apr_eq`

Signature: `(apr_path: pathlib.PosixPath, eq_path: pathlib.PosixPath, site_info: Dict[str, Any], ref_frame: str) -> None`

Write apr and eq file for GAMIT

**Args:**

- `apr_path`:    File path of GAMIT *.apr file
- `eq_path`:     File path of GAMIT *.eq file      
- `site_info`:   Dictionary with station information, whereby station name is the key and a dictionary with 
                 site information the value.           
- `ref_frame`:   Reference frame name of site coordinates (e.g. IGb14)


## midgard.writers.gamit_station_info
Write site information file for GAMIT

**Description:**




### REFERENCE_POINT (dict)
`REFERENCE_POINT = {'BAM': 'DHARP', 'BCR': 'DHBCR', 'BDG': '', 'BGP': 'DHBGP', 'BPA': 'DHBPA', 'TCR': 'DHTCR', 'TDG': '', 'TGP': 'DHTGP', 'TOP': 'DHARP', 'TPA': ''}`


### **gamit_station_info**()

Full name: `midgard.writers.gamit_station_info.gamit_station_info`

Signature: `(file_path: pathlib.PosixPath, site_info: Dict[str, Any]) -> None`

Write site information file for GAMIT

**Args:**

- `file_path`:       File path of site information GAMIT output file
- `site_info`:       Dictionary with station information, whereby station name is the key and a dictionary with 
                     site information the value.


## midgard.writers.gipsyx_site_info
Write site information file for GipsyX

**Description:**




### **gipsyx_site_info**()

Full name: `midgard.writers.gipsyx_site_info.gipsyx_site_info`

Signature: `(file_path: pathlib.PosixPath, site_info: Dict[str, Any]) -> None`

Write site information file for GipsyX

**Args:**

- `file_path`:       File path of site information GipsyX output file
- `site_info`:       Dictionary with station information, whereby station name is the key and a dictionary with 
                     site information the value.


## midgard.writers.report
Class for reports

**Description:**
TODO



### **Report**

Full name: `midgard.writers.report.Report`

Signature: `(fid: '_io.TextIOWrapper', rundate: datetime.date, path: 'pathlib.PosixPath', description: str = '') -> None`

Class for reports


## midgard.writers.sinex_tms
Write timeseries file in SINEX TMS format


### DATA_FIELD_TYPES (OrderedDict)
`DATA_FIELD_TYPES = OrderedDict({'YYYY-MM-DD': 'time.utc.date', 'YEAR': 'time.utc.decimalyear', 'X': 'obs.site_pos.trs.x', 'Y': 'obs.site_pos.trs.y', 'Z': 'obs.site_pos.trs.z', 'SIG_X': 'obs.site_pos_x_sigma', 'SIG_Y': 'obs.site_pos_y_sigma', 'SIG_Z': 'obs.site_pos_z_sigma', 'CORR_XY': 'obs.site_pos_xy_correlation', 'CORR_XZ': 'obs.site_pos_xz_correlation', 'CORR_YZ': 'obs.site_pos_yz_correlation', 'EAST': 'obs.dsite_pos.enu.east', 'NORTH': 'obs.dsite_pos.enu.north', 'UP': 'obs.dsite_pos.enu.up', 'SIG_E': 'obs.dsite_pos_east_sigma', 'SIG_N': 'obs.dsite_pos_north_sigma', 'SIG_U': 'obs.dsite_pos_up_sigma', 'CORR_EN': 'obs.dsite_pos_en_correlation', 'CORR_EU': 'obs.dsite_pos_eu_correlation', 'CORR_NU': 'obs.dsite_pos_nu_correlation', 'NOBSC': 'obs.code_obs_num', 'NOBSP': 'obs.phase_obs_num', 'NOUTC': 'obs.code_outlier_num', 'NOUTP': 'obs.phase_outlier_num', 'PRES_C': 'obs.code_residual_rms', 'PRES_P': 'obs.phase_residual_rms', 'RCV_CLK': 'obs.receiver_clock', 'SIG_RCV_CLK': 'obs.receiver_clock_sigma', 'TGE': 'obs.trop_gradient_east', 'SIG_TGE': 'obs.trop_gradient_east_sigma', 'TGN': 'obs.trop_gradient_north', 'SIG_TGN': 'obs.trop_gradient_north_sigma', 'TGTOT': 'obs.trop_gradient_total', 'SIG_TGTOT': 'obs.trop_gradient_total_sigma', 'TRODRY': 'obs.trop_zenith_dry', 'SIG_TRODRY': 'obs.trop_zenith_dry_sigma', 'TROWET': 'obs.trop_zenith_wet', 'SIG_TROWET': 'obs.trop_zenith_wet_sigma', 'TROTOT': 'obs.trop_zenith_total', 'SIG_TROTOT': 'obs.trop_zenith_total_sigma'})`


### DATA_TYPES (dict)
`DATA_TYPES = {'GPSWEEK': DataType(unit='', format='7s', description='Date as GPS week together with GPS day in format wwwwd (e.g. 22644)'), 'JD': DataType(unit='', format='11.1f', description='Date as Julian Day (e.g. 2460096.5)'), 'MJD': DataType(unit='', format='9.1f', description='Date as Modified Julian Day (e.g. 60096.0)'), 'YEAR': DataType(unit='y', format='12.5f', description='Date as decimal year (2023.4137)'), 'YYYY-DDD': DataType(unit='', format='10s', description='Date in format year and day of year (e.g. 2023-152)'), 'YYYY-MM-DD': DataType(unit='', format='12s', description='Date in format year, month and day (e.g. 2023-06-01)'), 'HH:MM:SS': DataType(unit='', format='10s', description='Time in format hour, minute and second (e.g. 01:34:15)'), 'EAST': DataType(unit='m', format='12.4f', description='East component of topocentric site coordinates'), 'NORTH': DataType(unit='m', format='12.4f', description='North component of topocentric site coordinates'), 'UP': DataType(unit='m', format='12.4f', description='Up component of topocentric site coordinates'), 'SIG_E': DataType(unit='m', format='10.4f', description='Standard deviation of topocentric East component'), 'SIG_N': DataType(unit='m', format='10.4f', description='Standard deviation of topocentric North component'), 'SIG_U': DataType(unit='m', format='10.4f', description='Standard deviation of topocentric Up component'), 'CORR_EN': DataType(unit='', format='10.4f', description='Correlation between East and North component'), 'CORR_EU': DataType(unit='', format='10.4f', description='Correlation between East and Up component'), 'CORR_NU': DataType(unit='', format='10.4f', description='Correlation between North and Up component'), 'X': DataType(unit='m', format='14.4f', description='X-coordinate of geocentric site coordinates'), 'Y': DataType(unit='m', format='14.4f', description='Y-coordinate of geocentric site coordinates'), 'Z': DataType(unit='m', format='14.4f', description='Z-coordinate of geocentric site coordinates'), 'SIG_X': DataType(unit='m', format='10.4f', description='Standard deviation of geocentric X-coordinate'), 'SIG_Y': DataType(unit='m', format='10.4f', description='Standard deviation of geocentric Y-coordinate'), 'SIG_Z': DataType(unit='m', format='10.4f', description='Standard deviation of geocentric Z-coordinate'), 'CORR_XY': DataType(unit='', format='10.4f', description='Correlation between X- and Y-coordinate '), 'CORR_XZ': DataType(unit='', format='10.4f', description='Correlation between X- and Z-coordinate'), 'CORR_YZ': DataType(unit='', format='10.4f', description='Correlation between Y- and Z-coordinate'), 'NOBS': DataType(unit='', format='8d', description='Number of observations used by generation of daily site coordinate solution'), 'RES_E': DataType(unit='m', format='12.4f', description='Residual of topocentric East component, which represent the difference between the East observation and the calculated model (e.g. linear trend) '), 'RES_N': DataType(unit='m', format='12.4f', description='Residual of topocentric North component, which represent the difference between the North observation and the calculated model (e.g. linear trend) '), 'RES_U': DataType(unit='m', format='12.4f', description='Residual of topocentric Up component, which represent the difference between the Up observation and the calculated model (e.g. linear trend) '), 'MOD_E': DataType(unit='m', format='12.4f', description='Calculated model for topocentric East component time-series data'), 'MOD_N': DataType(unit='m', format='12.4f', description='Calculated model for topocentric North component time-series data'), 'MOD_U': DataType(unit='m', format='12.4f', description='Calculated model for topocentric Up component time-series data'), 'NOBSC': DataType(unit='', format='7.0f', description='Number of GNSS carrier-phase observations used by generation of site coordinate solution for given sampling rate period'), 'NOBSP': DataType(unit='', format='7.0f', description='Number of GNSS pseudo_range observations used by generation of site coordinate solution for given sampling rate period'), 'NOUTC': DataType(unit='', format='7.0f', description='Number of GNSS carrier-phase outliers by generation of site coordinate solution for given sampling rate period'), 'NOUTP': DataType(unit='', format='7.0f', description='Number of GNSS pseudo_range outliers by generation of site coordinate solution for given sampling rate period'), 'PRES_C': DataType(unit='m', format='14.4f', description='Post-fit GNSS carrier-phase residuals by generation of site coordinate solution for given sampling rate period'), 'PRES_P': DataType(unit='m', format='14.4f', description='Post-fit GNSS pseudo_range residuals by generation of site coordinate solution for given sampling rate period'), 'RCV_CLK': DataType(unit='m', format='18.4f', description='Daily average of receiver clock estimate'), 'TGE': DataType(unit='m', format='14.4f', description='Daily average of tropospheric gradient - East component'), 'TGN': DataType(unit='m', format='14.4f', description='Daily average of tropospheric gradient - North component'), 'TGTOT': DataType(unit='m', format='14.4f', description='Daily average of tropospheric total gradient (East + North parts)'), 'TRODRY': DataType(unit='m', format='14.4f', description='Daily average of tropospheric zenith dry/hydrostation delay (ZHD)'), 'TROTOT': DataType(unit='m', format='14.4f', description='Daily average of tropospheric zenith total delay (ZTD)'), 'TROWET': DataType(unit='m', format='14.4f', description='Daily average of tropospheric zenith wet delay (ZWD)'), 'SIG_RCV_CLK': DataType(unit='m', format='18.4f', description='Daily average of standard deviation of receiver clock estimate'), 'SIG_TGE': DataType(unit='m', format='11.4f', description='Daily average of standard deviation of tropospheric gradient - East component'), 'SIG_TGN': DataType(unit='m', format='11.4f', description='Daily average of standard deviation of tropospheric gradient - North component'), 'SIG_TGTOT': DataType(unit='m', format='11.4f', description='Daily average of standard deviation of tropospheric total gradient (East + North parts)'), 'SIG_TRODRY': DataType(unit='m', format='11.4f', description='Daily average of standard deviation of tropospheric zenith dry/hydrostation delay (ZHD)'), 'SIG_TROTOT': DataType(unit='m', format='11.4f', description='Daily average of standard deviation of tropospheric zenith total delay (ZTD)'), 'SIG_TROWET': DataType(unit='m', format='11.4f', description='Daily average of standard deviation of tropospheric zenith wet delay (ZWD)')}`


### **DataType**

Full name: `midgard.writers.sinex_tms.DataType`

Signature: `(unit=None, format=None, description=None)`

A convenience class for defining a data type 

**Args:**

unit (str):            Unit of data type
format (str):          Data type format definition
description  (str):    Description to given data type acronym


### ESTIMATE_PARAMETER_FIELD_TYPES (OrderedDict)
`ESTIMATE_PARAMETER_FIELD_TYPES = OrderedDict({'VEL_X': ParaType(keys=('vel', 'trend', 'x'), unit='m/y'), 'VEL_Y': ParaType(keys=('vel', 'trend', 'y'), unit='m/y'), 'VEL_Z': ParaType(keys=('vel', 'trend', 'z'), unit='m/y'), 'VEL_E': ParaType(keys=('vel', 'trend', 'e'), unit='m/y'), 'VEL_N': ParaType(keys=('vel', 'trend', 'n'), unit='m/y'), 'VEL_U': ParaType(keys=('vel', 'trend', 'u'), unit='m/y'), 'BIAS_X': ParaType(keys=('vel', 'bias', 'x'), unit='m'), 'BIAS_Y': ParaType(keys=('vel', 'bias', 'y'), unit='m'), 'BIAS_Z': ParaType(keys=('vel', 'bias', 'z'), unit='m'), 'BIAS_E': ParaType(keys=('vel', 'bias', 'e'), unit='m'), 'BIAS_N': ParaType(keys=('vel', 'bias', 'n'), unit='m'), 'BIAS_U': ParaType(keys=('vel', 'bias', 'u'), unit='m'), 'AMPA_X': ParaType(keys=('vel', 'amp_annual', 'x'), unit='m'), 'AMPA_Y': ParaType(keys=('vel', 'amp_annual', 'y'), unit='m'), 'AMPA_Z': ParaType(keys=('vel', 'amp_annual', 'z'), unit='m'), 'AMPA_E': ParaType(keys=('vel', 'amp_annual', 'e'), unit='m'), 'AMPA_N': ParaType(keys=('vel', 'amp_annual', 'n'), unit='m'), 'AMPA_U': ParaType(keys=('vel', 'amp_annual', 'u'), unit='m'), 'AMPS_X': ParaType(keys=('vel', 'amp_semiannual', 'x'), unit='m'), 'AMPS_Y': ParaType(keys=('vel', 'amp_semiannual', 'y'), unit='m'), 'AMPS_Z': ParaType(keys=('vel', 'amp_semiannual', 'z'), unit='m'), 'AMPS_E': ParaType(keys=('vel', 'amp_semiannual', 'e'), unit='m'), 'AMPS_N': ParaType(keys=('vel', 'amp_semiannual', 'n'), unit='m'), 'AMPS_U': ParaType(keys=('vel', 'amp_semiannual', 'u'), unit='m'), 'PHSA_X': ParaType(keys=('vel', 'phase_annual', 'x'), unit='deg'), 'PHSA_Y': ParaType(keys=('vel', 'phase_annual', 'y'), unit='deg'), 'PHSA_Z': ParaType(keys=('vel', 'phase_annual', 'z'), unit='deg'), 'PHSA_E': ParaType(keys=('vel', 'phase_annual', 'e'), unit='deg'), 'PHSA_N': ParaType(keys=('vel', 'phase_annual', 'n'), unit='deg'), 'PHSA_U': ParaType(keys=('vel', 'phase_annual', 'u'), unit='deg'), 'PHSS_X': ParaType(keys=('vel', 'phase_semiannual', 'x'), unit='deg'), 'PHSS_Y': ParaType(keys=('vel', 'phase_semiannual', 'y'), unit='deg'), 'PHSS_Z': ParaType(keys=('vel', 'phase_semiannual', 'z'), unit='deg'), 'PHSS_E': ParaType(keys=('vel', 'phase_semiannual', 'e'), unit='deg'), 'PHSS_N': ParaType(keys=('vel', 'phase_semiannual', 'n'), unit='deg'), 'PHSS_U': ParaType(keys=('vel', 'phase_semiannual', 'u'), unit='deg'), 'RMS_X': ParaType(keys=('vel', 'rms', 'x'), unit='m'), 'RMS_Y': ParaType(keys=('vel', 'rms', 'y'), unit='m'), 'RMS_Z': ParaType(keys=('vel', 'rms', 'z'), unit='m'), 'RMS_E': ParaType(keys=('vel', 'rms', 'e'), unit='m'), 'RMS_N': ParaType(keys=('vel', 'rms', 'n'), unit='m'), 'RMS_U': ParaType(keys=('vel', 'rms', 'u'), unit='m'), 'OFFSET_X': ParaType(keys=('vel', 'offset', 'x'), unit='m'), 'OFFSET_Y': ParaType(keys=('vel', 'offset', 'y'), unit='m'), 'OFFSET_Z': ParaType(keys=('vel', 'offset', 'z'), unit='m'), 'OFFSET_E': ParaType(keys=('vel', 'offset', 'e'), unit='m'), 'OFFSET_N': ParaType(keys=('vel', 'offset', 'n'), unit='m'), 'OFFSET_U': ParaType(keys=('vel', 'offset', 'u'), unit='m'), 'VEL_X_SIG': ParaType(keys=('vel', 'trend_sigma', 'x'), unit='m/y'), 'VEL_Y_SIG': ParaType(keys=('vel', 'trend_sigma', 'z'), unit='m/y'), 'VEL_E_SIG': ParaType(keys=('vel', 'trend_sigma', 'e'), unit='m/y'), 'VEL_N_SIG': ParaType(keys=('vel', 'trend_sigma', 'n'), unit='m/y'), 'VEL_U_SIG': ParaType(keys=('vel', 'trend_sigma', 'u'), unit='m/y'), 'BIAS_X_SIG': ParaType(keys=('vel', 'bias_sigma', 'x'), unit='m'), 'BIAS_Y_SIG': ParaType(keys=('vel', 'bias_sigma', 'y'), unit='m'), 'BIAS_Z_SIG': ParaType(keys=('vel', 'bias_sigma', 'z'), unit='m'), 'BIAS_E_SIG': ParaType(keys=('vel', 'bias_sigma', 'e'), unit='m'), 'BIAS_N_SIG': ParaType(keys=('vel', 'bias_sigma', 'n'), unit='m'), 'BIAS_U_SIG': ParaType(keys=('vel', 'bias_sigma', 'u'), unit='m'), 'AMPA_X_SIG': ParaType(keys=('vel', 'amp_annual_sigma', 'x'), unit='m'), 'AMPA_Y_SIG': ParaType(keys=('vel', 'amp_annual_sigma', 'y'), unit='m'), 'AMPA_Z_SIG': ParaType(keys=('vel', 'amp_annual_sigma', 'z'), unit='m'), 'AMPA_E_SIG': ParaType(keys=('vel', 'amp_annual_sigma', 'e'), unit='m'), 'AMPA_N_SIG': ParaType(keys=('vel', 'amp_annual_sigma', 'n'), unit='m'), 'AMPA_U_SIG': ParaType(keys=('vel', 'amp_annual_sigma', 'u'), unit='m'), 'AMPS_X_SIG': ParaType(keys=('vel', 'amp_semiannual_sigma', 'x'), unit='m'), 'AMPS_Y_SIG': ParaType(keys=('vel', 'amp_semiannual_sigma', 'y'), unit='m'), 'AMPS_Z_SIG': ParaType(keys=('vel', 'amp_semiannual_sigma', 'z'), unit='m'), 'AMPS_E_SIG': ParaType(keys=('vel', 'amp_semiannual_sigma', 'e'), unit='m'), 'AMPS_N_SIG': ParaType(keys=('vel', 'amp_semiannual_sigma', 'n'), unit='m'), 'AMPS_U_SIG': ParaType(keys=('vel', 'amp_semiannual_sigma', 'u'), unit='m')})`


### **ParaType**

Full name: `midgard.writers.sinex_tms.ParaType`

Signature: `(keys=None, unit=None)`

A convenience class for defining a parameter type 

**Args:**

keys (tuple):          Keys of meta variable dictionary
unit (str):            Unit of parameter


### **TimeseriesBlocks**

Full name: `midgard.writers.sinex_tms.TimeseriesBlocks`

Signature: `(dset: 'Dataset', fid: 'FileHandle', station: str, contact: str, data_agency: str, file_agency: str, input_: str = '', organization: str = '', output: str = '', software: str = '', version: str = '001', data_field_types: None | collections.OrderedDict[str, str] = None)`

This class takes care of the writing of the different blocks in the SINEX TMS files


### **sinex_tms**()

Full name: `midgard.writers.sinex_tms.sinex_tms`

Signature: `(dset: 'Dataset', station: str, file_path: pathlib.PosixPath, contact: str, data_agency: str, file_agency: str, input_: str, organization: str, output: str, software: str, version: str) -> None`

Write timeseries file in SINEX TMS format

**Args:**

- `dset`:  A dataset containing the data.
