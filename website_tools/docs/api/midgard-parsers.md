# midgard.parsers
Framework for parsers

**Description:**

To add a new parser, simply create a new .py-file which defines a class
inheriting from parsers.Parser. The class needs to be decorated with the
`midgard.dev.plugins.register` decorator as follows:

    from midgard.parsers import parser
    from midgard.lib import plugins

    @plugins.register
    class MyNewParser(parser.Parser):
        ...

To use a parser, you will typically use the `parse_file`-function defined below

    from midgard import parsers
    my_new_parser = parsers.parse_file('my_new_parser', 'file_name.txt', ...)
    my_data = my_new_parser.as_dict()

The name used in `parse_file` to call the parser is the name of the module
(file) containing the parser.


### **names**()

Full name: `midgard.parsers.names`

Signature: `() -> List[str]`

List the names of the available parsers

**Returns:**

Names of the available parsers


### **parse_file**()

Full name: `midgard.parsers.parse_file`

Signature: `(parser_name: str, file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, timer_logger: Union[Callable[[str], NoneType], NoneType] = None, use_cache: bool = False, **parser_args: Any) -> midgard.parsers._parser.Parser`

Use the given parser on a file and return parsed data

Specify `parser_name` and `file_path` to the file that should be parsed. The following parsers are available:

{doc_parser_names}

Data can be retrieved either as Dictionaries, Pandas DataFrames or Midgard Datasets by using one of the methods
`as_dict`, `as_dataframe` or `as_dataset`.

Example:

    >>> df = parse_file('rinex2_obs', 'ande3160.16o').as_dataframe()  # doctest: +SKIP

**Args:**

- `parser_name`:    Name of parser
- `file_path`:      Path to file that should be parsed.
- `encoding`:       Encoding in file that is parsed.
- `timer_logger`:   Logging function that will be used to log timing information.
- `use_cache`:      Whether to use a cache to avoid parsing the same file several times. (TODO: implement this)
- `parser_args`:    Input arguments to the parser

**Returns:**

- `Parser`:  Parser with the parsed data


## midgard.parsers._parser
Basic functionality for parsing datafiles, extended by individual parsers

**Description:**

This module contains functions and classes for parsing datafiles. It should typically be used by calling
`parsers.parse_file`:

**Example:**

    from midgard import parsers
    my_new_parser = parsers.parse_file('my_new_parser', 'file_name.txt', ...)
    my_data = my_new_parser.as_dict()



### **Parser**

Full name: `midgard.parsers._parser.Parser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

An abstract base class that has basic methods for parsing a datafile

This class provides functionality for parsing a file. You should inherit from one of the specific parsers like for
instance ChainParser, LineParser, SinexParser etc

**Attributes:**

data (Dict):                  The (observation) data read from file.
data_available (Boolean):     Indicator of whether data are available.
file_encoding (String):       Encoding of the datafile.
file_path (Path):             Path to the datafile that will be read.
meta (Dict):                  Metainformation read from file.
parser_name (String):         Name of the parser (as needed to call parsers.parse_...).        


## midgard.parsers._parser_chain
Basic functionality for parsing datafiles line by line

**Description:**

This module contains functions and classes for parsing datafiles.


**Example:**

    from midgard import parsers
    my_new_parser = parsers.parse_file('my_new_parser', 'file_name.txt', ...)
    my_data = my_new_parser.as_dict()



### **ChainParser**

Full name: `midgard.parsers._parser_chain.ChainParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

An abstract base class that has basic methods for parsing a datafile

This class provides functionality for parsing a file with chained groups of information. You should inherit from
this one, and at least specify the necessary parameters in `setup_parser`.


### **ParserDef**

Full name: `midgard.parsers._parser_chain.ParserDef`

Signature: `(end_marker: Callable[[str, int, str], bool], label: Callable[[str, int], Any], parser_def: Dict[Any, Dict[str, Any]], skip_line: Union[Callable[[str], bool], NoneType] = None, end_callback: Union[Callable[[Dict[str, Any]], NoneType], NoneType] = None)`

A convenience class for defining the necessary fields of a parser

A single parser can read and parse one group of datalines, defined through the ParserDef by specifying how to parse
each line (parser_def), how to identify each line (label), how to recognize the end of the group of lines
(end_marker) and finally what (if anything) should be done after all lines in a group is read (end_callback).

The end_marker, label, skip_line and end_callback parameters should all be functions with the following signatures:

    end_marker   = func(line, line_num, next_line)
    label        = func(line, line_num)
    skip_line    = func(line)
    end_callback = func(cache)

The parser definition `parser_def` includes the `parser`, `field`, `strip` and `delimiter` entries. The `parser`
entry points to the parser function and the `field` entry defines how to separate the line in fields. The separated
fields are saved either in a dictionary or in a list. In the last case the line is split on whitespace by
default. With the `delimiter` entry the default definition can be overwritten. Leading and trailing whitespace
characters are removed by default before a line is parsed.  This default can be overwritten by defining the
characters, which should be removed with the 'strip' entry. The `parser` dictionary is defined like:

    parser_def = { <label>: {'fields':    <dict or list of fields>,
                             'parser':    <parser function>,
                             'delimiter': <optional delimiter for splitting line>,
                             'strip':     <optional characters to be removed from beginning and end of line>
                 }}

**Args:**

- `end_marker`:   A function returning True for the last line in a group.
- `label`:        A function returning a label used in the parser_def.
- `parser_def`:   A dict with 'parser' and 'fields' defining the parser.
- `skip_line`:    A function returning True if the line should be skipped.
- `end_callback`: A function called after reading all lines in a group.


## midgard.parsers._parser_line
Basic functionality for parsing datafiles line by line using Numpy

**Description:**

This module contains functions and classes for parsing datafiles.


**Example:**

    from midgard import parsers
    my_new_parser = parsers.parse_file('my_new_parser', 'file_name.txt', ...)
    my_data = my_new_parser.as_dict()



### **LineParser**

Full name: `midgard.parsers._parser_line.LineParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

An abstract base class that has basic methods for parsing a datafile

This class provides functionality for using numpy to parse a file line by line. You should inherit from this one,
and at least specify the necessary parameters in `setup_parser`.


## midgard.parsers._parser_rinex
Basic functionality for parsing Rinex files

**Description:**

This module contains functions and classes for parsing Rinex files.

This file defines the general structure shared by most types of Rinex files, including header information. More
specific format details are implemented in subclasses. When calling the parser, you should call the apropriate parser
for a given Rinex format.



### **RinexHeader**

Full name: `midgard.parsers._parser_rinex.RinexHeader`

Signature: `(marker: str, fields: Dict[str, Tuple[int, int]], parser: Callable[[Dict[str, str]], Dict[str, Any]])`

A convenience class for defining how a Rinex header is parsed

**Args:**

- `marker`:  Marker of header (as defined in columns 60 and onward).
- `fields`:  Dictionary with field names as keys, tuple of start- and end-columns as value.
- `parser`:  Function that will parse the fields.


### **RinexParser**

Full name: `midgard.parsers._parser_rinex.RinexParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

An abstract base class that has basic methods for parsing a datafile

This class provides functionality for reading Rinex header data. You should inherit from this one,
and at least implement `parse_epochs`.


### **parser_cache**()

Full name: `midgard.parsers._parser_rinex.parser_cache`

Signature: `(func: Callable[[ForwardRef('RinexParser'), Dict[str, str], List[Dict[str, str]]], Dict[str, Any]]) -> Callable[[ForwardRef('RinexParser'), Dict[str, str]], Dict[str, Any]]`

Decorator for adding a cache to parser functions

## midgard.parsers._parser_sinex
Basic functionality for parsing Sinex datafiles

**Description:**

This module contains functions and classes for parsing Sinex datafiles.


**References:**

* SINEX Format: https://www.iers.org/IERS/EN/Organization/AnalysisCoordinator/SinexFormat/sinex.html



