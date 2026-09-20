"""A parser for reading GEMOP KPI CSV files

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gemop_kpi_csv', file_path='WPG3.1-NMA_2026Q1.csv')
    data = p.as_dict()

Description:
------------

Reads data from files in GEMOP KPI CSV format. 
"""

# Standard library import
from datetime import datetime
from typing import Union

# Third party import
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.parsers.csv_ import CsvParser
from midgard.dev import plugins


@plugins.register
class GemopKpiCsvParser(CsvParser):
    """A parser for reading GEMOP KPI CSV files

    Following dataset fields are available:

    | Field                      | Type          | Description                                                       |
    | :------------------------- | :------------ | :---------------------------------------------------------------- |
    | agency                     | numpy.ndarray | Agency name                                                       |
    | batch                      | numpy.ndarray | Satellite batch (e.g. IIA, G1 IOV)                                |
    | constellation              | numpy.ndarray | Constellation name (e.g. GPS, Galileo)                            |
    | dissemination_mean         | numpy.ndarray | Dissemination mean of the data (e.g. IDD, SIS, Terrestrial)       |
    | navigation_message         | numpy.ndarray | Navigation message type (e.g. I/NAV, LNAV)                        |
    | performance_indicator_code | numpy.ndarray | Performance indicator code (e.g. GNSS-OS-KPI-04)                  |
    | performance_indicator_name | numpy.ndarray | Performance indicator description                                 |
    | svid (former satellite)    | numpy.ndarray | Space vehicle identifier (e.g. GSAT0201). Former 'satellite'      | 
    |                            |               | column of KPI CSV format.                                         |
    | result                     | numpy.ndarray | KPI results                                                       |
    | satellite (former prn)     | numpy.ndarray | Satellite PRN number together with GNSS identifier (e.g. G07).    |
    |                            |               | Former 'prn' column of KPI CSV format.                            |
    | signal                     | numpy.ndarray | GNSS signals used in analysis (e.g. E1, E1/E5a)                   |
    | signal_combination         | numpy.ndarray | Single combination (e.g. Single, Dual, Multiple)                  |
    | slot                       | numpy.ndarray | Nominal and auxiliary slots of satellites (e.g. B04, A15)         |
    | station                    | numpy.ndarray | Station name list (9-alphanumeric characters, e.g. KOUG00GUF).    |
    |                            |               | Former 'station_identifier' column of KPI CSV format.             |
    | system                     | numpy.ndarray | GNSS identifier                                                   |
    | target                     | numpy.ndarray | KPI target or minimum performance level or typical performance    |
    |                            |               | level                                                             |
    | time                       | Time          | Observation time given as Time object                             |
    | unit                       | numpy.ndarray | KPI unit                                                          |

    """
    
    def __init__(
            self,
            file_path: Union[str, pathlib.Path],
            encoding: Optional[str] = None,
            dropnan: bool = False,
            keep_default_na: bool = False,
            
    ) -> None:
        """Set up the basic information needed by the parser

        Add a self._sinex dictionary for the raw Sinex data and read which
        blocks to read from self.setup_parser().

        Args:
            file_path:          Path to file that will be read.
            encoding:           Encoding of file that will be read.
            dropnan:            Drop 'NaN' columns.
            keep_default_na:    Convert empty entries into 'NaN'.
        """
        super().__init__(file_path, encoding=encoding)
        self._dropnan = dropnan
        self._keep_default_na = keep_default_na
        

    def as_dataset(self, agency: Union[str, None] = None) -> "Dataset":
        """Return the parsed data as a Dataset
        
        Args:
            agency: Agency name. If given than agengy field is added.

        Returns:
            A dataset containing the data.
        """
        
        # Keys of dictionary in lowercase and empty space as underscore
        data = { k.lower().replace(" ","_"): v for k, v in self.data.items() }
        
        # Rename keys to adapt it to Midgard naming convention
        data["svid"] = data.pop("satellite")
        data["satellite"] = data.pop("prn")
        data["station"] = data.pop("station_identifier")
        data["unit_"] = data.pop("unit")  # Needed otherwise 'unit' field name comes in conflict with 'unit()' function
        
        # Initialize dataset
        dset = dataset.Dataset()
        if not data:
            log.warn("No data in {self.file_path}.")
            return dset
        dset.num_obs = len(data["constellation"])

        # Add time
        dset.add_time(
            name="time",
            val=[datetime.strptime(v, "%Y-%b") for v in data["date"]],
            scale="utc",
            fmt="datetime",
            write_level="operational",
        )
        
        # Define fields to save in dataset
        remove_time_fields = {"Date"}
        fields = set(data.keys()) - remove_time_fields

        # Add text and float fields
        for field in fields:

            if data[field].dtype.kind in {"U", "S"}:  # Check if numpy type is string
                data[field][data[field] == "nan"] = "" # Convert 'nan' values to empty string
                dset.add_text(field.lower(), val=data[field], write_level="operational")
                continue
           
            dset.add_float(field.lower(), val=data[field])
            
        # Add system field
        system = list()
        for sat in data["satellite"]:
            if sat == "":
                system.append("")
            else:
                system.append(sat[0:1])
                
        dset.add_text("system", system)
        
        # Add agency field, if given as argument
        if agency:
            dset.add_text("agency", val=np.repeat(agency.lower(), dset.num_obs))

        return dset
