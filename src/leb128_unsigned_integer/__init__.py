"""Leb128 Unsigned Integer: read and write unsigned LEB128 integers."""

from .core import (
    read_leb128,
    write_leb128,
)

__all__ = [
    "read_leb128",
    "write_leb128",
]