### **SinexBlock**

Full name: `midgard.parsers._parser_sinex.SinexBlock`

Signature: `(marker: str, fields: Tuple[midgard.parsers._parser_sinex.SinexField, ...], parser: Callable[[<built-in function array>, Tuple[str, ...]], Dict[str, Any]])`

A convenience class for defining a Sinex block

**Args:**

- `marker`:  Sinex marker denoting the block.
- `fields`:  Fields in Sinex block.
- `parser`:  Function used to parse the data.


### **SinexField**

Full name: `midgard.parsers._parser_sinex.SinexField`

Signature: `(name: str, start_col: int, dtype: Union[str, NoneType], converter: Union[str, NoneType] = None)`

A convenience class for defining the fields in a Sinex block

**Args:**

- `name`:       Name of field.
- `start_col`:  Starting column of field (First column is 0)
- `dtype`:      String, using numpy notation, defining type of field, use None to ignore field.
- `converter`:  Optional, name of converter to apply to field data.


### **SinexParser**

Full name: `midgard.parsers._parser_sinex.SinexParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, header: bool = True) -> None`

An abstract base class that has basic methods for parsing a Sinex file

This class provides functionality for parsing a sinex file with chained
groups of information. You should inherit from this one, and at least
specify which Sinex blocks you are interested in by implementing
`setup_parser`, as well as implement methods that parse each block if
needed.


### **parsing_factory**()

Full name: `midgard.parsers._parser_sinex.parsing_factory`

Signature: `() -> Callable[..., Dict[str, Any]]`

Create a default parsing function for a Sinex block

The default parsing function returns a dictionary containing all fields of
the block as separated arrays. This will be stored in self.data['{marker}']
with the {marker} of the current block.

**Returns:**

Simple parsing function for one Sinex block.


### **parsing_matrix_factory**()

Full name: `midgard.parsers._parser_sinex.parsing_matrix_factory`

Signature: `(marker: str, size_marker: str) -> Callable[..., Dict[str, Any]]`

Create a parsing function for parsing a matrix within a Sinex block

The default parsing function converts data to a symmetric matrix and stores
it inside `self.data[marker]`.

The size of the matrix is set to equal the number of parameters in the
`size_marker`-block. If that block is not parsed/found. The size is set to
the last given row index. If some zero elements in the matrix are omitted
this might be wrong.

**Args:**

- `marker`:       Marker of Sinex block.
- `size_marker`:  Marker of a different Sinex block indicating the size of the matrix.

**Returns:**

Simple parsing function for one Sinex block.


## midgard.parsers.anubis
A parser for reading Anubis xtr-files


### **AnubisXtrParser**

Full name: `midgard.parsers.anubis.AnubisXtrParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading Anubis XTR files



## midgard.parsers.bcecmp_sisre
A parser for reading DLR BCEcmp Software SISRE output files

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='bcecmp_sisre', file_path='BCEcmp_GAL_FNAV_E1E5A_com_2018_032.OUT')
    data = p.as_dict()

**Description:**

Reads data from files in the BCEcmp Software output file format. The BCEcmp Software is developed and used by DLR.



### **BcecmpParser**

Full name: `midgard.parsers.bcecmp_sisre.BcecmpParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading DLR BCEcmp Software output files.

The following **data** are available after reading BCEcmp Software output file:

| Key                   | Description                                                                          |
|-----------------------|--------------------------------------------------------------------------------------|
| age_min               | age of ephemeris in [min]                                                            |
| clk_diff_with_dt_mean | Satellite clock correction difference corrected for average satellite clock offset   |
|                       | difference for given GNSS and epoch in [m]                                           |
| dalong_track          | Along-track orbit difference in [m]                                                  |
| dcross_track          | Cross-track orbit difference in [m]                                                  |
| dradial               | Radial orbit difference in [m]                                                       |
| dradial_wul           | Worst-user-location (wul) SISRE?                                                     |
| satellite             | Satellite PRN number together with GNSS identifier (e.g. G07)                        |
| sisre                 | Signal-in-space range error [m]                                                      |
| time                  | Observation time                                                                     |
| used_iodc             | GPS: IODC (Clock issue of data indicates changes (set equal to IODE))                |
|                       | QZSS: IODC                                                                           |
| used_iode             | Ephemeris issue of data indicates changes to the broadcast ephemeris:                |
|                       |   - GPS: Ephemeris issue of data (IODE), which is set equal to IODC                  |
|                       |   - Galileo: Issue of Data of the NAV batch (IODnav)                                 |
|                       |   - QZSS: Ephemeris issue of data (IODE)                                             |
|                       |   - BeiDou: Age of Data Ephemeris (AODE)                                             |
|                       |   - IRNSS: Issue of Data, Ephemeris and Clock (IODEC)                                |

and **meta**-data:

| Key                   | Description                                                                          |
|-----------------------|--------------------------------------------------------------------------------------|
| \__data_path__        | File path                                                                            |
| \__parser_name__      | Parser name                                                                          |


## midgard.parsers.csv_
A parser for reading CSV output files

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='csv_', file_path='ADOP20473_0000.csv')
    data = p.as_dict()

**Description:**

Reads data from files in CSV output format. The header information of the CSV file is not read (TODO).



### **CsvParser**

Full name: `midgard.parsers.csv_.CsvParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading CSV output files

The CSV data header line is used to define the keys of the **data** dictionary. The values of the **data** 
dictionary are represented by the CSV colum values.

Following **meta**-data are available after reading of CSV file:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |


## midgard.parsers.discontinuities_snx
A parser for reading data from discontinuities.snx in SINEX format

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='discontinuities_snx', file_path='discontinuities_snx')
    data = p.as_dict()

**Description:**

Reads discontinuities of GNSS station timeseries in SINEX format .




### **DiscontinuitiesSnxParser**

Full name: `midgard.parsers.discontinuities_snx.DiscontinuitiesSnxParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, header: bool = True) -> None`

A parser for reading data from discontinuties.snx file in SINEX format

The solution discontinuity dictionary has as keys the site identifiers and as value the 'solution_discontinuity'
entry. The dictionary has following strucuture:

   self.data[site] = { 'solution_discontinuity':  [] }   # SOLUTION/DISCONTINUITY SINEX block information

with the 'solution_discontinuity' dictionary entries

   solution_discontinuity[ii]     = [ 'point_code':         point_code,
                                      'soln':               soln,
                                      'obs_code':           obs_code,
                                      'start_time':         start_time,
                                      'end_time':           end_time,
                                      'event_code':         event_code,
                                      'description':        description ]

The counter 'ii' ranges from 0 to n and depends on how many discontinuities exists for a site. Note also, that 
time entries (e.g. start_time, end_time) are given as 'datetime'. If the time is defined as 00:000:00000 in the
SINEX file, then the value is saved as 'None' in the Sinex class.


## midgard.parsers.galileo_constellation_html
A parser for reading Galileo constellation info from a web page

See https://www.gsc-europa.eu/system-status/Constellation-Information for an example


### **GalileoConstellationHTMLParser**

Full name: `midgard.parsers.galileo_constellation_html.GalileoConstellationHTMLParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, url: Union[str, NoneType] = None) -> None`

A parser for reading Galileo constellation info from a web page

See https://www.gsc-europa.eu/system-status/Constellation-Information for an example


## midgard.parsers.gipsy_tdp
A parser for reading NASA JPL Gipsy time dependent parameter (TDP) file

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsy_tdp', file_path='final.tdp')
    data = p.as_dict()

**Description:**

Reads data from files in Gipsy time dependent parameter (TDP) format.



### **GipsyTdpParser**

Full name: `midgard.parsers.gipsy_tdp.GipsyTdpParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading Gipsy time dependent parameter (TDP) file

Following **data** are available after reading Gipsy TDP output file:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| apriori_value        | Nominal value. This field contains the last value used by the model.                 |
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


