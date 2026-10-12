"""The Learning Agency Lab's PII Data Detection competition on Kaggle (TASK-11.36): about 6,800 student essays written
by people and labelled by people (student names, e-mail addresses, usernames, ID numbers, phone numbers, personal
URLs, street addresses). Not financial, but real text: it shows the artefacts generated datasets hide.

Opt-in (setup.py --with-kaggle-pii) and local: the data needs the user's own Kaggle account, whose holder accepts the
competition rules on kaggle.com first (the API answers 403 before that), and its licence is not yet recorded here.
The token comes from KAGGLE_API_TOKEN in the environment or the repository's .env (git-ignored); it is passed to the
Kaggle CLI and never printed. train.json holds per essay its tokens, a whitespace flag per token and a BIO label per
token; the text is rebuilt from the tokens and must equal full_text."""
from __future__ import annotations

import json
import os
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from ..labels import LabelTable
from ..paths import BenchError
from ..schema import Sample, Span
from ..split import split_of

DATASET = "kagglepii"
COMPETITION = "pii-detection-removal-from-educational-data"
REVISION = "bio1"           # part of the version: a change of the adapter or its table builds the parquet again
LABELS = ("NAME_STUDENT", "EMAIL", "USERNAME", "ID_NUM", "PHONE_NUM", "URL_PERSONAL", "STREET_ADDRESS")
LICENCE_NOTE = ("kagglepii: The Learning Agency Lab - PII Data Detection (Kaggle). Your own Kaggle account must "
                "accept the competition rules first; its data licence is not yet recorded (TASK-11.36), so the "
                "results stay local.")


@dataclass
class Stats:
    dropped: int = 0


def samples(records: Iterable[dict], table: LabelTable, stats: Stats | None = None) -> Iterator[Sample]:
    stats = stats if stats is not None else Stats()
    for r in records:
        starts, parts, at = [], [], 0
        for tok, ws in zip(r["tokens"], r["trailing_whitespace"]):
            starts.append(at)
            parts.append(tok + (" " if ws else ""))
            at += len(parts[-1])
        text = "".join(parts)
        if text != r["full_text"] or len(r["labels"]) != len(r["tokens"]):
            stats.dropped += 1
            continue
        spans, run = [], None             # run: [label, start, end]
        for i, lab in enumerate(r["labels"]):
            end = starts[i] + len(r["tokens"][i])
            if lab.startswith("I-") and run and run[0] == lab[2:]:
                run[2] = end
                continue
            if run:
                spans.append(run)
            run = [lab[2:], starts[i], end] if lab != "O" else None
        if run:
            spans.append(run)
        sid = str(r["document"])
        yield Sample(DATASET, sid, sid, "en", text,
                     [Span(a, b, label, table.type_of(label), "pos") for label, a, b in spans], split_of(DATASET, sid))


def token(repo: Path) -> str:
    """KAGGLE_API_TOKEN from the environment, else from repo/.env; never printed."""
    value = os.environ.get("KAGGLE_API_TOKEN")
    env = repo / ".env"
    if not value and env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, sep, val = line.strip().removeprefix("export ").partition("=")
            if sep and key.strip() == "KAGGLE_API_TOKEN":
                value = val.strip().strip("'\"")
    if not value:
        raise BenchError("kagglepii: no KAGGLE_API_TOKEN in the environment or .env (a Kaggle API token of your own)")
    return value


def download(cache: Path, repo: Path) -> Path:
    """train.json of the competition into cache/kagglepii, once. The token reaches only the CLI's environment."""
    out = cache / "kagglepii"
    target = out / "train.json"
    if target.is_file():
        return target
    out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "KAGGLE_API_TOKEN": token(repo)}
    r = subprocess.run(["uvx", "--quiet", "kaggle", "competitions", "download", COMPETITION, "-f", "train.json",
                        "-p", str(out)], env=env, capture_output=True, text=True, timeout=1800)
    if r.returncode:
        hint = (" (403: accept the competition rules with your Kaggle account first)" if "403" in r.stdout + r.stderr
                else "")
        raise BenchError(f"kagglepii: the download failed, exit {r.returncode}{hint}")
    for z in out.glob("*.zip"):
        with zipfile.ZipFile(z) as zf:
            zf.extract("train.json", out)
        z.unlink()
    if not target.is_file():
        raise BenchError("kagglepii: train.json is not in the download")
    return target


def records(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))
