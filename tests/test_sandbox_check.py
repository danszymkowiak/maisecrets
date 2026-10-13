"""Does the Claude Code sandbox deny reads of the vault home (TASK-45)? C8 is text matching for Bash; the sandbox's
read deny is the boundary a run-time-built path cannot pass (THREAT-MODEL C8). /maisecrets:status says whether the
settings layers configure it, so a missing one is visible."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import sandbox_check as sc  # noqa: E402


class VerdictTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sbx-"))
        self.home = self.tmp / "u"
        self.vault = self.home / ".maisecrets"

    def layer(self, name, data, root=None):
        return sc.Layer(name, data, root or self.home / ".claude")

    def verdict(self, *layers):
        return sc.verdict(list(layers), self.vault, self.home)

    def test_no_settings_is_missing(self):
        v = self.verdict()
        self.assertFalse(v.denied)
        self.assertIn("not enabled", v.reason)

    def test_enabled_with_a_credentials_deny_of_the_home(self):
        v = self.verdict(self.layer("user", {"sandbox": {"enabled": True, "credentials": {
            "files": [{"path": "~/.maisecrets", "mode": "deny"}]}}}))
        self.assertTrue(v.denied)
        self.assertEqual(v.source, "user")

    def test_a_deny_of_a_parent_directory_covers_the_home(self):
        v = self.verdict(self.layer("user", {"sandbox": {"enabled": True, "filesystem": {"denyRead": ["~"]}}}))
        self.assertTrue(v.denied)

    def test_a_mask_entry_or_another_path_does_not_count(self):
        for files in ([{"path": "~/.maisecrets", "mode": "mask"}], [{"path": "~/.ssh", "mode": "deny"}]):
            with self.subTest(files=files):
                v = self.verdict(self.layer("user", {"sandbox": {"enabled": True, "credentials": {"files": files}}}))
                self.assertFalse(v.denied)
                self.assertIn("no read deny", v.reason)

    def test_a_deny_without_the_sandbox_enabled_does_not_count(self):
        v = self.verdict(self.layer("user", {"sandbox": {"credentials": {
            "files": [{"path": "~/.maisecrets", "mode": "deny"}]}}}))
        self.assertFalse(v.denied)

    def test_a_later_layer_can_turn_the_sandbox_off_and_managed_wins(self):
        on = {"sandbox": {"enabled": True, "credentials": {"files": [{"path": "~/.maisecrets", "mode": "deny"}]}}}
        off = {"sandbox": {"enabled": False}}
        self.assertFalse(self.verdict(self.layer("user", on), self.layer("project", off)).denied)
        self.assertTrue(self.verdict(self.layer("project", off), self.layer("managed", on)).denied)

    def test_filesystem_disabled_turns_the_read_denies_off(self):
        v = self.verdict(self.layer("user", {"sandbox": {"enabled": True, "filesystem": {"disabled": True},
                                                         "credentials": {"files": [{"path": "~/.maisecrets",
                                                                                    "mode": "deny"}]}}}))
        self.assertFalse(v.denied)
        self.assertIn("filesystem", v.reason)

    def test_a_relative_path_resolves_against_the_settings_root(self):
        v = self.verdict(self.layer("user", {"sandbox": {"enabled": True, "credentials": {
            "files": [{"path": "../.maisecrets", "mode": "deny"}]}}}))
        self.assertTrue(v.denied)


class LayerTests(unittest.TestCase):
    def test_layers_are_read_from_the_user_and_project_files_and_a_broken_file_is_named(self):
        tmp = Path(tempfile.mkdtemp(prefix="sbx-"))
        cfg = tmp / "claude"
        proj = tmp / "proj"
        (proj / ".claude").mkdir(parents=True)
        cfg.mkdir()
        (cfg / "settings.json").write_text(json.dumps({"sandbox": {"enabled": True}}), encoding="utf-8")
        (proj / ".claude" / "settings.local.json").write_text("{broken", encoding="utf-8")
        layers, problems = sc.layers(config_dir=cfg, project=proj, managed=tmp / "none.json")
        self.assertEqual([la.name for la in layers], ["user"])
        self.assertEqual(len(problems), 1)
        self.assertIn("settings.local.json", problems[0])

    def test_the_status_line(self):
        self.assertIn("missing", sc.line(sc.Verdict(False, "the sandbox is not enabled", None)))
        self.assertIn("on", sc.line(sc.Verdict(True, "", "user")))


class StatusTests(unittest.TestCase):
    def test_status_names_the_sandbox_deny(self):
        import io
        from contextlib import redirect_stdout
        from unittest import mock
        from maisecrets import cli
        tmp = Path(tempfile.mkdtemp(prefix="sbx-"))
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(tmp)}), \
                mock.patch.object(sc, "_managed_file", lambda: tmp / "none.json"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(cli.cmd_status([]), 0)
        self.assertIn("sandbox read deny of the vault: missing", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
