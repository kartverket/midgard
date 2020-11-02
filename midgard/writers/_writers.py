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
from midgard.dev import exceptions
from midgard.dev import log
from midgard.math.unit import Unit

# TODO: This function should be replaced by get_existing_fields_by_attrs!!!
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


def get_existing_fields_by_attrs(dset: "Dataset", writers_in: Tuple["WriterField", ...]) -> Tuple["WriterField", ...]:
    """Get existing writer fields, which are given in Dataset.

    Args:
        dset:         Dataset, a dataset containing the data.
        writers_in:   Fields to write/plot.

    Returns:
        Existing writer fields
    """
    writers_out = []
    for writer in writers_in:
        exists = True
        field = dset
        for attr in writer.attrs:
            try:
                field = getattr(field, attr)
            except AttributeError:
                exists = False
                break
        if exists:
            writers_out.append(writer)

    return writers_out


# TODO: This function should be replaced by get_field_by_attrs!!!
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
        
    # Convert 'unit' if necessary
    if unit:
        field_attrs = field if len(attrs) == 0 else f"{field}.{'.'.join(attrs)}"
        
        try:
            field_unit = dset.unit(field_attrs)[0]
        except (exceptions.UnitError, TypeError) as e:
            log.debug(f"Skip unit conversion for field '{field_attrs}'.")
            return f # Skip unit conversion for text fields, which do not have a unit.
        
        try:
            log.debug(f"Convert dataset field {field} from unit {field_unit} to {unit}.")
            f = f * Unit(field_unit).to(unit).m
        except (exceptions.UnitError):
            log.warn(f"Cannot convert from '{field_unit}' to '{unit}' for field {field}.")

    return f


def get_field_by_attrs(dset: "Dataset", attrs: Tuple[str], unit: str) -> np.ndarray:
    """Get field values of a Dataset specified by the field attributes

    If necessary the unit of the data fields are corrected to the defined 'output' unit.

    Args:
        dset:     Dataset, a dataset containing the data.
        attrs:    Field attributes (e.g. for Time object: (<scale>, <time format>)).
        unit:     Unit used for output.

    Returns:
        Array with Dataset field values
    """
    f = dset
    for attr in attrs:
        f = getattr(f, attr)

    # Convert 'unit' if necessary
    if unit:
        field = f"{'.'.join(attrs)}"
        if dset.unit(field):
            field_unit = dset.unit(field)[0]
            try:
                log.debug(f"Convert dataset field {field} from unit {field_unit} to {unit}.")
                f = f * Unit(field_unit).to(unit).m
            except exceptions.UnitError:
                log.warn(f"Cannot convert from '{field_unit}' to '{unit}'.")

    return f


def get_header(
    fields: List[str],
    pgm_version: Union[None, str] = None,
    run_by: str = "",
    summary: Union[None, str] = None,
    add_description: Union[None, str] = None,
    lsign: str = "",
) -> List[str]:
    """Get header

    Args:
        fields:             List with fields to write.
        pgm_version:        Name and version (e.g. where 1.0.0) of program, which has created the output.
        run_by:             Information about who has created this file (e.g. NMA).
        summary:            Short description of output file
        add_description:    Additional description lines
        lsign:              Leading comment sign

    Returns:
        Header lines
    """

    # Generate header description
    midgard_version = f"midgard {midgard.__version__}"
    pgm = f"{pgm_version}/{midgard_version}" if pgm_version else midgard_version
    file_created = datetime.utcnow().strftime("%Y%m%d %H%M%S") + " UTC"
    description = f"{lsign}PGM: {pgm:s}  RUN_BY: {run_by:s}  DATE: {file_created:s}\n"
    if summary:
        description += f"{lsign}DESCRIPTION: {summary}\n{lsign}\n"
    if add_description:
        description += f"{lsign}" + add_description
    description = (
        description
        + f"\n{lsign}\n{lsign}HEADER         UNIT                   DESCRIPTION\n"
        f"{lsign}" + "_" * 117 + "\n"
    )
    # TODO: 'description' should not exceed number of 120 characters. Newline should automatically introduced if
    #      f.description exceeds a certain number of characters.
    for f in fields:
        description += f"{lsign}{f.header:14s} {f.unit:22s} {f.description}\n"

    # Add data header lines to description
    header = [
        description + f"{lsign}\n",
        f"{lsign}" + "".join(f"{f.header:>{f.width}s}" for f in fields) + "\n",
        f"{lsign}" + "".join(f"{f.unit:>{f.width}s}" for f in fields) + "\n",
        f"{lsign}" + "_" * sum([f.width for f in fields]) + "\n",
    ]

    return "".join(header)