## midgard.parsers.gipsyx_gdcov
A parser for reading NASA JPL GipsyX `gdcov` format file

`gdcov` format file includes GipsyX estimates and covariance information. 

NOTE: At the moment this parser can only read station estimate and covariance information, that means STA.X, STA.Y 
      and STA.Z parameters.

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_gdcov', file_path='smoothFinal.gdcov')
    data = p.as_dict()

**Description:**

Reads data from files in GipsyX `gdcov` format.



### **GipsyxGdcovParser**

Full name: `midgard.parsers.gipsyx_gdcov.GipsyxGdcovParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading GipsyX `gdcov` format file

Following **data** are available after reading GipsyX `gdcov` output file:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| column               | Column number of correlations                                                        |
| correlation          | Correlation values                                                                   |
| parameter            | Parameter name. An arbitrary sequence of letters [A-Z,a-z], digits[0-9], and "."     |
|                      | without spaces.                                                                      |
| row                  | Row number of correlations                                                           |
| station              | Station name.                                                                        |    
| sigma                | Standard deviation of the parameter.                                                 |
| time_past_j2000      | Time given in GPS seconds past J2000, whereby GipsyX uses following definition:      |
|                      | J2000 is continuous seconds past Jan. 1, 2000 11:59:47 UTC.                          |
| estimate             | Parameter estimate at the given time                                                 |


and **meta**-data:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |


## midgard.parsers.gipsyx_residual
A parser for reading NASA JPL GipsyX residual file

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_residual', file_path='finalResiduals.out')
    data = p.as_dict()

**Description:**

Reads data from files in GipsyX residual format.



### **GipsyxResidualParser**

Full name: `midgard.parsers.gipsyx_residual.GipsyxResidualParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading GipsyX residual file

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


## midgard.parsers.gipsyx_series
A parser for reading NASA JPL GipsyX timeseries file

**Example:**

    from analyx import parsers
    p = parsers.parse_file(parser_name='gipsyx_series', file_path='NYA1.series')
    data = p.as_dict()

**Description:**

Reads data from files in GipsyX timeseries format.



### **GipsyxSeriesParser**

Full name: `midgard.parsers.gipsyx_series.GipsyxSeriesParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading GipsyX timeseries file

Following **data** are available after reading GipsyX residual output file:


| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| corr_en              | Correlation East-North.                                                              |
| corr_ev              | Correlation East-Vertical.                                                           |
| corr_nv              | Correlation North-Vertical.                                                          |
| day                  | Day                                                                                  |
| decimalyear          | Date in unit year.                                                                   |
| east                 | East coordinate in [m].                                                              |
| east_sigma           | Standard devication of east coordinate in [m].                                       |
| hour                 | Hour                                                                                 |
| minute               | Minute                                                                               |
| month                | Month                                                                                |
| north                | North coordinate in [m].                                                             |
| north_sigma          | Standard devication of north coordinate in [m].                                      |
| second               | Second                                                                               |
| time_past_j2000      | Time given in GPS seconds past J2000, whereby GipsyX uses following definition:      |
|                      | J2000 is continuous seconds past Jan. 1, 2000 11:59:47 UTC.                          |
| vertical             | Vertical coordinate in [m].                                                          |
| vertical_sigma       | Standard devication of vertical coordinate in [m].                                   |
| year                 | Year                                                                                 |

and **meta**-data:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |


## midgard.parsers.gipsyx_summary
A parser for reading GipsyX summary output file

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_summary', file_path='gipsyx_summary')
    data = p.as_dict()

**Description:**

Reads data from files in GipsyX summary output format.



### **GipsyxSummary**

Full name: `midgard.parsers.gipsyx_summary.GipsyxSummary`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading GipsyX summary file

GipsyX summary file **data** are grouped as follows:

| Key                   | Description                                                                          |
|-----------------------|--------------------------------------------------------------------------------------|
| position              | Dictionary with position summary information                                         |
| residual              | Dictionary with residual summary information                                         |
| station               | Station name                                                                         |

**position** entries are:

| Key                   | Description                                                                          |
|-----------------------|--------------------------------------------------------------------------------------|
| pos_x                 | X-coordinate of station position solution                                            |
| pos_y                 | Y-coordinate of station position solution                                            |
| pos_z                 | Z-coordinate of station position solution                                            |
| pos_vs_ref_x          | X-coordinate of difference between solution and reference of station coordinate      |
| pos_vs_ref_y          | Y-coordinate of difference between solution and reference of station coordinate      |
| pos_vs_ref_z          | Z-coordinate of difference between solution and reference of station coordinate      |
| pos_vs_ref_e          | East-coordinate of difference between solution and reference of station coordinate   |
| pos_vs_ref_n          | North-coordinate of difference between solution and reference of station coordinate  |
| pos_vs_ref_v          | Vertical-coordinate of difference between solution and reference of station          |
|                       | coordinate                                                                           |


**residual** entries are:

| Key                   | Description                                                                          |
|-----------------------|--------------------------------------------------------------------------------------|
| code_max              | Maximal residual of used pseudo-range observations                                   |
| code_min              | Minimal residual of used pseudo-range observations                                   |
| code_num              | Number of used pseudo-range observations                                             |
| code_rms              | RMS of residuals from used pseudo-range observations                                 |
| code_outlier_max      | Maximal residual of rejected pseudo-range observations                               |
| code_outlier_min      | Minimal residual of rejected pseudo-range observations                               |
| code_outlier_num      | Number of rejected pseudo-range observations                                         |
| code_outlier_rms      | RMS of residuals from rejected pseudo-range observations                             |
| phase_max             | Maximal residual of used phase observations                                          |
| phase_min             | Minimal residual of used phase observations                                          |
| phase_num             | Number of used phase observations                                                    |
| phase_rms             | RMS of residuals from used phase observations                                        |
| phase_outlier_max     | Maximal residual of rejected phase observations                                      |
| phase_outlier_min     | Minimal residual of rejected phase observations                                      |
| phase_outlier_num     | Number of rejected phase observations                                                |
| phase_outlier_rms     | RMS of residuals from rejected phase observations                                    |


and **meta**-data:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |


## midgard.parsers.gipsyx_tdp
A parser for reading NASA JPL GipsyX time dependent parameter (TDP) file

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_tdp', file_path='final.tdp')
    data = p.as_dict()

**Description:**

Reads data from files in GipsyX time dependent parameter (TDP) format.



### **DatasetField**

Full name: `midgard.parsers.gipsyx_tdp.DatasetField`

Signature: `(name=None, category=None, dtype=None)`

A convenience class for defining a dataset field properties

**Args:**

name  (str):             Dataset field name
category (str):          Category of parameter (e.g. station or satellite parameter)
dtype (str):             Dataset data type


### **GipsyxTdpParser**

Full name: `midgard.parsers.gipsyx_tdp.GipsyxTdpParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading GipsyX time dependent parameter (TDP) file

Following **data** are available after reading GipsyX TDP output file:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| apriori              | Nominal value. This field contains the last value used by the model.                 |
| name                 | Parameter name. An arbitrary sequence of letters [A-Z,a-z], digits[0-9], and "."     |
|                      | without spaces.                                                                      |
| sigma                | Standard deviation of the parameter.                                                 |
| time_past_j2000      | Time given in GPS seconds past J2000, whereby GipsyX uses following definition:      |
|                      | J2000 is continuous seconds past Jan. 1, 2000 11:59:47 UTC.                          |
| value                | Parameter value at the given time                                                    |

and **meta**-data:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |


## midgard.parsers.glab_output
A parser for reading gLAB output files

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='glab_output', file_path='glab_output.txt')
    data = p.as_dict()

**Description:**




### **GlabOutputParser**

