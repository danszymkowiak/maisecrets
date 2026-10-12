"""The Veles sync (TASK-19.5): Kingfisher's generated veles.yml (Google Veles detectors, Apache-2.0, converted to
regexes by Kingfisher, Apache-2.0) becomes rules/veles.json. The pattern and its secret group stay; validation and
revocation go (the threat model sends no secret anywhere to test it); anything unknown stops the sync, naming the
rule. Nothing is fetched here: the tests feed parsed YAML."""
from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("sync_veles", ROOT / "scripts" / "sync_veles.py")
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)

RULE = {"name": "Deno Organization PAT", "id": "veles.secrets/denopatorg", "pattern": "(ddo_[A-Za-z0-9]{36})",
        "validation": {"type": "Http", "content": {}}, "revocation": {"type": "Http"}, "betterleaks_secret_group": 0,
        "references": ["https://raw.githubusercontent.com/google/osv-scalibr/abc/veles/secrets/deno/detector.go"]}


class ConvertTests(unittest.TestCase):
    def test_a_rule_keeps_its_pattern_and_group_and_loses_validation(self):
        out = sync.convert({"rules": [RULE, dict(RULE, id="veles.secrets/x", pattern="(?P<TOKEN>a(?P<P>b))",
                                                 betterleaks_secret_group=2, path="(?i)x$")]}, "v2.11.1", "abc")
        a, b = out["rules"]
        self.assertEqual((a["id"], a["regex"], a["secret_group"]), ("veles.secrets/denopatorg",
                                                                   "(ddo_[A-Za-z0-9]{36})", 0))
        self.assertNotIn("validation", a)
        self.assertEqual((b["secret_group"], b["path"]), (2, "(?i)x$"))
        self.assertEqual((out["kingfisher"], out["osv_scalibr"]), ("v2.11.1", "abc"))

    def test_an_unknown_field_or_a_missing_pattern_stops_the_sync_naming_the_rule(self):
        with self.assertRaisesRegex(sync.SyncError, "denopatorg.*'colour'"):
            sync.convert({"rules": [dict(RULE, colour="red")]}, "v1", "r")
        with self.assertRaisesRegex(sync.SyncError, "denopatorg.*pattern"):
            sync.convert({"rules": [{k: v for k, v in RULE.items() if k != "pattern"}]}, "v1", "r")

    def test_a_pattern_python_cannot_compile_stops_the_sync(self):
        with self.assertRaisesRegex(sync.SyncError, "denopatorg"):
            sync.convert({"rules": [dict(RULE, pattern="(ddo_[A-Z")]}, "v1", "r")


class LoadTests(unittest.TestCase):
    def test_a_kept_rule_finds_its_token_and_a_switched_off_rule_is_not_loaded(self):
        import random
        import string
        from maisecrets import detect
        ids = {r.id for r in detect.rules()}
        self.assertIn("veles.secrets/denopatorg", ids)
        self.assertNotIn("veles.secrets/sendgrid", ids, "covered by Betterleaks' sendgrid-api-token: off")
        r = random.Random(195)
        token = "ddo_" + "".join(r.choice(string.ascii_letters + string.digits) for _ in range(36))
        self.assertEqual([(m.kind, m.value) for m in detect.scan(f"deploy with {token} now")],
                         [("veles.secrets/denopatorg", token)])


if __name__ == "__main__":
    unittest.main()
