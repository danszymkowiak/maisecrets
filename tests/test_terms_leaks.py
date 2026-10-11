"""Personal terms (docs/TERMS.md) never leave as text: not in a log, the audit, an event, an incident record, a
report, a list, the status or an error. Each test drives a path with a term in it and then searches every
output and every file of the home but terms.txt itself.

Run: python3 -m unittest tests.test_terms_leaks -v
Synthetic names only. A placeholder here is built from OPEN and CLOSE, so the file holds none.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import cli, detect, hooks, incidents  # noqa: E402
from maisecrets.placeholder import CLOSE, OPEN  # noqa: E402
from maisecrets.vault import HOME  # noqa: E402
import _hygiene  # noqa: E402
from _hygiene import CLAUDE  # noqa: E402

TERMS = Path(HOME, "terms.txt")
GOOD = "PERSON_A  Zbigniew Testowski | Testowsk*\nCASE_A  *akt-0042x*\n"
# every piece of a term that would show it: the test searches each, lowercased
PIECES = ("zbigniew", "testowsk", "akt-0042x")
PERSON = f"{OPEN}PERSON_A_c0{CLOSE}"
STATE = ("index.json", "vault.json", "audit.log", "hooks.log", "events.log", "terms.txt")


def _clean() -> None:
    for f in STATE:
        try:
            os.unlink(Path(HOME, f))
        except FileNotFoundError:
            pass
    incidents.clear(Path(HOME))
    detect.reset_terms()


def _write_terms(text: str) -> None:
    TERMS.write_text(text, encoding="utf-8")
    os.chmod(TERMS, 0o600)
    detect.reset_terms()


def _cli(*argv: str) -> str:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            cli.main(list(argv))
        except SystemExit:
            pass
    return out.getvalue() + err.getvalue()


def _home_text() -> str:
    """Every file under the home but terms.txt, as text."""
    parts = []
    for p in Path(HOME).rglob("*"):
        if p.is_file() and p != TERMS:
            parts.append(f"--- {p.name}\n" + p.read_bytes().decode("utf-8", errors="replace"))
    return "\n".join(parts)


def _run_main(event: str, payload: dict, handler=None) -> str:
    buf = io.StringIO()
    patches = [mock.patch.object(hooks.sys, "stdin", io.StringIO(json.dumps(payload))),
               mock.patch.object(hooks.sys, "stdout", buf),
               mock.patch.object(hooks.os, "_exit", lambda code: None)]
    if handler is not None:
        patches.append(mock.patch.dict(hooks.HANDLERS, {event: handler}))
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        hooks.main(["hook", event])
    return buf.getvalue()


def setUpModule():  # noqa: N802 - unittest hook
    Path(HOME, "config.json").write_text('{"backend": "jsonfile", "allow_plaintext_store": true}')


def tearDownModule():  # noqa: N802 - unittest hook
    _clean()
    _hygiene.assert_pristine()


class _Base(unittest.TestCase):
    def setUp(self):
        _clean()
        _write_terms(GOOD)
        _hygiene.patch(self, hooks, "_clipboard", lambda t: True)

    def tearDown(self):
        _clean()

    def assertNoTerm(self, text: str, where: str) -> None:  # noqa: N802 - unittest style
        low = text.lower()
        for piece in PIECES:
            self.assertNotIn(piece, low, f"{where} shows a term")


class TermsNeverLeakTests(_Base):
    def _session(self) -> list[str]:
        """A prompt, a tool result and a tool call with terms, through the hook entry points."""
        outs = [_run_main("user-prompt", {"hook_event_name": "UserPromptSubmit", "session_id": "S1",
                                          "transcript_path": "", **CLAUDE,
                                          "prompt": "write to Zbigniew Testowski about akt-0042x"}),
                _run_main("post-tool", {"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "S1",
                                        "tool_input": {"command": "cat notes.txt"}, **CLAUDE,
                                        "tool_response": {"stdout": "Pan Testowskiego, akt-0042x-B", "stderr": ""}}),
                _run_main("pre-tool", {"hook_event_name": "PreToolUse", "tool_name": "mcp__x__y", "session_id": "S1",
                                       "transcript_path": "", **CLAUDE, "tool_input": {"q": f"mail {PERSON}"}})]
        return outs

    def test_the_hook_answers_logs_audit_and_events_hold_no_term(self):
        outs = self._session()
        self.assertIn("Zbigniew Testowski", outs[2], "the tool call got the value: the session ran for real")
        self.assertNoTerm(outs[0] + outs[1], "a hook answer to the model")
        for name in ("audit.log", "events.log", "hooks.log", "index.json"):
            self.assertTrue(Path(HOME, name).exists(), f"{name} was written: the path ran")
        self.assertNoTerm(_home_text(), "a file of the home")

    def test_report_audit_list_and_status_show_labels_only(self):
        self._session()
        for argv in (("list",), ("status",), ("audit",), ("report",), ("report", "last"), ("report", "1")):
            with self.subTest(argv):
                self.assertNoTerm(_cli(*argv), "maisecrets " + " ".join(argv))
        self.assertIn("PERSON_A", _cli("report"))

    def test_scan_names_the_label_and_the_span_only(self):
        out = _cli("scan", "hello Zbigniew Testowski")
        self.assertIn("PERSON_A", out)
        self.assertNoTerm(out.replace("hello Zbigniew Testowski", ""), "maisecrets scan")

    def test_a_crash_while_a_term_is_in_the_payload_records_no_term(self):
        def crash(payload):
            raise RuntimeError("boom near " + payload["tool_response"]["stdout"])
        out = _run_main("post-tool", {"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "S1",
                                      "tool_input": {"command": "cat notes.txt"}, **CLAUDE,
                                      "tool_response": {"stdout": "Zbigniew Testowski", "stderr": ""}}, crash)
        self.assertNoTerm(out, "the hook answer after a crash")
        self.assertNoTerm(_home_text(), "the incident record and the logs after a crash")
        self.assertNoTerm(_cli("status"), "status after a crash")


class StatusTests(_Base):
    def test_status_counts_the_entities_and_names_their_labels(self):
        self.assertIn("terms: 2 entities (CASE_A, PERSON_A)", _cli("status"))

    def test_status_without_a_terms_file(self):
        _clean()
        self.assertIn("terms: none", _cli("status"))

    def test_status_with_a_bad_terms_file_names_the_line_only(self):
        _write_terms("PERSON_A  Zbigniew Testowski\nPERSON_A  Testowsk*\n")
        out = _cli("status")
        self.assertIn("terms: unusable (", out)
        self.assertIn("terms.txt: line 2: the label appears on an earlier line", out)
        self.assertNoTerm(out, "status with a bad file")


class ErrorPathTests(_Base):
    BAD = {  # every refusal of the loader, each with a term on the bad line
        "empty variant": "PERSON_A  Zbigniew Testowski | \n",
        "inner star": "PERSON_A  Zbig*niew Testowski\n",
        "short inside": "PERSON_A  *Tes*\n",
        "bad label": "person_a  Zbigniew Testowski\n",
        "reserved label": "EMAIL  Zbigniew Testowski\n",
        "duplicate label": "PERSON_A  Zbigniew\nPERSON_A  Testowski\n",
    }

    def test_every_refusal_of_the_file_names_a_line_and_never_its_text(self):
        for case, text in self.BAD.items():
            with self.subTest(case):
                _clean()
                _write_terms(text)
                out = _run_main("post-tool", {"hook_event_name": "PostToolUse", "tool_name": "Bash",
                                              "session_id": "S1", "tool_input": {"command": "cat notes.txt"},
                                              **CLAUDE, "tool_response": {"stdout": "Zbigniew Testowski",
                                                                          "stderr": ""}})
                self.assertIn("terms.txt", out, "the hook fails closed and names the file")
                self.assertNoTerm(out, "the hook answer")
                self.assertNoTerm(_home_text(), "a file of the home")
                self.assertNoTerm(_cli("status"), "status")


if __name__ == "__main__":
    unittest.main()
