"""scripts/scan_tree.py: in a git checkout it scans what git would carry (tracked and untracked files, not ignored
ones), so private notes kept in an ignored folder do not fail the push; outside git it scans every file.

Run: python3 -m unittest tests.test_scan_tree -v
The token is generated at run time, so no literal sits in the tree.
"""
from __future__ import annotations

import importlib.util
import io
import os
import random
import shutil
import string
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("scan_tree", ROOT / "scripts" / "scan_tree.py")
scan_tree = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scan_tree)

_R = random.Random(25)
TOKEN = "ghp_" + "".join(_R.choice(string.ascii_letters + string.digits) for _ in range(36))


def run(root: Path) -> tuple[int, str]:
    out = io.StringIO()
    with redirect_stdout(out):
        code = scan_tree.main([str(root)])
    return code, out.getvalue()


class ScanTreeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / "clean.txt").write_text("nothing here\n", encoding="utf-8")
        (self.root / "notes").mkdir()
        (self.root / "notes" / "idea.md").write_text(f"token = {TOKEN}\n", encoding="utf-8")

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    @unittest.skipUnless(shutil.which("git"), "git is not installed")
    def test_an_ignored_folder_is_not_scanned_in_a_checkout(self):
        self.git("init", "-q")
        (self.root / ".gitignore").write_text("notes/\n", encoding="utf-8")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertNotIn("notes/idea.md", out)

    @unittest.skipUnless(shutil.which("git"), "git is not installed")
    def test_an_untracked_file_that_is_not_ignored_is_scanned(self):
        self.git("init", "-q")
        code, out = run(self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("notes/idea.md:1:", out)
        self.assertNotIn(TOKEN, out, "the hit names the place, never the value")

    def test_outside_git_every_file_is_scanned(self):
        code, out = run(self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("notes/idea.md:1:", out)


if __name__ == "__main__":
    unittest.main()
