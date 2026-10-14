"""The redact tool's skeleton (TASK-34.1): its command answers --help and --version, refuses to write an output while
no detector exists, and the plugin never depends on it.

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "maisecrets_redact", *args], capture_output=True, text=True,
                          timeout=60)


class CommandTests(unittest.TestCase):
    def test_help_names_the_command_and_its_input(self):
        r = run("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("redact", r.stdout)
        self.assertIn("PATH", r.stdout)

    def test_version(self):
        from maisecrets_redact import __version__
        r = run("--version")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, f"redact {__version__}"))

    def test_without_the_plugin_checkout_nothing_is_written(self):
        # an output named .redacted.txt that redacts nothing would be worse than none
        import os
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "notes.txt"
            src.write_text("nothing here\n", encoding="utf-8")
            r = subprocess.run([sys.executable, "-m", "maisecrets_redact", str(src)], capture_output=True, text=True,
                               timeout=60, env={**os.environ, "MAISECRETS_REPO": d})
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("no maisecrets checkout", r.stderr)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ["notes.txt"])


class BoundaryTests(unittest.TestCase):
    """The plugin stays fast and light: it imports nothing of the tool and nothing outside the standard library."""

    def imports(self, folder: str) -> list[tuple[str, str]]:
        out = []
        for path in sorted((ROOT / folder).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    out += [(str(path.relative_to(ROOT)), a.name.split(".")[0]) for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    out.append((str(path.relative_to(ROOT)), node.module.split(".")[0]))
        return out

    def test_the_plugin_imports_only_the_standard_library_and_itself(self):
        allowed = set(sys.stdlib_module_names) | {"maisecrets", "hooks", "_platform_fakes"}
        for folder in ("maisecrets", "hooks"):
            for where, mod in self.imports(folder):
                with self.subTest(where=where, module=mod):
                    self.assertIn(mod, allowed)
                    self.assertNotEqual(mod, "maisecrets_redact")

    def test_the_repository_root_declares_no_dependency(self):
        for name in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
            self.assertFalse((ROOT / name).exists(), name)


class CheckoutTests(unittest.TestCase):
    """The tool finds the checkout it lives in by a file of it (maisecrets/detect.py), not by a count of parent
    folders: the count broke silently when the module moved into adapters/ (TASK-62)."""

    def test_the_checkout_is_the_one_this_tool_lives_in(self):
        from maisecrets_redact.adapters import plugin_rules
        here = Path(__file__).resolve().parents[2]
        self.assertEqual(plugin_rules.checkout(), here)
        self.assertTrue((plugin_rules.checkout() / "maisecrets" / "detect.py").is_file())


if __name__ == "__main__":
    unittest.main()
