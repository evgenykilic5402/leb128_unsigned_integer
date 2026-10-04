import unittest

from leb128_unsigned_integer import read_leb128, write_leb128


class TestReadLeb128(unittest.TestCase):
    def test_zero(self):
        value, offset = read_leb128(b"\x00")
        self.assertEqual(value, 0)
        self.assertEqual(offset, 1)

    def test_single_byte_max(self):
        value, offset = read_leb128(b"\x7f")
        self.assertEqual(value, 127)
        self.assertEqual(offset, 1)

    def test_two_byte_min(self):
        value, offset = read_leb128(b"\x80\x01")
        self.assertEqual(value, 128)
        self.assertEqual(offset, 2)

    def test_two_byte_max(self):
        value, offset = read_leb128(b"\xff\x7f")
        self.assertEqual(value, 16383)
        self.assertEqual(offset, 2)

    def test_three_byte_midrange(self):
        value, offset = read_leb128(b"\x80\x80\x01")
        self.assertEqual(value, 16384)
        self.assertEqual(offset, 3)

    def test_large_value(self):
        value, offset = read_leb128(b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x01")
        self.assertEqual(value, 1 << 63)
        self.assertEqual(offset, 10)

    def test_offset_start(self):
        value, offset = read_leb128(b"\xff\x7f", 1)
        self.assertEqual(value, 127)
        self.assertEqual(offset, 2)

    def test_truncated_continuation(self):
        with self.assertRaises(ValueError):
            read_leb128(b"\x80")

    def test_truncated_midway(self):
        with self.assertRaises(ValueError):
            read_leb128(b"\x80\x80")

    def test_bytearray_input(self):
        value, offset = read_leb128(bytearray(b"\x80\x01"))
        self.assertEqual(value, 128)
        self.assertEqual(offset, 2)

    def test_memoryview_input(self):
        value, offset = read_leb128(memoryview(b"\x80\x01"))
        self.assertEqual(value, 128)
        self.assertEqual(offset, 2)


class TestWriteLeb128(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(write_leb128(0), b"\x00")

    def test_single_byte_max(self):
        self.assertEqual(write_leb128(127), b"\x7f")

    def test_two_byte_min(self):
        self.assertEqual(write_leb128(128), b"\x80\x01")

    def test_two_byte_max(self):
        self.assertEqual(write_leb128(16383), b"\xff\x7f")

    def test_three_byte_min(self):
        self.assertEqual(write_leb128(16384), b"\x80\x80\x01")

    def test_large_value(self):
        self.assertEqual(
            write_leb128(1 << 63),
            b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x01",
        )

    def test_returns_bytes(self):
        self.assertIsInstance(write_leb128(0), bytes)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            write_leb128(-1)

    def test_non_int_rejected(self):
        with self.assertRaises(TypeError):
            write_leb128("128")

    def test_overflow_rejected(self):
        with self.assertRaises(ValueError):
            write_leb128((1 << 65))


class TestRoundTrip(unittest.TestCase):
    def _round_trip(self, value):
        encoded = write_leb128(value)
        decoded, offset = read_leb128(encoded)
        self.assertEqual(decoded, value)
        self.assertEqual(offset, len(encoded))

    def test_round_trip_zero(self):
        self._round_trip(0)

    def test_round_trip_powers_of_two(self):
        for exp in range(0, 64):
            self._round_trip(1 << exp)

    def test_round_trip_boundaries(self):
        self._round_trip((1 << 7) - 1)
        self._round_trip(1 << 7)
        self._round_trip((1 << 14) - 1)
        self._round_trip(1 << 14)
        self._round_trip((1 << 21) - 1)
        self._round_trip(1 << 21)

    def test_round_trip_max(self):
        self._round_trip((1 << 64) - 1)


if __name__ == "__main__":
    unittest.main()