Full name: `midgard.parsers.glab_output.GlabOutputParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading gLAB output files

The keys of the **data** dictionary are defined depending, which kind of gLAB output file is read. The values of 
the **data** dictionary are represented by the gLAB colum values.

Following **meta**-data are available after reading of gLAB files:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |


## midgard.parsers.gnss_android_raw_data
A parser for reading GNSS raw data from `GnssLogger` Android App

**Example:**
    
    from midgard import parsers
    
    # Parse data
    parser = parsers.parse_file(parser_name="gnss_android_raw_data", file_path=file_path)
    
    # Get Dataset with parsed data
    dset = parser.as_dataset()

**Description:**

Reads raw data file from `GnssLogger` Android App.



### **GnssAndroidRawDataParser**

Full name: `midgard.parsers.gnss_android_raw_data.GnssAndroidRawDataParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`



## midgard.parsers.gnss_antex
A parser for reading ANTEX format 1.4 data

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnss_antex', file_path='igs14.atx')
    data = p.as_dict()

**Description:**

Reads data from files in the GNSS Antenna Exchange (ANTEX) file format version 1.4 (see :cite:`antex`).



### **AntexParser**

Full name: `midgard.parsers.gnss_antex.AntexParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading ANTEX file

The parser reads GNSS ANTEX format 1.4 (see :cite:`antex`).

The 'data' attribute is a dictionary with GNSS satellite PRN or receiver antenna as key. The GNSS satellite
antenna corrections are time dependent and saved with "valid from" datetime object entry. The dictionary looks
like:

    dout = { <prn> : { <valid from>: { cospar_id:   <value>,
                                       sat_code:    <value>,
                                       sat_type:    <value>,
                                       valid_until: <value>,
                                       azimuth:     <list with azimuth values>,
                                       elevation:   <list with elevation values>,
                                       <frequency>: { azi: [<list with azimuth-elevation dependent corrections>],
                                                      neu: [north, east, up],
                                                      noazi: [<list with elevation dependent corrections>] }}},

             <receiver antenna> : { azimuth:     <list with azimuth values>,
                                    elevation:   <list with elevation values>,
                                    <frequency>: { azi: [<array with azimuth-elevation dependent corrections>],
                                                   neu: [north, east, up],
                                                   noazi: [<list with elevation dependent corrections>] }}}

with following entries:

| Value              | Type              | Description                                                            |
|--------------------|-------------------|------------------------------------------------------------------------|
| azi                | numpy.ndarray     | Array with azimuth-elevation dependent antenna correction in [mm] with |
|                    |                   | the shape: number of azimuth values x number of elevation values.      |
| azimuth            | numpy.ndarray     | List with azimuth values in [rad] corresponding to antenna corrections |
|                    |                   | given in `azi`.                                                        |
| cospar_id          | str               | COSPAR ID <yyyy-xxxa>: yyyy -> year when the satellite was put in      |
|                    |                   | orbit, xxx -> sequential satellite number for that year, a -> alpha    |
|                    |                   | numeric sequence number within a launch                                |
| elevation          | numpy.ndarray     | List with elevation values in [rad] corresponding to antenna           |
|                    |                   | corrections given in `azi` or `noazi`.                                 |
| <frequency>        | str               | Frequency identifier (e.g. G01 - GPS L1)                               |
| neu                | list              | North, East and Up eccentricities in [m]. The eccentricities of the    |
|                    |                   | mean antenna phase center is given relative to the antenna reference   |
|                    |                   | point (ARP) for receiver antennas or to the center of mass of the      |
|                    |                   | satellite in X-, Y- and Z-direction.                                   |
| noazi              | numpy.ndarray     | List with elevation dependent (non-azimuth-dependent) antenna          |
|                    |                   | correction in [mm].                                                    |
| <prn>              | str               | Satellite code e.g. GPS PRN, GLONASS slot or Galileo SVID number       |
| <receiver antenna> | str               | Receiver antenna name together with radome code                        |
| sat_code           | str               | Satellite code e.g. GPS SVN, GLONASS number or Galileo GSAT number     |
| sat_type           | str               | Satellite type (e.g. BLOCK IIA)                                        |
| valid_from         | datetime.datetime | Start of validity period of satellite in GPS time                      |
| valid_until        | datetime.datetime | End of validity period of satellite in GPS time                        |

The 'meta' attribute is a dictionary with following entries:

| Value          | Type | Description                                      |
|----------------|------|--------------------------------------------------|
| comment        | list | Header commments given in list line by line      |
| pcv_type       | str  | Phase center variation type                      |
| ref_antenna    | str  | Reference antenna type for relative antenna      |
| ref_serial_num | str  | Serial number of the reference antenna           |
| sat_sys        | str  | Satellite system                                 |
| version        | str  | Format version                                   |

**Attributes:**

- `data`:            (dict), Contains the (observation) data read from file.
- `data_available`:  (bool), Indicator of whether data are available.
- `file_path`:       (pathlib.Path), File path.
- `parser_name`:     (str), Parser name.
- `meta`:            (dict), Contains metainformation read from file.


## midgard.parsers.gnss_bernese_crd
A parser for reading Bernese CRD file

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnss_bernese_crd', file_path='W20216.CRD')
    data = p.as_dict()

**Description:**

Reads data from files in Bernese CRD format.



### **GnssCrdParser**

