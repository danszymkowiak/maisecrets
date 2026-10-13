"""The plugin's detector, imported for the bench with a temp maisecrets home: the bench never touches the real
store (CLAUDE.md). Import this module before anything from `maisecrets`."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from .paths import REPO


def _isolate() -> Path:
    """A fresh home with the plaintext test store, unless the caller already chose one that is not the real one."""
    set_home = os.environ.get("MAISECRETS_HOME")
    if set_home and Path(set_home).expanduser().resolve() != (Path.home() / ".maisecrets").resolve():
        return Path(set_home)
    home = Path(tempfile.mkdtemp(prefix="maisecrets-bench-home-"))
    (home / "config.json").write_text(json.dumps({"backend": "jsonfile", "allow_plaintext_store": True}))
    os.environ["MAISECRETS_HOME"] = str(home)
    return home


HOME = _isolate()
# the maisecrets checkout whose detector is measured: this one, or another one, such as a worktree of the version the
# fork started from (user, 2026-10-14). Only a plain run works with an older one: mutations need the newer API
DETECTOR_REPO = Path(os.environ.get("MAISECRETS_BENCH_DETECTOR") or REPO).expanduser().resolve()
if str(DETECTOR_REPO) not in sys.path:
    sys.path.insert(0, str(DETECTOR_REPO))

from maisecrets import detect  # noqa: E402

_TYPES: frozenset[str] | None = None


def all_regions() -> tuple[str, ...]:
    """Every region the vendored Presidio rules know, `generic` included."""
    recs = json.loads((DETECTOR_REPO / "maisecrets" / "rules" / "presidio.json").read_text(encoding="utf-8"))
    regional = getattr(detect, "REGIONAL_RULES", ())     # an older maisecrets has no regional rules
    return tuple(sorted({detect.presidio_region(r["id"]) for r in recs["recognizers"]}
                        | {d["region"] for d in regional}))


OLDER = DETECTOR_REPO != REPO.resolve()


def unknown_type(t: str) -> bool:
    """Is t a type the bench's own tables name in error? Measuring another checkout, a type it does not know is
    expected (it finds none of them: an older maisecrets lacks the fork's CH_AHV), so nothing is unknown then."""
    return not OLDER and t not in known_types()


def known_types() -> frozenset[str]:
    """Every type the detector can report, over all regions: what a label table may map to."""
    global _TYPES
    if _TYPES is None:
        _TYPES = frozenset({r.type for r in detect._load_presidio(all_regions())}
                           | {r.type for r in getattr(detect, "_load_regional", lambda regions: [])(all_regions())}
                           | {r.type for r in detect._load_own()} | detect.SECRET_TYPES)
    return _TYPES


def rule_index() -> dict:
    """Every rule of every region by id: type, regex and the fields a mutation can set. What an agent reads before it
    proposes a change; the rule sets are public (Betterleaks with the carried gitleaks rules, Presidio, detect-secrets,
    the plugin's own)."""
    rules = (detect._load_own() + detect._load_detect_secrets(("en", "de")) + detect._load_betterleaks()
             + detect._load_regional(all_regions()) + detect._load_presidio(all_regions()))
    out = {}
    for r in rules:
        out.setdefault(r.id, {"type": r.type, "regex": r.regex.pattern, "keywords": list(r.keywords),
                              "entropy": r.entropy, "score": r.score, "context": list(r.context),
                              "require_context": r.require_context, "validator": r.validator})
    return out
