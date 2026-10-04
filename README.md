# Leb128 Unsigned Integer

Reads and writes unsigned integers encoded as Little-Endian Base 128 (LEB128), consuming a variable number of bytes from a buffer.

## Usage

```python
from leb128_unsigned_integer import read_leb128, write_leb128

# Encode an integer to LEB128 bytes.
encoded = write_leb128(16384)
# encoded == b'\x80\x80\x01'

# Decode from a buffer at a given offset.
value, new_offset = read_leb128(encoded, 0)
# value == 16384, new_offset == 3
```

## Why this exists

LEB128 appears in binary formats where integers are size-predictable but variable-width: DWARF debug info, WebAssembly, Protocol Buffers wire encoding. Reading and writing it correctly means handling the 7-bit grouping, the little-endian ordering, and the continuation bit. This library does exactly that and nothing more.

The trade-off is simplicity over generality. There is no signed-LEB128 variant here, no stream class with internal cursors, no async reader. The reader is a pure function that takes a buffer and an offset and returns the value plus the new offset. The writer returns `bytes`. If you need signed LEB128, wrap or fork; do not expect this library to grow that surface.

## The awkward edge

The writer rejects integers above 2**64 - 1. This is a deliberate ceiling, not a bug: real-world LEB128 consumers cap the meaningful range well below 64 bits, and silently accepting thousand-byte encodings of astronomically large integers would let bugs propagate. If your use case genuinely needs unbounded magnitude, this is the wrong library.

Zero is encoded as the single byte `b'\x00'`, not as the empty byte string. An encoder that emits nothing for zero makes the value indistinguishable from "absent" on read, which breaks round-tripping. Every value this library writes, including zero, can be read back.