Full name: `midgard.parsers.gnss_bernese_crd.GnssCrdParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading Bernese CRD file

Following **data** are available after reading Bernese CRD file:

| Parameter           | Description                                                                           |
|---------------------|---------------------------------------------------------------------------------------|
| num                 | Number of station coordinate solution                                                 |
| station             | 4-digit station identifier                                                            |
| domes               | Domes number                                                                          |
| gpssec              | Seconds of GPS week                                                                   |
| pos_x               | X-coordinate of station position                                                      |
| pos_y               | Y-coordinate of station position                                                      |
| pos_z               | Z-coordinate of station position                                                      |
| flag                | Flag                                                                                  |

and **meta**-data:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |



## midgard.parsers.gnss_galat_results
A parser for GALAT single point positioning result files

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnss_galat_results', file_path='galat_results.txt')
    data = p.as_dict()

**Description:**

Reads data from files in GALAT result format.



### **GalatResults**

Full name: `midgard.parsers.gnss_galat_results.GalatResults`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading GALAT single point positioning result files

Following **data** are available after reading GALAT SPP result file:

| Key                      | Description                                                                      |
|--------------------------|----------------------------------------------------------------------------------|
| time                     | Time epoch                                                                       |
| latitude                 | Latitude in degree                                                               |
| longitude                | Longitude in degree                                                              |
| height                   | Height in [m]                                                                    |
| dlatitude                | Latitude related to reference coordinate in [m]                                  |
| dlongitude               | Longitude related to reference coordinate in [m]                                 |
| dheight                  | Height related to reference coordinate in [m]                                    |
| hpe                      | Horizontal positioning error (HPE) in [m]                                        |
| vpe                      | Vertical positioning error (VPE) in [m]                                          |
| site_vel_3d              | 3D site velocity in [m/s]                                                        |
| pdop                     | Precision dilution of precision                                                  |
| num_satellite_available  | Number of available satellites                                                   |
| num_satellite_used       | Number of used satellites                                                        |


and **meta**-data:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__params__          | np.genfromtxt parameters                                                             |
| \__parser_name__     | Parser name                                                                          |


## midgard.parsers.gnss_sinex_igs
A parser for reading data from igs.snx file based on IGS sitelog files in SINEX format

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='gnss_sinex_igs', file_path='igs.snx')
    data = p.as_dict()

**Description:**

Reads station information (e.g. approximated station coordinates, receiver and antenna type, station eccentricities,
...) igs.snx file in SINEX format.




### **IgsSnxParser**

Full name: `midgard.parsers.gnss_sinex_igs.IgsSnxParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, header: bool = True) -> None`

A parser for reading data from igs.snx file based on IGS sitelog files in SINEX format

site - Site dictionary, whereby keys are the site identifiers and values are a site entry
       dictionary with the keys 'site_antenna', 'site_eccentricity', 'site_id' and 'site_receiver'. The
       site dictionary has following strucuture:

          self.site[site] = { 'site_antenna':          [],  # SITE/ANTENNA SINEX block information
                              'site_eccentricity':     [],  # SITE/ECCENTRICITY block information
                              'site_id':               {},  # SITE/ID block information
                              'site_receiver':         [],  # SITE/RECEIVER block information }

       with the site entry dictionary entries

          site_antenna[ii]      = { 'point_code':         point_code,
                                    'soln':               soln,
                                    'obs_code':           obs_code,
                                    'start_time':         start_time,
                                    'end_time':           end_time,
                                    'antenna_type':       antenna_type,
                                    'radome_type':        radome_type,
                                    'serial_number':      serial_number }

          site_eccentricity[ii] = { 'point_code':         point_code,
                                    'soln':               soln,
                                    'obs_code':           obs_code,
                                    'start_time':         start_time,
                                    'end_time':           end_time,
                                    'reference_system':   reference_system,
                                    'vector_1':           vector_1,
                                    'vector_2':           vector_2,
                                    'vector_3':           vector_3,
                                    'vector_type':        UNE }

          site_id               = { 'point_code':         point_code,
                                    'domes':              domes,
                                    'marker':             marker,
                                    'obs_code':           obs_code,
                                    'description':        description,
                                    'approx_lon':         approx_lon,
                                    'approx_lat':         approx_lat,
                                    'approx_height':      approx_height }

          site_receiver[ii]     = { 'point_code':         point_code,
                                    'soln':               soln,
                                    'obs_code':           obs_code,
                                    'start_time':         start_time,
                                    'end_time':           end_time,
                                    'receiver_type':      receiver_type,
                                    'serial_number':      serial_number,
                                    'firmware':           firmware }

       The counter 'ii' ranges from 0 to n and depends on how many antenna type, receiver type and
       antenna monument changes were done at each site. Note also, that time entries (e.g. start_time,
       end_time) are given in Modified Julian Date. If the time is defined as 00:000:00000 in the SINEX
       file, then the value is saved as 'None' in the Sinex class.



## midgard.parsers.rinex212_nav
A parser for reading GNSS RINEX navigation file (exception GLONASS and SBAS)

**Example:**
    from midgard import parsers

    # Parse data
    parser = parsers.parse_file(parser_name="rinex212_nav", file_path=file_path)

    # Get Dataset with parsed data
    dset = parser.as_dataset()


**Description:**

Reads GNSS data from files in the RINEX navigation file format 2.12 (see :cite:`rinex2`). An exception is, that this
parser does not handle GLONASS and SBAS navigation messages. All navigation time epochs (time of clock (toc)) are
converted to GPS time scale.

The navigation message is not defined for GALILEO, BeiDou, QZSS and IRNSS in RINEX format 2.12. In this case the RINEX
3.03 definition is used (see :cite:`rinex3`).



### **Rinex212NavParser**

Full name: `midgard.parsers.rinex212_nav.Rinex212NavParser`

Signature: `(*args: Tuple[Any], **kwargs: Dict[Any, Any])`

A parser for reading RINEX navigation file

The parser reads GNSS broadcast ephemeris in RINEX format 2.12 (see :cite:`rinex2`).

#TODO: Would it not be better to use one leading underscore for non-public methods and instance variables.

**Attributes:**

data (Dict):                  The (observation) data read from file.
data_available (Boolean):     Indicator of whether data are available.
file_encoding (String):       Encoding of the datafile.
file_path (Path):             Path to the datafile that will be read.
meta (Dict):                  Metainformation read from file.
parser_name (String):         Name of the parser (as needed to call parsers.parse_...).        
system (String):              GNSS identifier.

Methods:
    as_dataframe()                Return the parsed data as a Pandas DataFrame
    as_dataset()                  Return the parsed data as a Midgard Dataset
    as_dict()                     Return the parsed data as a dictionary
    parse()                       Parse data
    parse_line()                  Parse line
    postprocess_data()            Do simple manipulations on the data after they are read
    read_data()                   Read data from the data file
    setup_parser()                Set up information needed for the parser
    setup_postprocessors()        List postprocessors that should be called after parsing

    _check_nav_message()          Check correctness of navigation message
    _get_system_from_file_extension()  Get GNSS by reading RINEX navigation file extension
    _parse_file()                 Read a data file and parse the content
    _parse_ionospheric_corr()     Parse entries of RINEX header `IONOSPHERIC CORR` to instance variable `meta`.
    _parse_leap_seconds()         Parse entries of RINEX header `LEAP SECONDS` to instance variable `meta`.
    _parse_obs_float()            Parse float entries of RINEX navigation data block to instance variable 'data'.
    _parse_observation_epoch()    Parse observation epoch information of RINEX navigation data record
    _parse_string()               Parse string entries of SP3 header to instance variable 'meta'
    _parse_string_list()          Parse string entries of RINEX header to instance variable 'meta' in a list
    _parse_time_system_corr()     Parse entries of RINEX header `TIME SYSTEM CORR` to instance variable `meta`.
    _rename_fields_based_on_system()  Rename general GNSS fields to GNSS specific ones
    _time_system_correction()     Apply correction to given time system for getting GPS time scale


### SYSNAMES (dict)
`SYSNAMES = {'gnss_data_info': {'G': 'codes_l2', 'J': 'codes_l2', 'E': 'data_source'}, 'gnss_interval': {'G': 'fit_interval', 'J': 'fit_interval', 'C': 'age_of_clock_corr'}, 'gnss_iodc_groupdelay': {'G': 'iodc', 'J': 'iodc', 'E': 'bgd_e1_e5b', 'C': 'tgd_b2_b3'}, 'gnss_l2p_flag': {'G': 'l2p_flag', 'J': 'l2p_flag'}, 'gnss_tgd_bgd': {'G': 'tgd', 'J': 'tgd', 'E': 'bgd_e1_e5a', 'C': 'tgd_b1_b3', 'I': 'tgd'}}`


### SYSTEM_FILE_EXTENSION (dict)
`SYSTEM_FILE_EXTENSION = {'n': 'G', 'g': 'R', 'l': 'E'}`


### SYSTEM_TIME_OFFSET_TO_GPS_SECOND (dict)
`SYSTEM_TIME_OFFSET_TO_GPS_SECOND = {'C': 14, 'E': 0, 'I': 0, 'J': 0}`


### SYSTEM_TIME_OFFSET_TO_GPS_WEEK (dict)
`SYSTEM_TIME_OFFSET_TO_GPS_WEEK = {'C': 1356, 'E': 0, 'I': 0, 'J': 0}`


## midgard.parsers.rinex2_nav
A parser for reading GNSS RINEX navigation file (exception GLONASS and SBAS)

**Example:**
    from midgard import parsers

    # Parse data
    parser = parsers.parse_file(parser_name="rinex2_nav", file_path=file_path)

    # Get Dataset with parsed data
    dset = parser.as_dataset()


**Description:**

Reads GNSS data from files in the RINEX navigation file format 2.11 (see :cite:`rinex2`). An exception is, that this
parser does not handle GLONASS and SBAS navigation messages. All navigation time epochs (time of clock (toc)) are
converted to GPS time scale.

The navigation message is not defined for GALILEO, BeiDou, QZSS and IRNSS in RINEX format 2.11. In this case the RINEX
3.03 definition is used (see :cite:`rinex3`).



### **Rinex2NavParser**

Full name: `midgard.parsers.rinex2_nav.Rinex2NavParser`

Signature: `(*args: Tuple[Any], **kwargs: Dict[Any, Any])`

A parser for reading RINEX navigation file

The parser reads GNSS broadcast ephemeris in RINEX format 2.11 (see :cite:`rinex2`).

#TODO: Would it not be better to use one leading underscore for non-public methods and instance variables.

**Attributes:**

data (Dict):                  The (observation) data read from file.
data_available (Boolean):     Indicator of whether data are available.
file_encoding (String):       Encoding of the datafile.
file_path (Path):             Path to the datafile that will be read.
meta (Dict):                  Metainformation read from file.
parser_name (String):         Name of the parser (as needed to call parsers.parse_...).        
system (String):              GNSS identifier.

Methods:
    as_dataframe()                Return the parsed data as a Pandas DataFrame
    as_dataset()                  Return the parsed data as a Midgard Dataset
    as_dict()                     Return the parsed data as a dictionary
    parse()                       Parse data
    parse_line()                  Parse line
    postprocess_data()            Do simple manipulations on the data after they are read
    read_data()                   Read data from the data file
    setup_parser()                Set up information needed for the parser
    setup_postprocessors()        List postprocessors that should be called after parsing

    _check_nav_message()          Check correctness of navigation message
    _get_system_from_file_extension()  Get GNSS by reading RINEX navigation file extension
    _parse_file()                 Read a data file and parse the content
    _parse_ion_alpha()            Parse entries of RINEX header `ION ALPHA` to instance variable `meta`.
    _parse_ion_beta()             Parse entries of RINEX header `ION BETA` to instance variable `meta`.
    _parse_obs_float()            Parse float entries of RINEX navigation data block to instance variable 'data'.
    _parse_observation_epoch()    Parse observation epoch information of RINEX navigation data record
    _parse_string()               Parse string entries of SP3 header to instance variable 'meta'
    _parse_string_list()          Parse string entries of RINEX header to instance variable 'meta' in a list
    _parse_time_system_corr()     Parse entries of RINEX header `DELTA-UTC: A0,A1,T,W` to instance variable `meta`.
    _rename_fields_based_on_system()  Rename general GNSS fields to GNSS specific ones
    _time_system_correction()     Apply correction to given time system for getting GPS time scale


### SYSNAMES (dict)
`SYSNAMES = {'gnss_data_info': {'G': 'codes_l2', 'J': 'codes_l2', 'E': 'data_source'}, 'gnss_interval': {'G': 'fit_interval', 'J': 'fit_interval', 'C': 'age_of_clock_corr'}, 'gnss_iodc_groupdelay': {'G': 'iodc', 'J': 'iodc', 'E': 'bgd_e1_e5b', 'C': 'tgd_b2_b3'}, 'gnss_l2p_flag': {'G': 'l2p_flag', 'J': 'l2p_flag'}, 'gnss_tgd_bgd': {'G': 'tgd', 'J': 'tgd', 'E': 'bgd_e1_e5a', 'C': 'tgd_b1_b3', 'I': 'tgd'}}`


### SYSTEM_FILE_EXTENSION (dict)
`SYSTEM_FILE_EXTENSION = {'n': 'G', 'g': 'R', 'l': 'E'}`


### SYSTEM_TIME_OFFSET_TO_GPS_SECOND (dict)
`SYSTEM_TIME_OFFSET_TO_GPS_SECOND = {'C': 14, 'E': 0, 'I': 0, 'J': 0}`


### SYSTEM_TIME_OFFSET_TO_GPS_WEEK (dict)
`SYSTEM_TIME_OFFSET_TO_GPS_WEEK = {'C': 1356, 'E': 0, 'I': 0, 'J': 0}`


## midgard.parsers.rinex2_obs
A parser for reading Rinex data

**Example:**

    from midgard import parsers
    
    # Parse data
    parser = parsers.parse_file(parser_name="rinex2_obs", file_path=file_path)
    
    # Get Dataset with parsed data
    dset = parser.as_dataset()

**Description:**

Reads data from files in the Rinex file format 2.11 (see :cite:`rinex2`).



### **Rinex2Parser**

Full name: `midgard.parsers.rinex2_obs.Rinex2Parser`

Signature: `(*args: Tuple[Any], sampling_rate: Union[NoneType, float] = None, convert_unit: bool = False, **kwargs: Dict[Any, Any]) -> None`

A parser for reading RINEX observation file

The parser reads GNSS observations in RINEX format 2.11 (see :cite:`rinex2`). The GNSS observations
are sampled after sampling rate definition in configuration file.

**Attributes:**

convert_unit (Boolean):       Convert unit from carrier-phase and Doppler observation to meter. Exception:
                                  unit conversion for GLONASS observations is not implemented.
data (Dict):                  The (observation) data read from file.
data_available (Boolean):     Indicator of whether data are available.
file_encoding (String):       Encoding of the datafile.
file_path (Path):             Path to the datafile that will be read.
meta (Dict):                  Metainformation read from file.
parser_name (String):         Name of the parser (as needed to call parsers.parse_...).
sampling_rate (Float):        Sampling rate in seconds.
system (String):              GNSS identifier.
time_scale (String):          Time scale, which is used to define the time scale of Dataset. GPS time scale is
                                  used. If another time scale is given e.g. BDT, then the time entries are 
                                  converted to GPS time scale. An exception is if GLONASS time scale is given, 
                                  then UTC is used as time scale. Hereby should be noted, the reported GLONASS time
                                  has the same hours as UTC and not UTC+3 h as the original GLONASS System Time in
                                  the RINEX file definition.


### SYSTEM_TIME_OFFSET_TO_GPS_TIME (dict)
`SYSTEM_TIME_OFFSET_TO_GPS_TIME = {'BDT': 14, 'GAL': 0, 'IRN': 0, 'QZS': 0}`


## midgard.parsers.rinex3_nav
A parser for reading GNSS RINEX v3.03 navigation file (exception GLONASS and SBAS)

**Example:**

    from midgard import parsers

    # Parse data
    parser = parsers.parse_file(parser_name="rinex3_nav", file_path=file_path)

    # Get Dataset with parsed data
    dset = parser.as_dataset()

**Description:**

Reads GNSS data from files in the RINEX navigation file format 3.03 (see :cite:`rinex3`). An exception is also, that
this parser does not handle GLONASS and SBAS navigation messages. All navigation time epochs (time of clock (toc)) are
converted to GPS time scale.



### **Rinex3NavParser**

Full name: `midgard.parsers.rinex3_nav.Rinex3NavParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading RINEX navigation file

