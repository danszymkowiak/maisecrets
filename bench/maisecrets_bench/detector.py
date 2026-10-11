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
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from maisecrets import detect  # noqa: E402

_TYPES: frozenset[str] | None = None


def all_regions() -> tuple[str, ...]:
    """Every region the vendored Presidio rules know, `generic` included."""
    recs = json.loads((REPO / "maisecrets" / "rules" / "presidio.json").read_text(encoding="utf-8"))["recognizers"]
    return tuple(sorted({detect.presidio_region(r["id"]) for r in recs}))


def known_types() -> frozenset[str]:
    """Every type the detector can report, over all regions: what a label table may map to."""
    global _TYPES
    if _TYPES is None:
        _TYPES = frozenset({r.type for r in detect._load_presidio(all_regions())}
                           | {r.type for r in detect._load_own()} | detect.SECRET_TYPES)
    return _TYPES
