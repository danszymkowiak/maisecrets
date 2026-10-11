"""Personal terms (docs/TERMS.md): the matcher compiled from parsed entities.

Run: python3 -m unittest tests.test_term_match -v
Synthetic names only (Jan Kowalski, ul. Przykladowa 12).
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import terms  # noqa: E402


def matcher(text: str) -> terms.Matcher:
    return terms.compile_entities(terms.parse(text))


def runs(m: terms.Matcher, text: str) -> list[tuple[str, str]]:
    return [(text[s:e], ent.label) for s, e, ent in m.find(text)]


class StandaloneTests(unittest.TestCase):
    def setUp(self):
        self.m = matcher("PERSON_A  Jan\n")

    def test_matches_with_no_letter_or_digit_around(self):
        for text in ("Jan", "Jan, hello", "(Jan)", "Jan's car", "x\nJan\ny", "| Jan |", "|Jan|", "-Jan-", "_Jan_"):
            with self.subTest(text=text):
                self.assertEqual(runs(self.m, text), [("Jan", "PERSON_A")])

    def test_no_match_inside_a_word(self):
        for text in ("January", "Janek", "Dajan", "Jan2", "2Jan", "Janö", "öJan"):
            with self.subTest(text=text):
                self.assertEqual(runs(self.m, text), [])


class ModeTests(unittest.TestCase):
    def test_word_start_any_ending_is_one_run(self):
        m = matcher("PERSON_A  Kowalsk*\n")
        for word in ("Kowalski", "Kowalskiego", "Kowalskiej"):
            with self.subTest(word=word):
                self.assertEqual(runs(m, f"dla {word}."), [(word, "PERSON_A")])
        self.assertEqual(runs(m, "Nowakowalski"), [])

    def test_any_start_word_end(self):
        m = matcher("PERSON_A  *kowalski\n")
        self.assertEqual(runs(m, "Kowalski JanKowalski"), [("Kowalski", "PERSON_A"), ("JanKowalski", "PERSON_A")])
        self.assertEqual(runs(m, "Kowalskiego"), [])

    def test_anywhere_takes_the_whole_run_also_in_an_email_address(self):
        m = matcher("PERSON_A  *kowalski*\n")
        address = "jan." + "kowalski1984" + "@" + "example.com"
        self.assertEqual(runs(m, f"<{address}>"), [("kowalski1984", "PERSON_A")])
        self.assertEqual(runs(m, "akta_JanKowalskiego2.pdf"), [("JanKowalskiego2", "PERSON_A")])


class TextTests(unittest.TestCase):
    def test_case_insensitive_with_polish_letters(self):
        m = matcher("CITY_A  łódź | Żółć*\n")
        self.assertEqual(runs(m, "ŁÓDŹ i Łódź"), [("ŁÓDŹ", "CITY_A"), ("Łódź", "CITY_A")])
        self.assertEqual(runs(m, "ŻÓŁCIĄ"), [])
        self.assertEqual(runs(m, "żółćą"), [("żółćą", "CITY_A")])

    def test_whitespace_in_a_term_matches_any_whitespace_run(self):
        m = matcher("PERSON_A  Jan Kowalski\n")
        for text in ("Jan Kowalski", "Jan\tKowalski", "Jan\nKowalski", "Jan \r\n  Kowalski"):
            with self.subTest(text=text):
                self.assertEqual(runs(m, text), [(text, "PERSON_A")])
        self.assertEqual(runs(m, "JanKowalski"), [])

    def test_longest_variant_wins_across_entities(self):
        m = matcher("FIRST_A  Jan\nPERSON_A  Kowalski | Jan Kowalski\n")
        self.assertEqual(runs(m, "Jan Kowalski, Jan"), [("Jan Kowalski", "PERSON_A"), ("Jan", "FIRST_A")])

    def test_regex_characters_are_literal(self):
        m = matcher("ADDRESS_A  ul. Przykladowa 12 | a+b (c)\n")
        self.assertEqual(runs(m, "ul. Przykladowa 12"), [("ul. Przykladowa 12", "ADDRESS_A")])
        self.assertEqual(runs(m, "ulX Przykladowa 12"), [])
        self.assertEqual(runs(m, "x a+b (c) y"), [("a+b (c)", "ADDRESS_A")])
        self.assertEqual(runs(m, "aab (c)"), [])

    def test_no_entities_match_nothing(self):
        self.assertEqual(terms.compile_entities([]).find("Jan Kowalski"), [])


if __name__ == "__main__":
    unittest.main()
