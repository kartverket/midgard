"""A Dataset collection field consisting of other fields

"""
# Standard library imports
from typing import List

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import _h5utils
from midgard.data import fieldtypes
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.dev import console
from midgard.dev import exceptions
from midgard.dev import plugins


class Collection:
    def __init__(self):
        self._fields = dict()

    @property
    def fields(self):
        """Names of fields in the collection"""
        all_fields = list()
        for field in self._fields.values():
            all_fields.extend(field.subfields)

        return sorted(all_fields)

    @property
    def data(self):
        values = [self[f] for f in self.fields]
        if values:
            return np.stack(values, axis=1).reshape(len(values[0]), -1)
        else:
            return np.empty((0, 0))

    def unit(self, field):
        """Unit for values in a given field"""
        mainfield, _, subfield = field.partition(".")
        try:
            return self._fields[mainfield].unit(subfield)
        except KeyError:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    def __getitem__(self, key):
        """Get a field from the collection using dict-notation"""
        field, _, attribute = key.partition(".")
        if attribute:
            return getattr(self[field], attribute)
        else:
            return self._fields[key].data

    def __setitem__(self, key, value):
        """Add a field to the collection"""
        self._fields[key] = value

    def __getattr__(self, key):
        """Get a field from the collection using dot-notation"""
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}") from None

    def __dir__(self):
        """List all fields and attributes on the collection"""
        return super().__dir__() + self.fields

    def _ipython_key_completions_(self) -> List[str]:
        """Tab completion for dict-style lookups in ipython

        See http://ipython.readthedocs.io/en/stable/config/integrating.html

        Returns:
            Fieldnames in the dataset.
        """
        return self.fields

    def __repr__(self) -> str:
        """A string representing the collection

        """
        return f"{type(self).__name__}(num_fields={len(self.fields)})"

    def __str__(self) -> str:
        """A string describing the dataset

        """
        fields = console.fill(f"Fields: {', '.join(self.fields)}", hanging=8)
        return f"{self!r}\n{fields}"


@plugins.register
class CollectionField(FieldType):

    _factory = staticmethod(Collection)

    def _post_init(self, val, **field_args):
        """Initialize field"""
        self.data = self._factory()

        # Check that unit is not given
        if self._unit is not None:
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for collections")

    @property
    def _subfields(self):
        return self.data.fields

    @classmethod
    def read(cls, h5_group, memo):
        name = h5_group.attrs["fieldname"]
        field = cls(num_obs=None, name=name, val=None)  # num_obs and val not used
        fields = _h5utils.h5attr2dict(h5_group.attrs["fields"])
        for fieldname, fieldtype in fields.items():
            field.data[fieldname] = fieldtypes.function(fieldtype).read(h5_group[fieldname])

        return field

    @classmethod
    def _read(cls, h5_group, memo):
        """ Abstract field needs implementation, but is not used by collections"""
        pass

    def write(self, h5_group, memo, write_level):
        """Write data to a HDF5 data source"""
        # Write each field in the collection
        h5_group.attrs["fieldname"] = self.name
        for field_name, field in self.data._fields.items():
            h5_subgroup = h5_group.create_group(field_name)
            field.write(h5_subgroup, write_level=write_level)

        fields = {fn: f.fieldtype for fn, f in self.data._fields.items()}
        h5_group.attrs["fields"] = _h5utils.dict2h5attr(fields)

    def _write(self, h5_group, memo):
        """Abstract method needs implementation, but is not used by collections"""
        pass
