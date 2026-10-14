"""The file system (TASK-34.6): the files of a tree, and the outputs written. Implements the Tree and OutputSink
ports."""
from __future__ import annotations

import os
from pathlib import Path


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def files_of(root: Path, recursive: bool) -> list[Path]:
    """The files of a tree in a fixed order (placeholders are numbered in it); symlinked folders are not entered."""
    if not recursive:
        return sorted(p for p in root.iterdir() if p.is_file() or p.is_symlink())
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        out += [Path(dirpath) / f for f in sorted(filenames)]
    return out


class LocalTree:
    def files(self, root: Path, recursive: bool) -> list[Path]:
        return files_of(root, recursive)

    def inside(self, path: Path, root: Path) -> bool:
        return _inside(path, root)

    def same(self, a: Path, b: Path) -> bool:
        return a.resolve() == b.resolve()

    def is_link(self, path: Path) -> bool:
        return path.is_symlink()


class LocalSink:
    def exists(self, path: Path) -> bool:
        return path.exists()

    def write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="": a CSV's line ends are its own (\r\n), and a line break in a quoted cell stays as it was
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
