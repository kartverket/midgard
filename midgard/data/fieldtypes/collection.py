"""A Dataset collection field consisting of other fields

"""
# Standard library imports
import copy
from typing import List, Dict, Any

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
        self._default_field_suffix = None

    @property
    def fields(self):
        """Names of fields in the collection"""
        all_fields = list()
        for field in self._fields.values():
            all_fields.extend(field.subfields)

        return sorted(all_fields)

    @property
    def plot_fields(self):
        """Names of fields in the collection"""
        all_fields = list()
        for field in self._fields.values():
            all_fields.extend(field.plot_fields)

        return sorted(all_fields)

    @property
    def data(self):
        values = list()
        for field in self._fields.values():
            if field.data.ndim > 1:
                values.extend(np.asarray(field.data.T))
            else:
                values.append(np.asarray(field.data))
        if values:
            return np.stack(values, axis=1)
        else:
            return np.empty((0, 0))

    def unit(self, field):
        """Unit for values in a given field"""
        mainfield, _, subfield = field.partition(".")
        try:
            return self._fields[mainfield].unit(subfield)
        except KeyError:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    @property
    def sum(self):
        return np.sum(self.data, axis=1)

    # TODO other functions? mean, std, count??

    def for_each_fieldtype(self, fieldtype):
        for field in self._fields.values():
            module = field.__module__.split(".")[-1]
            if fieldtype == module:
                yield field.data

    @property
    def default_field_suffix(self):
        """Default field suffix

        """
        return self._default_field_suffix

    @default_field_suffix.setter
    def default_field_suffix(self, suffix):
        """Set the default field suffix"""
        if suffix is not None:
            suffix = str(suffix)
            if not suffix.startswith("_"):
                suffix = "_" + suffix
        else:
            suffix = None
        for collection in self.for_each_fieldtype("collection"):
            collection.default_field_suffix = suffix
        self._default_field_suffix = suffix

    def __getitem__(self, key):
        """Get a field from the collection using dict-notation"""
        field, _, attribute = key.partition(".")
        if attribute:
            return getattr(self[field], attribute)
        else:
            if self.default_field_suffix is not None:
                key_with_suffix = key + self.default_field_suffix
                if key_with_suffix in self._fields:
                    return self._fields[key_with_suffix].data
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
        """A string representing the collection"""
        return f"{type(self).__name__}(num_fields={len(self.fields)})"

    def __str__(self) -> str:
        """A string describing the dataset"""
        fields = console.fill(f"Fields: {', '.join(self.fields)}", hanging=8)
        return f"{self!r}\n{fields}"

    def __len__(self) -> int:
        return len(self.data)

    def __deepcopy__(self, memo):
        """Deep copy of collection"""
        new_collection = self.__class__()
        for fieldname, field in self._fields.items():
            new_collection._fields[fieldname] = copy.deepcopy(field, memo)
        return new_collection


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

    @property
    def _subfields(self):
        return self.data.fields

    @property
    def plot_fields(self):
        return [f"{self.name}.{f}" for f in self.data.plot_fields]

    def plot_values(self, field=None):
        if not field:
            return self.data.sum

        mainfield, _, subfield = field.partition(".")
        return self.data._fields[mainfield].plot_values(subfield)

    @property
    def fields(self):
        return self._subfields

    @classmethod
    def read(cls, h5_group, memo):
        name = h5_group.attrs["fieldname"]
        field = cls(num_obs=None, name=name, val=None)  # num_obs and val not used
        fields = _h5utils.decode_h5attr(h5_group.attrs["fields"])
        for fieldname, fieldtype in fields.items():
            field.data[fieldname] = fieldtypes.function(fieldtype).read(h5_group[fieldname], memo)

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
        """Extend each field in collection """
        for field in self.data._fields.values():
            field.prepend_empty(num_obs, memo)

    def _append_empty(self, num_obs, memo):
        """Extend each field in collection """
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
            field._subset(idx, memo)

    def _extend(self, other_field, memo) -> None:
        """Add observations from another field"""
        for field_name, field in other_field.data._fields.items():
            self.data._fields[field_name].extend(field, memo)
