"""Simple utilities used by Dataset when dealing with HDF5 files

"""

# Standard library imports
from typing import Dict, List, Sequence, Tuple


def sequence2h5attr(lst: Sequence[str]) -> str:
    """Convert a list to a string that can be stored as an HDF5 attribute"""
    return ",".join(str(s) for s in lst)


def h5attr2list(attr: str) -> List[str]:
    """Convert an HDF5 attribute to a list of strings"""
    return attr.split(",")


def h5attr2tuple(attr: str) -> Tuple[str, ...]:
    """Convert an HDF5 attribute to a list of strings"""
    return tuple(attr.split(","))


def dict2h5attr(dct: Dict[str, str]) -> str:
    """Convert a dictionary to a string that can be stored as an HDF5 attribute"""
    return ",".join(f"{k}:{v}" for k, v in dct.items())


def h5attr2dict(attr: str) -> List[str]:
    """Convert an HDF5 attribute to a dictionary of strings"""
    return dict(a.partition(":")[::2] for a in attr.split(","))
