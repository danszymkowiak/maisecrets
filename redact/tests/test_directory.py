"""A directory run (TASK-34.6, the user's request of 2026-10-12): the tree is mirrored into an output directory, every
supported file redacted, unsupported files skipped with one line each, placeholders consistent across the whole run,
a symlink out of the tree skipped, and an output inside the source tree refused.

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _home  # noqa: E402,F401  first: a temp maisecrets home

from maisecrets_redact import app  # noqa: E402
from test_extract import minimal_pdf  # noqa: E402

MAIL = "max.muster@firma-beispiel.ch"
IBAN = "CH93 0076 2011 6238 5295 7"


class DirectoryTests(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp())
        self.src = base / "docs"
        (self.src / "2025").mkdir(parents=True)
        (self.src / "notes.txt").write_text(f"mail {MAIL}\n", encoding="utf-8")
        (self.src / "konten.csv").write_text(f"name,iban\nMax,{IBAN}\n", encoding="utf-8")
        (self.src / "2025" / "auszug.pdf").write_bytes(minimal_pdf([[f"IBAN {IBAN}", f"Kontakt {MAIL}"]]))
        from openpyxl import Workbook
        wb = Workbook()
        wb.active.append(["email"])
        wb.active.append([MAIL])
        wb.save(self.src / "2025" / "liste.xlsx")
        (self.src / "foto.jpg").write_bytes(b"\xff\xd8\xff")
        outside = base / "outside.txt"
        outside.write_text(f"secret {MAIL}\n", encoding="utf-8")
        (self.src / "link.txt").symlink_to(outside)
        self.out = base / "docs.redacted"
        self.lines: list[str] = []

    def run_dir(self, **kw):
        return app.run_dir(self.src, self.out, model_detectors={}, regions=("generic",), interactive=False,
                           log=self.lines.append, **kw)

    def test_the_tree_is_mirrored_and_every_supported_file_redacted(self):
        summary = self.run_dir(recursive=True)
        got = sorted(str(p.relative_to(self.out)) for p in self.out.rglob("*") if p.is_file())
        # a table comes out as CSV, a workbook as one per sheet (TASK-54)
        self.assertEqual(got, ["2025/auszug.pdf.redacted.txt", "2025/liste.xlsx.Sheet.redacted.csv",
                               "konten.csv.redacted.csv", "notes.txt.redacted.txt"])
        for p in self.out.rglob("*.redacted.*"):
            text = p.read_text(encoding="utf-8")
            self.assertNotIn(MAIL, text)
            self.assertNotIn(IBAN, text)
        self.assertEqual((summary.written, summary.skipped), (4, 2))
        self.assertEqual(summary.counts, {"EMAIL": 1, "IBAN": 1}, "one placeholder per value across the run")

    def test_the_same_value_keeps_its_placeholder_across_files(self):
        self.run_dir(recursive=True)
        notes = (self.out / "notes.txt.redacted.txt").read_text(encoding="utf-8")
        listed = (self.out / "2025" / "liste.xlsx.Sheet.redacted.csv").read_text(encoding="utf-8")
        self.assertIn("⟦EMAIL_1⟧", notes)
        self.assertIn("⟦EMAIL_1⟧", listed)

    def test_unsupported_files_and_a_symlink_out_of_the_tree_are_skipped_with_a_line_each(self):
        self.run_dir(recursive=True)
        self.assertEqual(sum("foto.jpg" in line for line in self.lines), 1)
        self.assertEqual(sum("link.txt" in line and "outside" in line for line in self.lines), 1)
        self.assertFalse((self.out / "link.txt.redacted.txt").exists())

    def test_without_recursive_only_the_top_level(self):
        self.run_dir(recursive=False)
        self.assertFalse((self.out / "2025").exists())
        self.assertTrue((self.out / "notes.txt.redacted.txt").exists())

    def test_an_output_inside_the_source_tree_is_refused(self):
        with self.assertRaisesRegex(ValueError, "inside"):
            app.run_dir(self.src, self.src / "out", model_detectors={}, regions=("generic",), interactive=False)

    def test_the_source_folder_itself_takes_the_output_next_to_each_file(self):
        # user, 2026-10-14: by default the redacted files go back into the same folder
        summary = app.run_dir(self.src, self.src, model_detectors={}, regions=("generic",), interactive=False,
                              recursive=True)
        self.assertTrue((self.src / "notes.txt.redacted.txt").exists())
        self.assertTrue((self.src / "2025" / "liste.xlsx.Sheet.redacted.csv").exists())
        self.assertNotIn(MAIL, (self.src / "notes.txt.redacted.txt").read_text(encoding="utf-8"))
        again = app.run_dir(self.src, self.src, model_detectors={}, regions=("generic",), interactive=False,
                            recursive=True)
        self.assertEqual(again.written, 0, "a second run does not redact its own output")
        self.assertFalse(list(self.src.rglob("*.redacted.*.redacted.*")))
        self.assertEqual(again.exists, summary.written)

    def test_an_existing_output_is_not_overwritten(self):
        self.run_dir(recursive=True)
        before = (self.out / "notes.txt.redacted.txt").read_text(encoding="utf-8")
        (self.src / "notes.txt").write_text("changed\n", encoding="utf-8")
        summary = self.run_dir(recursive=True)
        self.assertEqual((self.out / "notes.txt.redacted.txt").read_text(encoding="utf-8"), before)
        self.assertGreaterEqual(summary.exists, 1)

    def test_the_source_is_never_changed(self):
        before = {p: p.read_bytes() for p in self.src.rglob("*") if p.is_file() and not p.is_symlink()}
        self.run_dir(recursive=True)
        self.assertEqual({p: p.read_bytes() for p in before}, before)


class DirectoryCommandTests(unittest.TestCase):
    def test_the_command_takes_a_directory(self):
        import subprocess
        base = Path(tempfile.mkdtemp())
        (base / "in").mkdir()
        (base / "in" / "a.txt").write_text(f"mail {MAIL}\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "maisecrets_redact", str(base / "in"), "--rules-only"],
                           capture_output=True, text=True, timeout=120,
                           env={**os.environ, "MAISECRETS_HOME": _home.HOME})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 written", r.stderr)
        self.assertNotIn(MAIL, r.stderr)
        self.assertNotIn(MAIL, (base / "in" / "a.txt.redacted.txt").read_text(encoding="utf-8"),
                         "by default next to each file, in the same folder")
        r = subprocess.run([sys.executable, "-m", "maisecrets_redact", str(base / "in"), "--rules-only",
                            "--out", str(base / "elsewhere")], capture_output=True, text=True, timeout=120,
                           env={**os.environ, "MAISECRETS_HOME": _home.HOME})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((base / "elsewhere" / "a.txt.redacted.txt").exists())


if __name__ == "__main__":
    unittest.main()
