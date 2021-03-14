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

Signature: `(dset: 'Dataset', field: str, attrs: Tuple[str], unit: str) -> numpy.ndarray`

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

Signature: `(fields: List[str], pgm_version: Union[NoneType, str] = None, run_by: str = '', summary: Union[NoneType, str] = None, add_description: Union[NoneType, str] = None, lsign: str = '') -> str`

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
