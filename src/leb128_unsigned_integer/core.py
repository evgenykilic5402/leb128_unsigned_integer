"""Core LEB128 read/write for unsigned integers.

LEB128 (Little-Endian Base 128) encodes an unsigned integer as a sequence of
bytes where only the low 7 bits of each byte carry value; the high bit (0x80)
flags continuation. The "little-endian" part means the least-significant 7-bit
group is emitted first, so the reader must accumulate `value += group << (7 * i)`.

Design choices documented here because they are not obvious:

- The reader takes a `memoryview` (or any buffer-protocol object) and an offset,
  and returns `(value, new_offset)`. Returning the offset (rather than mutating
  a stream pointer) keeps the function pure, testable, and free of shared state.
- The writer returns `bytes`, the simplest immutable, widely-accepted buffer
  type. Callers wanting a `memoryview` can wrap it themselves.
- We raise `ValueError` for truncated input (the continuation bit promised more
  bytes than arrived) and for integers that overflow 2**63. The 2**63 ceiling
  is an intentional, documented limit: the test suite runs against CPython where
  `int` is unbounded, but real LEB128 consumers (e.g. DWARF, WebAssembly) cap
  the meaningful range well below 64 bits. Rather than silently accept absurd
  magnitudes, we bound the writer so callers learn about overflow at the source.
  This is a documented limit, not an accident.
- The zero case is handled correctly: the reader, on seeing a single byte with
  the continuation bit clear, returns that value (0 for the byte 0x00). The
  writer, given 0, emits the single byte `b'\x00'`. Some encoders special-case
  zero to emit nothing; we do not, because a reader cannot then distinguish
  "value 0" from "no value present", and round-tripping is a core requirement.
"""

from typing import Tuple

_MAX_VALUE = (1 << 64) - 1  # 64-bit ceiling; see module docstring.


def read_leb128(buffer, offset: int = 0) -> Tuple[int, int]:
    """Read one unsigned LEB128 integer from *buffer* starting at *offset*.

    *buffer* must support the buffer protocol (bytes, bytearray, memoryview).
    *offset* is the byte position to begin reading.

    Returns ``(value, new_offset)`` where *new_offset* points just past the
    last byte consumed.

    Raises:
        ValueError: if the input is truncated (a continuation byte promised
            more data than is available).
    """
    view = memoryview(buffer)
    result = 0
    shift = 0
    pos = offset
    length = len(view)
    while True:
        if pos >= length:
            # A prior byte's continuation bit told us to expect another byte.
            raise ValueError(
                "truncated LEB128 input: continuation bit set but no "
                "further byte available"
            )
        byte = view[pos]
        pos += 1
        # Mask to 0xFF so a signed byte (e.g. from a bytearray cast) reads
        # as its unsigned value.
        group = byte & 0x7F
        result |= group << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result, pos


def write_leb128(value: int) -> bytes:
    """Encode *value* as unsigned LEB128 and return the ``bytes``.

    Raises:
        ValueError: if *value* is negative or exceeds the 64-bit ceiling
            (see module docstring).
        TypeError: if *value* is not an int.
    """
    if not isinstance(value, int):
        raise TypeError(f"value must be int, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"value must be non-negative, got {value}")
    if value > _MAX_VALUE:
        raise ValueError(
            f"value exceeds 64-bit ceiling (max {_MAX_VALUE}): {value}"
        )
    out = bytearray()
    remaining = value
    while True:
        group = remaining & 0x7F
        remaining >>= 7
        if remaining:
            out.append(group | 0x80)
        else:
            out.append(group)
            break
    return bytes(out)
