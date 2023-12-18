"""Write dataset fields in CSV file format
"""

# Standard library import
from pathlib import Path, PosixPath
from typing import OrderedDict, List, Union

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import log
from midgard.writers._writers import get_field

# CSV file example:
#
#
# date,mjd,gpsweek,gpssec,satellite,frequency,amplitude,peak2noise,reflection_height,reflection_height_referenced,...
# 2023-01-01 00:08:24,59945.006042,2243,522.000,R08,L2,21.44,3.04,5.64,44.10,1.01,44.05
# 2023-01-01 00:51:00,59945.035625,2243,3078.000,E04,E5a,29.98,3.23,5.74,43.99,1.02,44.06
# 2023-01-01 01:57:36,59945.081875,2243,7074.000,G08,L5,51.78,3.68,5.62,44.11,1.00,44.04
# 2023-01-01 03:41:24,59945.153958,2243,13302.000,E12,E1,16.12,3.17,5.67,44.06,1.18,44.22
# ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+-

def csv_(
        dset: "Dataset",
        file_path: Union[str, PosixPath],
        fields: OrderedDict[str, str],
) -> None:
    """Write dataset fields in CSV file format


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

    Args:
        dset:       A dataset containing the data.
        file_path:  File path of CSV file.
        fields:     Dictionary with field name as key and format specifiers as values
    """
    file_path = Path(file_path)

    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=False)
         
    # Get data types needed to define numpy array
    field_types = list()
    for field, format_ in fields.items():
        if "s" in format_:
            field_types.append(object)
        elif "d" in format_:
            field_types.append(int)
        elif "f" in format_:
            field_types.append(float)
        else:
            field_types.append(object)
            fields[field] = "s"
            log.debug(f"CSV field format '{format_}' is not defined and is set to 's'.")

        fields[field] = f"%{fields[field]}"

    # Add date field to dataset
    if "date" not in dset.fields:
        dset.add_text("date", val=[d.strftime("%Y-%m-%d %H:%M:%S") for d in dset.time.datetime])

    # Generate output_list with tuples, which include field values for each row
    output_list = list()
    for field in fields.keys():
        words = field.split(".")
        name = words[0]
        if len(field) > 1:
            words.pop(0)
            attrs = tuple(words)
        else:
            attrs = ()
        output_list.append(get_field(dset, name, attrs))
    output_list = list(zip(*(output_list)))

    # List epochs ordered by dates
    idx = np.concatenate([np.where(dset.filter(date=d))[0] for d in sorted(dset.unique("date"))])
           
    # Put together fields in an array as specified by the 'dtype' tuple list    
    output_array = np.array(output_list, dtype=[(field, type_) for field, type_ in zip(fields, field_types)])[idx]

    # Write to disk
    np.savetxt(
        file_path,
        output_array,
        fmt=tuple(format_ for format_ in fields.values()),
        header=_get_csv_header(fields.keys()),
        comments="",
        delimiter=",",
        encoding="utf8",
    )


def _get_csv_header(fields: List[str]) -> str:
    """Get CSV file header

    Args:
        fields:  Field names

    Returns:
        Line with header names separated by comma
    """
    fields_def = {
        "time.decimalyear": "decimalyear",
        "time.gps.decimalyear": "decimalyear",
        "time.utc.decimalyear": "decimalyear",
        "time.mjd": "mjd",
        "time.gps.mjd": "mjd",
        "time.utc.mjd": "mjd",
        "time.gps.gps_ws.week": "gpsweek",
        "time.gps.gps_ws.seconds": "gpssec",
    }

    # Get header names
    header_names = list()
    for field in fields:
        header_names.append(fields_def[field] if field in fields_def else field)

    return f"{','.join(header_names)}"




	





