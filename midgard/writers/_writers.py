"""Basic functionality for writing files

Description:

This module contains functions for writing files.
"""
# Standard library imports
from datetime import datetime
from typing import List, Tuple, Union

# External library imports
import numpy as np

# Midgard imports
import midgard
from midgard.math.unit import Unit


def get_existing_fields(dset: "Dataset", writers_in: Tuple["WriterField", ...]) -> Tuple["WriterField", ...]:
    """Get existing writer fields, which are given in Dataset.

    Args:
        dset:         Dataset, a dataset containing the data.
        writers_in:   Writer fields.

    Returns:
        Existing writer fields
    """
    writers_out = []
    for writer in writers_in:
        if writer.field in dset.fields:
            exists = True
            field = dset[writer.field]
            for attr in writer.attrs:
                try:
                    field = getattr(field, attr)
                except AttributeError:
                    exists = False
                    break
            if exists:
                writers_out.append(writer)

    return writers_out


def get_field(dset: "Dataset", field: str, attrs: Tuple[str], unit: str) -> np.ndarray:
    """Get field values of a Dataset specified by the field attributes

    If necessary the unit of the data fields are corrected to the defined 'output' unit.

    Args:
        dset:     Dataset, a dataset containing the data.
        field:    Field name.
        attrs:    Field attributes (e.g. for Time object: (<scale>, <time format>)).
        unit:     Unit used for output.

    Returns:
        Array with Dataset field values
    """
    f = dset[field]
    for attr in attrs:
        f = getattr(f, attr)

    # Determine output 'unit'
    # +TODO: Does not work for all fields, because dset.unit() does not except 'time.gps.mjd'.
    if unit.startswith("deg"):
        field_attrs = field if len(attrs) == 0 else f"{field}.{'.'.join(attrs)}"
        f = f * getattr(Unit, f"{dset.unit(field_attrs)[0]}2{unit}")
    # -TODO

    return f


def get_header(
    fields: List[str],
    pgm_version: Union[None, str] = None,
    run_by: str = "",
    summary: Union[None, str] = None,
    add_description: Union[None, str] = None,
) -> List[str]:
    """Get header

    Args:
        fields:             List with fields to write.
        pgm_version:        Name and version (e.g. where 1.0.0) of program, which has created the output.
        run_by:             Information about who has created this file (e.g. NMA).
        summary:            Short description of output file
        add_description:    Additional description lines

    Returns:
        Header lines
    """

    # Generate header description
    midgard_version = f"midgard {midgard.__version__}"
    pgm = f"{pgm_version}/{midgard_version}" if pgm_version else midgard_version
    file_created = datetime.utcnow().strftime("%Y%m%d %H%M%S") + " UTC"
    description = f"PGM: {pgm:s}  RUN_BY: {run_by:s}  DATE: {file_created:s}\n"
    if summary:
        description += f"DESCRIPTION: {summary}\n\n"
    if add_description:
        description += add_description
    description = (
        description
        + """

HEADER       UNIT                  DESCRIPTION
______________________________________________________________________________________________________________________
"""
    )
    # TODO: 'description' should not exceed number of 120 characters. Newline should automatically introduced if
    #      f.description exceeds a certain number of characters.
    for f in fields:
        description = f"{description}{f.header:12s} {f.unit:22s} {f.description}\n"

    # Add data header lines to description
    header = [
        description,
        "".join(f"{f.header:>{f.width}s}" for f in fields),
        "".join(f"{f.unit:>{f.width}s}" for f in fields),
        "_" * sum([f.width for f in fields]),
    ]

    return header
