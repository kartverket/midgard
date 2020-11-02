""" A collection of fields 

Also serves as base class for dataset
"""

# Standard library imports
import copy
from typing import List, Dict, Any

# Third party imports
import numpy as np

# Midgard imports
from midgard.data import fieldtypes
from midgard.dev import console
from midgard.dev import exceptions
from midgard.math.unit import Unit


class Collection:

    type = "collection"

    def __init__(self):
        self._fields = dict()
        self._default_field_suffix = None

    @property
    def fields(self):
        """Names of fields and nested fields in the collection"""
        all_fields = list()
        for fieldname, field in self._fields.items():
            all_fields.append(fieldname)
            try:
                all_fields.extend([f"{fieldname}.{f}" for f in field.fields])
            except AttributeError:
                pass

        return sorted(all_fields)

    def fieldnames(self):
        """Names of fields, nested fields and field attributes in the collection"""
        all_fields = list()
        for field in self._fields.values():
            all_fields.extend(field.subfields)

        return sorted(all_fields)

    def field(self, fieldname: str) -> "FieldType":
        """Return the field matching the given fieldname"""
        mainfield, _, subfield = fieldname.partition(".")
        try:
            field = self._fields[mainfield]
        except KeyError:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None
        if subfield:
            field_data = field.data
            try:
                # Recursive call for collections
                field = field_data.field(subfield)
            except AttributeError:
                # field_data does not have a function field
                # Only collections should have this function
                pass
        return field

    @property
    def plot_fields(self):
        """Names of fields in the collection"""
        all_fields = list()
        for fieldname, field in self._fields.items():
            if fieldname.endswith("_"):
                # Fields ending with trailing underscore should not be plotted
                continue
            all_fields.extend(field.plot_fields)

        return sorted(all_fields)

    def unit(self, field):
        """Unit for values in a given field"""
        mainfield, _, subfield = field.partition(".")
        try:
            return self._fields[mainfield].unit(subfield)
        except KeyError:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    def unit_short(self, field):
        units = self.unit(field)
        if units is None:
            return tuple()
        return tuple([Unit.symbol(u) for u in units])

    def set_unit(self, field, new_unit):
        """Update the unit of a given field"""
        mainfield, _, subfield = field.partition(".")
        try:
            return self._fields[mainfield].set_unit(subfield, new_unit)
        except KeyError:
            raise exceptions.FieldDoesNotExistError(f"Field {mainfield!r} does not exist") from None

    def for_each_fieldtype(self, fieldtype):
        for field in self._fields.values():
            module = field.__module__.split(".")[-1]
            if fieldtype == module:
                yield field.data

    def for_each_suffix(self, key):
        """Do something for each suffix"""
        *collections, key = key.split(".")
        container = self
        for c in collections:
            container = container._fields[c].data
        previous_field_suffix = self.default_field_suffix
        sm = [(f[len(key) :], container._fields[f].multiplier) for f in container._fields if f.startswith(key)]
        for suffix, multiplier in sm:
            if suffix and not suffix[1:].isdigit():
                continue
            self.default_field_suffix = suffix
            yield multiplier

        self.default_field_suffix = previous_field_suffix

    @property
    def default_field_suffix(self):
        """Default field suffix"""
        if self._default_field_suffix is None:
            return ""
        return self._default_field_suffix

    @default_field_suffix.setter
    def default_field_suffix(self, suffix):
        """Set the default field suffix"""
        if suffix:
            suffix = str(suffix)
            if not suffix.startswith("_"):
                suffix = "_" + suffix
        else:
            suffix = None
        for collection in self.for_each_fieldtype("collection"):
            collection.default_field_suffix = suffix
        self._default_field_suffix = suffix

    def _difference(self, other, num_obs, self_idx, other_idx, copy_self_on_error=False, copy_other_on_error=False):
        """Perform the - operation for each field in self and other"""
        result = self.__class__()
        for fieldname, field in self._fields.items():
            if fieldname in other._fields:
                try:
                    factors = [Unit(_from, _to) for _to, _from in zip(field._unit, other._fields[fieldname]._unit)]
                except TypeError:
                    factors = None
                except exceptions.UnitError as err:
                    raise ValueError(f"Cannot compute difference for field `{fieldname}`: {err}")
                try:
                    if factors:
                        difference = self[fieldname][self_idx] - other[fieldname][other_idx] * np.array(factors)
                    else:
                        difference = self[fieldname][self_idx] - other[fieldname][other_idx]
                    fieldtype = fieldtypes.fieldtype(difference)
                    func = fieldtypes.function(fieldtype)
                    field = func(
                        num_obs=num_obs,
                        name=fieldname,
                        val=difference,
                        unit=field._unit,
                        write_level=field._write_level.name,
                    )
                    result.add_field(fieldname, field)
                except IndexError as err:
                    # fieldname is a collection
                    collection = self[fieldname]._difference(
                        other[fieldname],
                        num_obs,
                        self_idx,
                        other_idx,
                        copy_self_on_error=copy_self_on_error,
                        copy_other_on_error=copy_other_on_error,
                    )
                    fieldtype = fieldtypes.fieldtype(collection)
                    func = fieldtypes.function(fieldtype)
                    field = func(
                        num_obs=num_obs,
                        name=fieldname,
                        val=collection,
                        unit=field._unit,
                        write_level=field._write_level.name,
                    )
                    result.add_field(fieldname, field)
                except TypeError as err:
                    # Fields that do not support the - operator
                    if copy_self_on_error:
                        index_data = self[fieldname][self_idx]
                        fieldtype = fieldtypes.fieldtype(index_data)
                        func = fieldtypes.function(fieldtype)
                        self_fieldname = f"{fieldname}_self"
                        field = func(
                            num_obs=num_obs,
                            name=self_fieldname,
                            val=index_data,
                            unit=field._unit,
                            write_level=field._write_level.name,
                        )
                        result.add_field(self_fieldname, field)
                    if copy_other_on_error:
                        index_data = other[fieldname][other_idx]
                        fieldtype = fieldtypes.fieldtype(index_data)
                        func = fieldtypes.function(fieldtype)
                        other_fieldname = f"{fieldname}_other"
                        field = func(
                            num_obs=num_obs,
                            name=other_fieldname,
                            val=index_data,
                            unit=other._fields[fieldname]._unit,
                            write_level=other._fields[fieldname]._write_level.name,
                        )
                        result.add_field(other_fieldname, field)

        return result

    def _extend(self, other, memo):
        """Extend fields in self with data from other"""
        only_in_other = set(other._fields.keys()) - set(self._fields.keys())
        only_in_self = set(self._fields.keys()) - set(other._fields.keys())

        if len(self) == 0:
            only_in_other = only_in_other | set(self._fields.keys())

        if len(other) == 0:
            only_in_self = only_in_self | set(other._fields.keys())

        for field_name, field in other._fields.items():

            if field_name in only_in_other:
                new_field = field.copy()
                new_field.prepend_empty(len(self), memo)
                self._fields[field_name] = new_field
            else:
                self._fields[field_name].extend(other._fields[field_name], memo)

        for field_name in only_in_self:
            self._fields[field_name].append_empty(len(other), memo)

    def add_field(self, fieldname: str, field: "FieldType") -> None:
        """Update the _fields dictionary with a field"""
        self._fields[fieldname] = field

    def __bool__(self) -> bool:
        """Dataset is truthy if it has fields with observations"""
        return len(self) > 0 and len(self._fields) > 0

    def __getitem__(self, key):
        """Get a field from the dataset using dict-notation"""
        try:
            mainfield, _, subfield = key.partition(".")
        except (TypeError, AttributeError):
            raise IndexError(f"Class {self.__class__.__name__} does not support slicing")

        if not subfield:
            return getattr(self, key)
        else:
            return getattr(getattr(self, mainfield), subfield)

    def __getattr__(self, key):
        """Get a field from the dataset using dot-notation"""
        if key == "_fields" or key.endswith("default_field_suffix"):
            return self.__getattribute__(key)

        container = self
        field = key
        if "." in key:
            collection, _, field = key.partition(".")
            container = self[collection]

        # If field exists
        if field in container._fields:
            if "." in field:
                return getattr(container, field)
            else:
                return container._fields[field].data

        # Field did not exist. Try default_field_suffix if set
        if container._default_field_suffix is not None:
            field = field + container.default_field_suffix
            if field in container._fields:
                if "." in field:
                    return getattr(container, field)
                else:
                    return container._fields[field].data

        else:
            # Raise error for unknown attributes
            raise AttributeError(f"{type(self).__name__!r} has no attribute {key!r}")

    def __delitem__(self, key):
        """Delete a field from the dataset"""
        try:
            mainfield, _, subfield = key.partition(".")
        except (TypeError, AttributeError):
            raise IndexError(
                f"Class {self.__class__.__name__} does not support deletion of slices. Use subset instead."
            )

        if not subfield:
            delattr(self, key)
        else:
            delattr(getattr(self, mainfield), subfield)

    def __delattr__(self, key):
        """Delete a field from the dataset"""
        if self._default_field_suffix is not None:
            key_with_suffix = key + self.default_field_suffix
            if key_with_suffix in self._fields:
                del self._fields[key_with_suffix]
                return
        if key in self._fields:
            del self._fields[key]
            return
        super().__delattr__(key)

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

    def __setattr__(self, key, value):
        """Protect fields from being accidentally overwritten"""
        if key != "_fields" and key in self._fields:
            if id(value) != id(self._fields[key].data):
                raise AttributeError(
                    f"Can't set attribute '{key}' on '{type(self).__name__}' object, use slicing instead"
                )
        super().__setattr__(key, value)

    def __str__(self) -> str:
        """A string describing the dataset"""
        fields = console.fill(f"Fields: {', '.join(self.fields)}", hanging=8)
        return f"{self!r}\n{fields}"

    def __len__(self) -> int:
        """The length of a collection is the number of rows in the fields"""
        if not self._fields:
            return 0
        first_field = list(self._fields.keys())[0]
        # All fields should have same length. Use length of first field in collection as length
        return len(self._fields[first_field].data)

    def __deepcopy__(self, memo):
        """Deep copy of collection"""
        new_collection = self.__class__()
        for fieldname, field in self._fields.items():
            new_collection._fields[fieldname] = copy.deepcopy(field, memo)
        return new_collection
