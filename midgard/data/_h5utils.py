"""Simple utilities used by Dataset when dealing with HDF5 files

"""

# Standard library imports
import ast
import copy
import re
from typing import Any, Dict, List, Tuple, Set

# Third party imports
import numpy as np

def encode_h5attr(data: Any) -> Any:
    """Convert a basic data type to something that can be saved as a hdf5 attribute

    Will raise a TypeError if the attribute cannot be saved in a way that allows
    reading and correct interpretation of the attribute.
    """
    data_type = type(data).__name__
    error_msg = f"Cannot save attribute to file. Data too complex: {type(data)} {data}. Data can only consist of strings, lists, dicts, tuples, sets or numbers"

    try:
        encoded_data = globals()[f"_{data_type}2h5attr"](data)
    except KeyError:
        encoded_data = data
        # Check if data is considered an dtype('O') by numpy
        # In which case it is not supported by h5py
        np_array = np.asarray(data)
        if np_array.dtype == "O":
            # Objects is too complex
            raise TypeError(error_msg)

    try:
        # Verify that decoding works
        decode_h5attr(copy.deepcopy(encoded_data))
    except ValueError:
        raise TypeError(error_msg)

    return encoded_data


def decode_h5attr(attr: Any) -> Any:
    """Convert hdf5 attribute back to its original datatype"""
    try:
        attr_type, _, attr = attr.partition(" ")
        if "nan" in attr or "inf" in attr:
            # ast.literal_eval does not understand that nan and inf are floats. convert these to strings
            attr = re.sub(r"\bnan\b", "'nan'", attr)
            attr = re.sub(r"\binf\b", "'inf'", attr)
            attr = re.sub(r"-'\binf\b'", "'-inf'", attr)
        result = globals()[f"_h5attr2{attr_type}"](attr)
        return _recursive_replace(result)
    except (AttributeError, KeyError):
        return attr


def _list2h5attr(data: List[str]) -> str:
    """Convert a list to a string that can be stored as an HDF5 attribute"""
    return f"list {str(data)}"


def _tuple2h5attr(data: Tuple[str]) -> str:
    """Convert a list to a string that can be stored as an HDF5 attribute"""
    return f"tuple {str(data)}"


def _set2h5attr(data: Set[str]) -> str:
    """Convert a list to a string that can be stored as an HDF5 attribute"""
    return f"set {str(data)}"


def _dict2h5attr(data: Dict[str, str]) -> str:
    """Convert a dictionary to a string that can be stored as an HDF5 attribute"""
    return f"dict {str(data)}"


def _str2h5attr(data: str) -> str:
    """Add a str prefix to distinguish an actual string from the other types saved as strings"""
    return f"str {data}"


_str_2h5attr = _str2h5attr


def _h5attr2list(attr: str) -> List[str]:
    """Convert an HDF5 attribute to a list of strings"""
    if not attr or attr == "list()":
        return list()
    return ast.literal_eval(attr)


def _h5attr2tuple(attr: str) -> Tuple[str, ...]:
    """Convert an HDF5 attribute to a list of strings"""
    if not attr or attr == "tuple()":
        return tuple()
    return ast.literal_eval(attr)


def _h5attr2set(attr: str) -> Set[str]:
    """Convert an HDF5 attribute to a list of strings"""
    if not attr or attr == "set()":
        return set()
    return ast.literal_eval(attr)


def _h5attr2dict(attr: str) -> List[str]:
    """Convert an HDF5 attribute to a dictionary of strings"""
    if not attr or attr == "dict()":
        return dict()
    return ast.literal_eval(attr)


def _h5attr2str(attr: str) -> str:
    """Simply return the string"""
    return attr


def _recursive_replace(data):
    """Searches data structure and replaces 'nan' and 'inf' with respective float values"""
    if isinstance(data, str):
        if data == "nan":
            return float("nan")
        if data == "inf":
            return float("inf")
        if data == "-inf":
            return -float("inf")
    if isinstance(data, List):
        return [_recursive_replace(v) for v in data]
    if isinstance(data, Tuple):
        return tuple([_recursive_replace(v) for v in data])
    if isinstance(data, Set):
        return set([_recursive_replace(v) for v in data])
    if isinstance(data, Dict):
        return {k: _recursive_replace(v) for k, v in data.items()}
    return data