The parser reads GNSS broadcast ephemeris in RINEX format 3.03 (see :cite:`rinex3`) except for GLONASS and SBAS.

#TODO: Would it not be better to use one leading underscore for non-public methods and instance variables.

**Attributes:**

data (Dict):                  The (observation) data read from file.
data_available (Boolean):     Indicator of whether data are available.
file_encoding (String):       Encoding of the datafile.
file_path (Path):             Path to the datafile that will be read.
meta (Dict):                  Metainformation read from file.
parser_name (String):         Name of the parser (as needed to call parsers.parse_...).        
system (String):              GNSS identifier.

Methods:
    as_dataframe()                Return the parsed data as a Pandas DataFrame
    as_dataset()                  Return the parsed data as a Midgard Dataset
    as_dict()                     Return the parsed data as a dictionary
    parse()                       Parse data
    parse_line()                  Parse line
    postprocess_data()            Do simple manipulations on the data after they are read
    read_data()                   Read data from the data file
    setup_parser()                Set up information needed for the parser
    setup_postprocessors()        List postprocessors that should be called after parsing

    _check_nav_message()          Check correctness of navigation message
    _parse_file()                 Read a data file and parse the content
    _parse_ionospheric_corr()     Parse entries of RINEX header `IONOSPHERIC CORR` to instance variable `meta`.
    _parse_leap_seconds()         Parse entries of RINEX header `LEAP SECONDS` to instance variable `meta`.
    _parse_obs_float()            Parse float entries of RINEX navigation data block to instance variable 'data'.
    _parse_observation_epoch()    Parse observation epoch information of RINEX navigation data record
    _parse_string()               Parse string entries of SP3 header to instance variable 'meta'
    _parse_string_list()          Parse string entries of RINEX header to instance variable 'meta' in a list
    _parse_time_system_corr()     Parse entries of RINEX header `TIME SYSTEM CORR` to instance variable `meta`.
    _rename_fields_based_on_system()  Rename general GNSS fields to GNSS specific ones
    _time_system_correction()     Apply correction to given time system for getting GPS time scale


