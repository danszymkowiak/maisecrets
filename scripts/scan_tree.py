#!/usr/bin/env python3
"""The repository must not carry a value the detector would hide: scan every file on its own.

The CI job used to pipe all files into one `maisecrets.cli scan`. A PNG in the tree crashed the
strict decode without output, which read as "nothing found" for weeks, and one long stream let
a label at the end of one file pair with the first word of the next (2026-09-27). Each file is
read as bytes, decoded with replacement, and scanned alone; a hit prints the path, the line and
the rule, never the value.

In a git checkout the files are those git would carry: tracked and untracked ones, not the ignored
ones (private notes in an ignored folder failed every push, 2026-10-12). Outside git, or when git
fails (a checkout of another owner, as root in CI), every file is scanned.

    python3 scripts/scan_tree.py [ROOT]
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from maisecrets import detect  # noqa: E402

SKIP = {".git", ".claude", "__pycache__", "dist", "node_modules", ".venv"}   # .venv: installed packages (bench/)
VENDORED = ("maisecrets/rules/",)   # the rule sets carry secret shapes by design


def _git_files(root: Path) -> list[str] | None:
    """The paths git would carry under root, relative to it; None when root is no checkout or git fails."""
    # without GIT_*: inside a git hook GIT_DIR names the repository being committed, not the one at root
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        r = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                           cwd=root, capture_output=True, timeout=60, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return [p for p in r.stdout.decode("utf-8", errors="surrogateescape").split("\0") if p]


def _walk_files(root: Path) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        out += [(Path(dirpath) / name).relative_to(root).as_posix() for name in filenames]
    return out


def main(argv: list[str]) -> int:
    root = Path(argv[0]) if argv else ROOT
    hits, files = 0, 0
    listed = _git_files(root)
    for rel in sorted(_walk_files(root) if listed is None else listed):
        path = root / rel
        if rel.startswith(VENDORED) or set(Path(rel).parts) & SKIP or not path.is_file():
            continue
        raw = path.read_bytes()
        if b"\x00" in raw[:4096]:
            continue
        files += 1
        text = raw.decode("utf-8", errors="replace")
        for m in detect.scan(text):
            if m.type == "SECRET":
                hits += 1
                print(f"{rel}:{text.count(chr(10), 0, m.start) + 1}: {m.kind}")
    print(f"scanned {files} files: {hits} secret-shaped value(s)")
    if files == 0:
        print("no file was scanned: the scan proves nothing")
        return 1
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
