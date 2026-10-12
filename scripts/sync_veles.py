#!/usr/bin/env python3
"""Vendor the Veles rules that Kingfisher carries for providers Betterleaks lacks (TASK-19.5).

Usage: uv run --with pyyaml python scripts/sync_veles.py v2.11.1
Reads crates/kingfisher-rules/generated/rules/veles.yml and provenance.json of mongodb/kingfisher at the tag as data
(Google's Veles detectors from OSV-SCALIBR, Apache-2.0, converted to regexes by Kingfisher, Apache-2.0) and writes
maisecrets/rules/veles.json, LICENSE-kingfisher and VELES_VERSION. Nothing upstream runs. Validation and revocation
are dropped: the threat model sends no secret anywhere to test it. Which rules load is decided in rules/overrides.txt
(a rule Betterleaks already covers, or one the bench rejected, is off there with its reason).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KEEP = {"id", "name", "pattern", "betterleaks_secret_group", "path", "references"}
DROPPED = {"validation", "revocation", "visible", "depends_on_rule"}
BASE = "https://raw.githubusercontent.com/mongodb/kingfisher/{tag}/"
RULES_PATH = "crates/kingfisher-rules/generated/rules/veles.yml"
PROVENANCE_PATH = "crates/kingfisher-rules/generated/provenance.json"


class SyncError(Exception):
    pass


def convert(data: dict, tag: str, scalibr: str) -> dict:
    """veles.yml (parsed) -> the JSON the detector reads. Anything unknown stops the sync, naming the rule."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from maisecrets.detect import _re2_to_python
    rules = []
    for r in data.get("rules", []):
        rid = r.get("id", "?")
        extra = set(r) - KEEP - DROPPED
        if extra:
            raise SyncError(f"{rid}: field(s) {', '.join(repr(x) for x in sorted(extra))} unknown")
        if not r.get("pattern"):
            raise SyncError(f"{rid}: no pattern")
        try:
            re.compile(_re2_to_python(r["pattern"]))
        except re.error as exc:
            raise SyncError(f"{rid}: pattern does not compile in Python ({exc})") from None
        out = {"id": rid, "name": r.get("name", ""), "regex": r["pattern"],
               "secret_group": int(r.get("betterleaks_secret_group") or 0)}
        if r.get("path"):
            out["path"] = r["path"]
        if r.get("references"):
            out["source"] = r["references"][0]
        rules.append(out)
    return {"kingfisher": tag, "osv_scalibr": scalibr,
            "source": f"Google Veles (OSV-SCALIBR {scalibr}, Apache-2.0) as converted by Kingfisher {tag} "
                      "(Apache-2.0, rules/LICENSE-kingfisher)", "rules": rules}


def _scalibr_revision(veles_yml: str) -> str:
    m = re.search(r"google/osv-scalibr/([0-9a-f]{40})/", veles_yml)
    if not m:
        raise SyncError("veles.yml names no pinned OSV-SCALIBR revision")
    return m.group(1)


def main(argv: list[str]) -> int:
    import urllib.request
    tag = argv[0] if argv else None
    if not tag or not re.fullmatch(r"v\d+\.\d+\.\d+", tag):   # it becomes part of a URL
        print("usage: sync_veles.py vX.Y.Z")
        return 2
    import yaml   # uv run --with pyyaml: the parsed data is all the tests need
    got = {}
    for src in (RULES_PATH, PROVENANCE_PATH, "LICENSE"):
        with urllib.request.urlopen(BASE.format(tag=tag) + src, timeout=60) as r:
            got[src] = r.read().decode("utf-8")
    try:
        data = convert(yaml.safe_load(got[RULES_PATH]), tag, _scalibr_revision(got[RULES_PATH]))
    except SyncError as exc:
        print(f"sync_veles: {exc}", file=sys.stderr)
        return 1
    dst = Path(__file__).resolve().parent.parent / "maisecrets" / "rules"
    (dst / "veles.json").write_text(json.dumps(data, ensure_ascii=False, indent=0, sort_keys=True) + "\n",
                                    encoding="utf-8")
    (dst / "LICENSE-kingfisher").write_text(got["LICENSE"], encoding="utf-8")
    (dst / "VELES_VERSION").write_text(tag + "\n")
    print(f"vendored {len(data['rules'])} Veles rules from Kingfisher {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
