"""The dev/check split (docs/BENCHMARK.md, Dev and check: no folds): a hash of the dataset and the group, so one
repository or document never lies on both sides and every machine gets the same split."""
from __future__ import annotations

import hashlib

SALT = "maisecrets-bench-split-v1"
DEV_PERCENT = 70


def split_of(dataset: str, group_id: str) -> str:
    h = hashlib.sha256(f"{SALT}\0{dataset}\0{group_id}".encode("utf-8")).digest()
    return "dev" if int.from_bytes(h[:8], "big") % 100 < DEV_PERCENT else "check"