### SYSNAMES (dict)
`SYSNAMES = {'gnss_data_info': {'G': 'codes_l2', 'J': 'codes_l2', 'E': 'data_source'}, 'gnss_interval': {'G': 'fit_interval', 'J': 'fit_interval', 'C': 'age_of_clock_corr'}, 'gnss_iodc_groupdelay': {'G': 'iodc', 'J': 'iodc', 'E': 'bgd_e1_e5b', 'C': 'tgd_b2_b3'}, 'gnss_l2p_flag': {'G': 'l2p_flag', 'J': 'l2p_flag'}, 'gnss_tgd_bgd': {'G': 'tgd', 'J': 'tgd', 'E': 'bgd_e1_e5a', 'C': 'tgd_b1_b3', 'I': 'tgd'}}`


### SYSTEM_TIME_OFFSET_TO_GPS_SECOND (dict)
`SYSTEM_TIME_OFFSET_TO_GPS_SECOND = {'C': 14, 'E': 0, 'G': 0, 'I': 0, 'J': 0}`


### SYSTEM_TIME_OFFSET_TO_GPS_WEEK (dict)
`SYSTEM_TIME_OFFSET_TO_GPS_WEEK = {'C': 1356, 'E': 0, 'G': 0, 'I': 0, 'J': 0}`


## midgard.parsers.rinex3_obs
A parser for reading RINEX format 3.03 data

**Example:**

    from midgard import parsers
    
    # Parse data
    parser = parsers.parse_file(parser_name="rinex3_obs", file_path=file_path)
      
    # Get Dataset with parsed data
    dset = parser.as_dataset()

**Description:**

Reads data from files in the RINEX file format version 3.03 (see :cite:`rinex3`).




### **Rinex3Parser**

Full name: `midgard.parsers.rinex3_obs.Rinex3Parser`

Signature: `(*args: Tuple[Any], sampling_rate: Union[NoneType, float] = None, convert_unit: bool = False, **kwargs: Dict[Any, Any]) -> None`

A parser for reading RINEX observation file

The parser reads GNSS observations in RINEX format 3.03 (see :cite:`rinex3`). The GNSS observations
are sampled after sampling rate definition in configuration file.

**Attributes:**

convert_unit (Boolean):       Convert unit from carrier-phase and Doppler observation to meter. Exception:
                                  unit conversion for GLONASS observations is not implemented.
data (Dict):                  The (observation) data read from file.
data_available (Boolean):     Indicator of whether data are available.
file_encoding (String):       Encoding of the datafile.
file_path (Path):             Path to the datafile that will be read.
meta (Dict):                  Metainformation read from file.
parser_name (String):         Name of the parser (as needed to call parsers.parse_...).
sampling_rate (Float):        Sampling rate in seconds.
time_scale (String):          Time scale, which is used to define the time scale of Dataset. GPS time scale is
                                  used. If another time scale is given e.g. BDT, then the time entries are 
                                  converted to GPS time scale. An exception is if GLONASS time scale is given, 
                                  then UTC is used as time scale. Hereby should be noted, the reported GLONASS time
                                  has the same hours as UTC and not UTC+3 h as the original GLONASS System Time in
                                  the RINEX file definition.
system (String):              GNSS identifier.


### SYSTEM_TIME_OFFSET_TO_GPS_TIME (dict)
`SYSTEM_TIME_OFFSET_TO_GPS_TIME = {'BDT': 14, 'GAL': 0, 'IRN': 0, 'QZS': 0}`


## midgard.parsers.rinex_nav
A parser for reading GNSS RINEX navigation files

**Example:**

    from midgard.data import dataset
    from midgard import parsers

    # Parse data
    parser = parsers.parse(file_path=file_path)

    # Create a empty Dataset
    dset = data.Dataset()

    # Fill Dataset with parsed data
    parser.write_to_dataset(dset)


**Description:**

Reads GNSS ephemeris data from RINEX navigation file in format 2.11 (see :cite:`rinex2`) or 3.03 (see :cite:`rinex3`).



### **get_rinex2_or_rinex3**()

Full name: `midgard.parsers.rinex_nav.get_rinex2_or_rinex3`

Signature: `(file_path: pathlib.PosixPath) -> 'TODO'`

Use either Rinex2NavParser or Rinex3NavParser for reading orbit files in format 2.11 or 3.03.

Firstly the RINEX file version is read. Based on the read version number it is decided, which Parser should be
used.

**Args:**

file_path (pathlib.PosixPath):  File path to broadcast orbit file.


## midgard.parsers.slr_prediction
A parser for reading SLR prediction files

**Description:**

Reads data from files in the CPF file format as defined in http://ilrs.gsfc.nasa.gov/docs/2006/cpf_1.01.pdf



### **SlrPredictionParser**

Full name: `midgard.parsers.slr_prediction.SlrPredictionParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading SLR prediction files (CPF format)


## midgard.parsers.spring_csv
A parser for reading Spring CSV output files

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='spring_csv', file_path='ADOP20473_0000.csv')
    data = p.as_dict()

**Description:**

Reads data from files in Spring CSV output format. The header information of the Spring CSV file is not read (TODO).


### **SpringCsvParser**

Full name: `midgard.parsers.spring_csv.SpringCsvParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading Spring CSV output files

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


## midgard.parsers.terrapos_position
A parser for reading Terrapos position output file

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='terrapos_position', file_path='Gal_C1X_brdc_land_30sec_24hrs_FNAV-file.txt')
    data = p.as_dict()

**Description:**

Reads data from files in Terrapos position output format.



### **TerraposPositionParser**

Full name: `midgard.parsers.terrapos_position.TerraposPositionParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading Terrapos position output file

Following **data** are available after reading Terrapos position file:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| gpsweek              | GPS week                                                                             |
| gpssec               | Seconds of GPS week                                                                  |
| head                 | Head in [deg]                                                                        |
| height               | Ellipsoidal height in [m]                                                            |
| lat                  | Latitude in [deg]                                                                    |
| lon                  | Longitude in [deg]                                                                   |
| num_sat              | Number of satellites                                                                 |
| pdop                 | Position Dilution of Precision (PDOP)                                                |
| pitch                | Pitch in [deg]                                                                       |
| reliability_east     | East position external reliability in [m] #TODO: Is that correct?                    |
| reliability_height   | Height position external reliability in [m] #TODO: Is that correct?                  |
| reliability_north    | North position external reliability in [m] #TODO: Is that correct?                   |
| roll                 | Roll in [deg]                                                                        |
| sigma_east           | Standard deviation of East position in [m] #TODO: Is that correct?                   |
| sigma_height         | Standard deviation of Height position in [m] #TODO: Is that correct?                 |
| sigma_north          | Standard deviation of North position in [m] #TODO: Is that correct?                  |

and **meta**-data:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |


## midgard.parsers.terrapos_residual
A parser for reading Terrapos residual file

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='terrapos_residual', file_path='PPP-residuals.txt')
    data = p.as_dict()

**Description:**

Reads data from files in Terrapos residual format.



### **TerraposResidualParser**

Full name: `midgard.parsers.terrapos_residual.TerraposResidualParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading Terrapos residual file

Following **data** are available after reading Terrapos residual file:

| Parameter           | Description                                                                           |
|---------------------|---------------------------------------------------------------------------------------|
| azimuth             | Azimuth of satellites in [deg]                                                        |
| elevation           | Elevation of satellites in [deg]                                                      |
| gpsweek             | GPS week                                                                              |
| gpssec              | Seconds of GPS week                                                                   |
| residual_code       | Code (pseudorange) residuals in [m]                                                   |
| residual_doppler    | Doppler residuals in [m]                                                              |
| residual_phase      | Carrier-phase residuals in [m]                                                        |
| satellite           | Satellite PRN number together with GNSS identifier (e.g. G07)                         |
| system              | GNSS identifier                                                                       |

