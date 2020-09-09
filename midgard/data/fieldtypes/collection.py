"""A Dataset collection field consisting of other fields

"""
# Standard library imports
from typing import List, Dict, Any

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import _h5utils
from midgard.data import fieldtypes
from midgard.data.fieldtypes._fieldtype import FieldType
from midgard.data.collection import Collection
from midgard.dev import exceptions
from midgard.dev import plugins


@plugins.register
class CollectionField(FieldType):

    _factory = staticmethod(Collection)

    def _post_init(self, val, **field_args):
        """Initialize field"""
        if field_args:
            raise exceptions.InitializationError(f"Unknown input parameter {','.join(field_args.keys())}")

        if isinstance(val, Collection):
            data = val
        else:
            data = self._factory()

        # Check that unit is not given
        if self._unit is not None:
            raise exceptions.InitializationError("Parameter 'unit' should not be specified for collections")

        # Store the data as a Collection
        self.data = data

    def unit(self, subfield):
        """Unit(s) of field"""
        if not subfield:
            raise exceptions.UnitError(f"Collections do not have units")
        else:
            return super().unit(subfield)

    def set_unit(self, subfield, new_unit):
        """Update unit of field"""
        if not subfield:
            raise exceptions.UnitError(f"Collections do not have units")
        else:
            super().set_unit(subfield, new_unit)

    @property
    def plot_fields(self):
        return [f"{self.name}.{f}" for f in self.data.plot_fields]

    def plot_values(self, field=None):
        if not field:
            # TODO: how to plot a collection?
            return np.full(len(self.data), np.nan)

        mainfield, _, subfield = field.partition(".")
        return self.data._fields[mainfield].plot_values(subfield)

    @property
    def fields(self):
        return self.data.fields

    @classmethod
    def read(cls, h5_group, memo):
        name = h5_group.attrs["fieldname"]
        field = cls(num_obs=None, name=name, val=None)  # num_obs and val not used
        fields = _h5utils.decode_h5attr(h5_group.attrs["fields"])
        for fieldname, fieldtype in fields.items():
            field.data._fields[fieldname] = fieldtypes.function(fieldtype).read(h5_group[fieldname], memo)

        return field

    @classmethod
    def _read(cls, h5_group, memo):
        """ Abstract field needs implementation, but is not used by collections"""
        pass

    def as_dict(self, fields=None) -> Dict[str, Any]:
        """Return a representation of the field as a dictionary"""
        field_dict = dict()

        for field in self.data._fields.values():
            field_dict.update(field.as_dict(fields))
        return field_dict

    def _prepend_empty(self, num_obs, memo):
        """Extend each field in the collection """
        for field in self.data._fields.values():
            field.prepend_empty(num_obs, memo)

    def _append_empty(self, num_obs, memo):
        """Extend each field in the collection """
        for field in self.data._fields.values():
            field.append_empty(num_obs, memo)

    def fill_memo(self, memo):
        for field_name, field in self.data._fields.items():
            memo[id(field.data)] = f"{self.name}.{field_name}"

    def write(self, h5_group, memo, write_level):
        """Write data to a HDF5 data source"""
        # Write each field in the collection
        h5_group.attrs["fieldname"] = self.name
        h5_group.attrs["__class__"] = f"{self.data.__class__.__module__}.{self.data.__class__.__name__}"
        for field_name, field in self.data._fields.items():
            if field.write_level >= write_level:
                h5_subgroup = h5_group.create_group(field_name)
                field.write(h5_subgroup, memo, write_level=write_level)

        fields = {fn: f.fieldtype for fn, f in self.data._fields.items() if f.write_level >= write_level}
        h5_group.attrs["fields"] = _h5utils.encode_h5attr(fields)

    def _write(self, h5_group, memo):
        """Abstract method needs implementation, but is not used by collections"""
        pass

    def _subset(self, idx: np.array, memo) -> None:
        """Remove observations from a field based on index"""
        for field in self.data._fields.values():
            field.subset(idx, memo)

    def _extend(self, other_field, memo) -> None:
        """Add observations from another field"""
        self.data._extend(other_field.data, memo)
