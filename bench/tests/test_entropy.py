"""Entropy variants (TASK-11.21): raw Shannon entropy, normalised by the value's alphabet, corrected for length, and
min-entropy.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import math
import unittest

from maisecrets_bench.domain import entropy


class CharsetTests(unittest.TestCase):
    def test_the_smallest_alphabet_that_holds_the_value(self):
        self.assertEqual(entropy.charset("deadbeef0123"), "hex")
        self.assertEqual(entropy.charset("DEADBEEF0123"), "hex")
        self.assertEqual(entropy.charset("MFRGGZDFMZTWQ2LK"), "base32")
        self.assertEqual(entropy.charset("abcXYZ019"), "base62")
        self.assertEqual(entropy.charset("ab+/cd=="), "base64")
        self.assertEqual(entropy.charset("ab-_cd"), "base64url")
        self.assertEqual(entropy.charset("a b!c"), "printable")


class VariantTests(unittest.TestCase):
    def test_raw_is_shannon_entropy_per_character(self):
        self.assertAlmostEqual(entropy.raw("abcd"), 2.0)
        self.assertEqual(entropy.raw(""), 0.0)

    def test_normalised_divides_by_the_bits_of_the_alphabet(self):
        self.assertAlmostEqual(entropy.normalised("0123456789abcdef"), 1.0)
        self.assertAlmostEqual(entropy.normalised("abcd"), 2.0 / 4.0)            # hex: 4 bits

    def test_length_corrected_divides_by_the_most_a_value_this_long_can_have(self):
        self.assertAlmostEqual(entropy.length_corrected("abcd"), 1.0)            # 4 distinct of 4
        self.assertAlmostEqual(entropy.length_corrected("aabb"), 1.0 / 2.0)
        self.assertEqual(entropy.length_corrected("a"), 0.0)

    def test_min_entropy_is_set_by_the_most_frequent_character(self):
        self.assertAlmostEqual(entropy.min_entropy("aaab"), -math.log2(0.75))
        self.assertAlmostEqual(entropy.min_entropy("abcd"), 2.0)
        self.assertLessEqual(entropy.min_entropy("aaabbc"), entropy.raw("aaabbc"))

    def test_every_variant_is_listed(self):
        self.assertEqual(set(entropy.VARIANTS), {"raw", "normalised", "length_corrected", "min"})


if __name__ == "__main__":
    unittest.main()
