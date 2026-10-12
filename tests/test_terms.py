"""Personal terms (docs/TERMS.md): the parser of terms.txt and its loader.

Run: python3 -m unittest tests.test_terms -v
Synthetic names only (Jan Kowalski, ul. Przykladowa 12).
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import terms  # noqa: E402
from maisecrets.terms import Entity, TermsError, Variant  # noqa: E402

SAMPLE = """\
# label      variants
PERSON_A     Jan Kowalski | Kowalsk* | Jan

ADDRESS_A    ul.  Przykladowa 12   |  *przykladowa*
CASE_A       *sygn
"""


class ParseTests(unittest.TestCase):
    def test_label_and_variants_blank_lines_and_comments(self):
        got = terms.parse(SAMPLE)
        self.assertEqual([e.label for e in got], ["PERSON_A", "ADDRESS_A", "CASE_A"])
        self.assertEqual([v.text for v in got[0].variants], ["Jan Kowalski", "Kowalsk", "Jan"])
        self.assertEqual(got[0].line, 2)
        self.assertEqual(got[1].line, 4)

    def test_whitespace_is_trimmed_and_inner_runs_become_one_space(self):
        got = terms.parse(SAMPLE)
        self.assertEqual([v.text for v in got[1].variants], ["ul. Przykladowa 12", "przykladowa"])

    def test_the_four_modes(self):
        got = terms.parse("PERSON_A  Jan | Kowalsk* | *kowalski | *kowalski*\n")
        self.assertEqual(got[0].variants, (Variant("Jan", terms.WORD), Variant("Kowalsk", terms.STARTS),
                                           Variant("kowalski", terms.ENDS), Variant("kowalski", terms.INSIDE)))

    def test_canonical_is_the_first_variant_without_a_star(self):
        self.assertEqual(terms.parse("PERSON_A  Kowalsk* | Jan Kowalski | Jan\n")[0].canonical, "Jan Kowalski")
        self.assertIsNone(terms.parse("CASE_A  *sygn\n")[0].canonical)

    def test_tabs_separate_the_label(self):
        self.assertEqual(terms.parse("PERSON_A\tJan\n")[0], Entity("PERSON_A", (Variant("Jan", terms.WORD),), 1))

    def test_no_file_content_no_entities(self):
        self.assertEqual(terms.parse(""), [])
        self.assertEqual(terms.parse("# only a comment\n\n   \n"), [])


class RejectTests(unittest.TestCase):
    """Every error names the line number and never the text of the line."""

    def assertRejected(self, text: str, line: int, words: tuple[str, ...] = ()):
        with self.assertRaises(TermsError) as cm:
            terms.parse(text)
        msg = str(cm.exception)
        self.assertIn(f"line {line}", msg)
        self.assertEqual(cm.exception.line, line)
        for word in words:
            self.assertNotIn(word.lower(), msg.lower(), "an error must not show a term")
        return msg

    def test_missing_label(self):
        self.assertRejected("# x\nKowalski | Jan\n", 2, ("Kowalski", "Jan"))
        self.assertRejected("Kowalski\n", 1, ("Kowalski",))

    def test_bad_label_shape(self):
        for label in ("person_a", "PERSON1", "Kowalski", "P" * 33, "_PERSON"):
            with self.subTest(label=label):
                self.assertRejected(f"{label}  Jan Nowak\n", 1, (label, "Nowak"))

    def test_label_that_is_a_detector_type(self):
        with self.assertRaises(TermsError) as cm:
            terms.parse("EMAIL  Jan Kowalski\n", reserved=frozenset({"EMAIL", "SECRET"}))
        self.assertEqual(cm.exception.line, 1)
        self.assertNotIn("Kowalski", str(cm.exception))

    def test_empty_variant(self):
        for rest in ("Jan || Kowalski", "Jan | ", "*", "**", "Jan | * | Kowalski"):
            with self.subTest(rest=rest):
                self.assertRejected(f"PERSON_A  {rest}\n", 1, ("Jan", "Kowalski"))
        self.assertRejected("PERSON_A\n", 1)

    def test_star_inside_a_variant(self):
        self.assertRejected("PERSON_A  Kow*ski\n", 1, ("Kow",))

    def test_short_anywhere_term(self):
        self.assertRejected("PERSON_A  Jan | *jan*\n", 1, ("jan",))
        self.assertRejected("PERSON_A  * ab *\n", 1, ("ab",))
        # four characters between the stars, and the other modes, are fine
        self.assertEqual(len(terms.parse("PERSON_A  *nowa* | jan* | *an | Al\n")[0].variants), 4)

    def test_duplicate_label(self):
        self.assertRejected("PERSON_A  Jan\n\nPERSON_A  Nowak\n", 3, ("Jan", "Nowak"))

    def test_first_bad_line_is_reported(self):
        self.assertRejected("PERSON_A  Jan\nbad line\nPERSON_A  Nowak\n", 2, ("bad",))


class LoadTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "terms.txt"

    def tearDown(self):
        for p in self.dir.iterdir():
            p.unlink()
        self.dir.rmdir()

    def write(self, text: str, mode: int = 0o600) -> None:
        self.path.write_text(text, encoding="utf-8")
        os.chmod(self.path, mode)

    def test_missing_file_is_no_terms(self):
        self.assertEqual(terms.load(self.path), [])

    def test_default_path_is_in_the_vault_home(self):
        from maisecrets import vault
        self.assertEqual(terms.default_path(), vault.HOME / "terms.txt")

    def test_private_file_loads(self):
        self.write(SAMPLE)
        self.assertEqual(len(terms.load(self.path)), 3)

    @unittest.skipIf(os.name == "nt", "POSIX mode bits")
    def test_group_or_world_readable_file_is_refused(self):
        # mode bits, not a failed open: the check holds for root in CI too
        for mode in (0o640, 0o604, 0o644, 0o660):
            with self.subTest(mode=oct(mode)):
                self.write(SAMPLE, mode)
                with self.assertRaises(TermsError) as cm:
                    terms.load(self.path)
                msg = str(cm.exception)
                self.assertIn("terms.txt", msg)
                self.assertIn("chmod 600", msg)
                self.assertNotIn("Kowalsk", msg)

    def test_not_utf8_is_refused_without_its_bytes(self):
        self.path.write_bytes("PERSON_A  Łukasz\n".encode("utf-16"))
        os.chmod(self.path, 0o600)
        with self.assertRaises(TermsError) as cm:
            terms.load(self.path)
        # the path is left out of the check: a temp directory named ...-0xk2svyy failed it (TASK-14, 2026-10-12)
        detail = str(cm.exception).replace(str(self.path), "<path>")
        self.assertNotIn("0x", detail)
        self.assertNotIn("position", detail, "the decoder's detail names the byte's place and value")

    def test_parse_errors_pass_through_load(self):
        self.write("PERSON_A  Jan\nPERSON_A  Nowak\n")
        with self.assertRaises(TermsError) as cm:
            terms.load(self.path)
        self.assertEqual(cm.exception.line, 2)
        self.assertIn("terms.txt", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
