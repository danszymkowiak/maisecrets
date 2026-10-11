"""Personal terms (docs/TERMS.md) through the hook entry points: a prompt, a tool result, a tool call.

Run: python3 -m unittest tests.test_terms_hooks -v
Synthetic names only (Jan Kowalski). A placeholder here is built from OPEN and CLOSE, so the file holds none.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import detect, hooks  # noqa: E402
from maisecrets.placeholder import CLOSE, OPEN  # noqa: E402
from maisecrets.vault import HOME  # noqa: E402
import _hygiene  # noqa: E402
from _hygiene import CLAUDE  # noqa: E402

TERMS = Path(HOME, "terms.txt")
PERSON = f"{OPEN}PERSON_A_c0{CLOSE}"
CASE = f"{OPEN}CASE_A_c0{CLOSE}"
STATE = ("index.json", "vault.json", "audit.log", "hooks.log", "terms.txt")


def _clean() -> None:
    for f in STATE:
        try:
            os.unlink(Path(HOME, f))
        except FileNotFoundError:
            pass
    detect.reset_terms()


def setUpModule():  # noqa: N802 - unittest hook
    Path(HOME, "config.json").write_text('{"backend": "jsonfile", "allow_plaintext_store": true}')


def tearDownModule():  # noqa: N802 - unittest hook
    _clean()
    _hygiene.assert_pristine()


def _write_terms(text: str, mode: int = 0o600) -> None:
    TERMS.write_text(text, encoding="utf-8")
    os.chmod(TERMS, mode)
    detect.reset_terms()


def _bash_result(stdout: str, session: str = "S1") -> dict:
    return hooks.post_tool({"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": session,
                            "tool_input": {"command": "cat notes.txt"}, **CLAUDE,
                            "tool_response": {"stdout": stdout, "stderr": ""}})


def _mcp_call(q: str, session: str = "S1") -> dict:
    return hooks.pre_tool({"tool_name": "mcp__x__y", "session_id": session, "prompt_id": "p",
                           "transcript_path": "", "tool_input": {"q": q}})


class TermHookTests(unittest.TestCase):
    def setUp(self):
        _clean()
        _write_terms("PERSON_A  Jan Kowalski | Kowalsk*\nCASE_A  *sygn-0042*\n")
        _hygiene.patch(self, hooks, "_clipboard", lambda t: True)

    def tearDown(self):
        _clean()

    def test_a_term_in_a_tool_result_becomes_its_entity_placeholder(self):
        out = _bash_result("Pan Kowalskiego i Jan Kowalski, akta X-sygn-0042-B.")
        self.assertEqual(out["hookSpecificOutput"]["updatedToolOutput"]["stdout"],
                         f"Pan {PERSON} i {PERSON}, akta X-{CASE}-B.")

    def test_same_entity_same_placeholder_across_documents_and_sessions(self):
        a = _bash_result("Kowalski", "S1")["hookSpecificOutput"]["updatedToolOutput"]["stdout"]
        b = _bash_result("JAN\nKOWALSKI", "S2")["hookSpecificOutput"]["updatedToolOutput"]["stdout"]
        self.assertEqual((a, b), (PERSON, PERSON))

    def test_a_term_in_a_prompt_does_not_reach_the_model(self):
        out = hooks.user_prompt({"prompt": "napisz do Jan Kowalski", "session_id": "S1",
                                 "transcript_path": "", **CLAUDE})
        self.assertEqual(out.get("decision"), "block")
        self.assertNotIn("Kowalski", json.dumps(out))

    def test_the_placeholder_resolves_to_the_first_plain_variant_in_a_session_that_saw_it(self):
        _bash_result("Kowalskiego", "S1")
        out = _mcp_call(f"list for {PERSON}", "S1")
        self.assertEqual(out["hookSpecificOutput"]["updatedInput"]["q"], "list for Jan Kowalski")

    def test_a_session_that_never_saw_the_term_cannot_resolve_it(self):
        _bash_result("Kowalskiego", "S1")
        out = _mcp_call(f"list for {PERSON}", "S9")
        self.assertNotIn("Kowalski", json.dumps(out))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_an_entity_without_a_plain_variant_is_refused_by_its_label(self):
        _bash_result("sygn-0042", "S1")
        out = _mcp_call(f"case {CASE}", "S1")
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("CASE_A", json.dumps(out))
        self.assertNotIn("sygn", json.dumps(out))

    def test_the_term_is_never_copied_into_the_store_or_the_index(self):
        _bash_result("Jan Kowalski", "S1")
        _mcp_call(f"list for {PERSON}", "S1")
        for name in ("index.json", "vault.json", "audit.log"):
            p = Path(HOME, name)
            if p.exists():
                self.assertNotIn("kowalsk", p.read_text(encoding="utf-8").lower(), name)

    def test_no_terms_file_no_term_matches(self):
        _clean()
        self.assertEqual(detect.scan("Jan Kowalski sygn-0042"), [])
        self.assertEqual(_bash_result("Jan Kowalski"), {})

    @unittest.skipIf(os.name == "nt", "POSIX mode bits")
    def test_a_readable_terms_file_fails_closed_without_a_term(self):
        _write_terms("PERSON_A  Jan Kowalski\n", 0o644)
        with self.assertRaises(hooks.ConfigError) as cm:
            detect.scan("hello")
        self.assertIn("terms.txt", str(cm.exception))
        out = hooks._post_tool_guarded({"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "S1",
                                        "tool_input": {"command": "cat notes.txt"}, **CLAUDE,
                                        "tool_response": {"stdout": "Jan Kowalski", "stderr": ""}})
        self.assertIn("terms.txt", json.dumps(out))
        self.assertNotIn("Kowalski", json.dumps(out), "the output is withheld, and no message shows a term")

    def test_a_shape_claims_its_span_before_a_term(self):
        _write_terms("PERSON_A  *kowalski*\n")
        token = "glpat-" + "KowalskiXyz1234567890"
        kinds = [m.type for m in detect.scan(f"token {token} and Kowalski")]
        self.assertEqual(kinds, ["SECRET", "PERSON_A"])


if __name__ == "__main__":
    unittest.main()