and **meta**-data:

| Key                  | Description                                                                          |
|----------------------|--------------------------------------------------------------------------------------|
| \__data_path__       | File path                                                                            |
| \__parser_name__     | Parser name                                                                          |



## midgard.parsers.ure_control_tool_csv
A parser for reading URE Control Tool CSV output files

**Example:**

    from midgard import parsers
    p = parsers.parse_file(parser_name='ure_control_tool_csv', file_path='G_GAL258_E1E5a_URE-AllPRN_190301.csv')
    data = p.as_dict()

**Description:**

Reads data from files in URE Control Tool CSV output format. The header information of the URE Control Tool CSV file is
not read (TODO).


### **UreControlToolCsvParser**

Full name: `midgard.parsers.ure_control_tool_csv.UreControlToolCsvParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading URE Control Tool CSV output files

The URE Control Tool CSV data header line is used to define the keys of the **data** dictionary. The values of the 
**data** dictionary are represented by the URE Control Tool CSV colum values.



## midgard.parsers.vlbi_source_names
A parser for reading IVS source names translation table


### **VlbiSourceNamesParser**

Full name: `midgard.parsers.vlbi_source_names.VlbiSourceNamesParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None) -> None`

A parser for reading IVS source names translation table

See https://vlbi.gsfc.nasa.gov/output for an example of a IVS source name file


## midgard.parsers.wip_rinex
A parser for reading Rinex files


### **rinex**()

Full name: `midgard.parsers.wip_rinex.rinex`

Signature: `(**parser_args: Any) -> midgard.parsers._parser_rinex.RinexParser`

Dispatch to correct subclass based on Rinex file type

## midgard.parsers.wip_rinex2_nav
A parser for reading RINEX navigation files with version 2.xx


### **Rinex2NavParser**

Full name: `midgard.parsers.wip_rinex2_nav.Rinex2NavParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading RINEX navigation files with version 2.xx



## midgard.parsers.wip_rinex2_nav_header
RINEX navigation header classes for file format version 2.xx


### **Rinex2NavHeaderMixin**

Full name: `midgard.parsers.wip_rinex2_nav_header.Rinex2NavHeaderMixin`

Signature: `()`

A mixin defining which RINEX navigation headers are mandatory and optional in RINEX version 2.xx

### **Rinex2NavHeaderParser**

Full name: `midgard.parsers.wip_rinex2_nav_header.Rinex2NavHeaderParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading just the RINEX version 2.xx navigation header

The data in the rinex file will not be parsed.


## midgard.parsers.wip_rinex2_obs
A parser for reading RINEX observation files with version 2.xx


### **Rinex2ObsParser**

Full name: `midgard.parsers.wip_rinex2_obs.Rinex2ObsParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading RINEX observation files with version 2.xx



## midgard.parsers.wip_rinex2_obs_header
RINEX observation header classes for file format version 3.xx


### **Rinex2ObsHeaderMixin**

Full name: `midgard.parsers.wip_rinex2_obs_header.Rinex2ObsHeaderMixin`

Signature: `()`

A mixin defining which RINEX observation headers are mandatory and optional in RINEX version 2.xx

### **Rinex2ObsHeaderParser**

Full name: `midgard.parsers.wip_rinex2_obs_header.Rinex2ObsHeaderParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading just the RINEX version 2.xx observation header

The data in the rinex file will not be parsed.


## midgard.parsers.wip_rinex3_clk
A parser for reading RINEX clock files with version 3.xx


### **Rinex3ClkParser**

Full name: `midgard.parsers.wip_rinex3_clk.Rinex3ClkParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading RINEX clock files with version 3.xx


## midgard.parsers.wip_rinex3_clk_header
RINEX clock header classes for file format version 3.xx


### **Rinex3ClkHeaderMixin**

Full name: `midgard.parsers.wip_rinex3_clk_header.Rinex3ClkHeaderMixin`

Signature: `()`

A mixin defining which RINEX clock headers are mandatory and optional in RINEX version 3.xx

### **Rinex3ClkHeaderParser**

Full name: `midgard.parsers.wip_rinex3_clk_header.Rinex3ClkHeaderParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading just the RINEX version 3.xx clock header

The data in the rinex file will not be parsed.


## midgard.parsers.wip_rinex3_nav
A parser for reading RINEX navigation files with version 3.xx


### **Rinex3NavParser**

Full name: `midgard.parsers.wip_rinex3_nav.Rinex3NavParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading RINEX navigation files with version 3.xx



## midgard.parsers.wip_rinex3_nav_header
RINEX navigation header classes for file format version 3.xx


### **Rinex3NavHeaderMixin**

Full name: `midgard.parsers.wip_rinex3_nav_header.Rinex3NavHeaderMixin`

Signature: `()`

A mixin defining which RINEX navigation headers are mandatory and optional in RINEX version 3.xx

### **Rinex3NavHeaderParser**

Full name: `midgard.parsers.wip_rinex3_nav_header.Rinex3NavHeaderParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading just the RINEX version 3.xx navigation header

The data in the rinex file will not be parsed.


## midgard.parsers.wip_rinex3_obs
A parser for reading RINEX observation files with version 3.xx


### **Rinex3ObsParser**

Full name: `midgard.parsers.wip_rinex3_obs.Rinex3ObsParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading RINEX observation files with version 3.xx



## midgard.parsers.wip_rinex3_obs_header
RINEX observation header classes for file format version 3.xx


### **Rinex3ObsHeaderMixin**

Full name: `midgard.parsers.wip_rinex3_obs_header.Rinex3ObsHeaderMixin`

Signature: `()`

A mixin defining which RINEX observation headers are mandatory and optional in RINEX version 3.xx

### **Rinex3ObsHeaderParser**

Full name: `midgard.parsers.wip_rinex3_obs_header.Rinex3ObsHeaderParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

A parser for reading just the RINEX version 3.xx observation header

The data in the rinex file will not be parsed.


## midgard.parsers.wip_rinex_clk
A parser for reading Rinex navigation files


### **RinexClkParser**

Full name: `midgard.parsers.wip_rinex_clk.RinexClkParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

Class for defining common methods for RINEX clock parsers.


### **rinex_clk**()

Full name: `midgard.parsers.wip_rinex_clk.rinex_clk`

Signature: `(**parser_args: Any) -> midgard.parsers._parser_rinex.RinexParser`

Dispatch to correct subclass based on version in Rinex file

## midgard.parsers.wip_rinex_nav
A parser for reading Rinex navigation files


### **RinexNavParser**

Full name: `midgard.parsers.wip_rinex_nav.RinexNavParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

Class for defining common methods for RINEX navigation parsers.


### **rinex_nav**()

Full name: `midgard.parsers.wip_rinex_nav.rinex_nav`

Signature: `(**parser_args: Any) -> midgard.parsers._parser_rinex.RinexParser`

Dispatch to correct subclass based on version in Rinex file

## midgard.parsers.wip_rinex_obs
A parser for reading Rinex observation files


### **RinexObsParser**

Full name: `midgard.parsers.wip_rinex_obs.RinexObsParser`

Signature: `(file_path: Union[str, pathlib.Path], encoding: Union[str, NoneType] = None, logger=<built-in function print>, sampling_rate: Union[int, NoneType] = None, strict: bool = False) -> None`

Class for defining common methods for RINEX observation parsers.


### **rinex_obs**()

Full name: `midgard.parsers.wip_rinex_obs.rinex_obs`

Signature: `(**parser_args: Any) -> midgard.parsers._parser_rinex.RinexParser`

Dispatch to correct subclass based on version in Rinex file