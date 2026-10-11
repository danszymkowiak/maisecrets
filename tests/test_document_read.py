"""A Read of a PDF or an image (docs/TERMS.md, "PDF and image reads"): the client hands the model the document,
which no hook can redact, so the person decides first, and the model learns the local route to the text.

Run: python3 -m unittest tests.test_document_read -v
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

from maisecrets import hooks  # noqa: E402
from _hygiene import CLAUDE, CODEX  # noqa: E402

DOCUMENTS = ("scan.pdf", "photo.png", "photo.jpg", "photo.jpeg", "anim.gif", "pic.webp", "fax.tif", "fax.tiff")


def _read(path: str, client: dict = CLAUDE) -> dict:
    return hooks.pre_tool({"hook_event_name": "PreToolUse", "tool_name": "Read", "session_id": "S1",
                           "transcript_path": "", "cwd": "/work", **client,
                           "tool_input": {"file_path": f"/work/docs/{path}"}})


class DocumentReadTests(unittest.TestCase):
    def test_a_pdf_or_an_image_asks_the_person_first(self):
        for name in DOCUMENTS:
            with self.subTest(name):
                out = _read(name)["hookSpecificOutput"]
                self.assertEqual(out["permissionDecision"], "ask")
                self.assertNotIn("updatedInput", out, "the call itself is not changed")

    def test_the_extension_counts_in_any_case(self):
        for name in ("SCAN.PDF", "Photo.Png", "fax.TiFf"):
            with self.subTest(name):
                self.assertEqual(_read(name)["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_other_files_are_unchanged(self):
        for name in ("notes.txt", "main.py", "report.pdf.txt", "pdf", "image.svg", "data.csv"):
            with self.subTest(name):
                self.assertEqual(_read(name), {})

    def test_the_prompt_says_what_each_answer_means(self):
        reason = _read("scan.pdf")["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("unredacted", reason)
        self.assertIn("scan.pdf", reason)
        self.assertIn("deny", reason.lower())
        self.assertIn("text", reason)

    def test_codex_gets_a_deny_that_names_the_local_route(self):
        out = _read("scan.pdf", CODEX)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("pdftotext -layout", out["permissionDecisionReason"])
        img = _read("photo.png", CODEX)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("tesseract", img)

    def test_the_model_learns_the_local_route_at_session_start(self):
        self.assertIn("pdftotext -layout file.pdf -", hooks.PRIMER)
        self.assertIn("tesseract image.png - -l pol+eng", hooks.PRIMER)


if __name__ == "__main__":
    unittest.main()
