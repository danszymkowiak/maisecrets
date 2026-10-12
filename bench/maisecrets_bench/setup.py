"""Build the benchmark data (docs/BENCHMARK.md): each source becomes <out>/<dataset>.parquet and an entry in
<out>/manifest.json with its version and counts. Gold of a checksummed type is checked on the way (validgold.py); a
source whose version and gold revision are already in the manifest, with its file present, is not built again."""
from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from . import exceptions, schema, split, validgold
from .labels import load as load_table
from .paths import BenchError, data_dir
from .schema import Sample


@dataclass
class Source:
    name: str
    version: Callable[[], str]
    build: Callable[[], Iterator[Sample]]
    stats: Callable[[], dict]


def _manifest(out: Path) -> dict:
    p = out / "manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"datasets": {}}


def run(sources: list[Source], out: Path, log: Callable[[str], None] = lambda s: None,
        exceptions_file: Path = exceptions.FILE) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    manifest = _manifest(out)
    entries = exceptions.load(exceptions_file)
    for src in sources:
        version = src.version()
        known = manifest["datasets"].get(src.name, {})
        target = out / f"{src.name}.parquet"
        reviewed = exceptions.digest(entries, src.name)
        if (known.get("version") == version and known.get("gold") == validgold.REVISION
                and known.get("exceptions") == reviewed and target.exists()):
            log(f"{src.name}: up to date ({version})")
            continue
        log(f"{src.name}: building ({version})")
        rows, gold = validgold.mark(list(src.build()))
        rows, applied = exceptions.apply(rows, entries)
        tmp = target.with_suffix(".parquet.tmp")
        schema.write(rows, tmp)
        os.replace(tmp, target)
        spans = Counter(sp.gold for s in rows for sp in s.spans)
        manifest["datasets"][src.name] = {
            "version": version, "samples": len(rows), "spans": dict(sorted(spans.items())),
            "split": dict(sorted(Counter(s.split for s in rows).items())), **src.stats(),
            "gold": validgold.REVISION, "gold_check": gold.get(src.name, {}),
            "exceptions": reviewed, "exceptions_applied": applied}
        log(f"{src.name}: {len(rows)} samples, spans {dict(spans)}")
    manifest["split_salt"] = split.SALT
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _git_rev(path: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        raise BenchError(f"{path}: not a git checkout; give the path of a clone") from None


def creddata_source(path: Path) -> Source:
    from .adapters import creddata
    if not (path / "meta").is_dir():
        raise BenchError(f"{path}: no CredData checkout there. Clone https://github.com/Samsung/CredData, run "
                         "`python download_data.py --data_dir data` in it (it fetches the source repositories and "
                         "takes a while), then pass --creddata <path>")
    return Source("creddata", lambda: _git_rev(path), lambda: creddata.samples(path, load_table("creddata")),
                  lambda: {})


TAB_URL = "https://github.com/NorskRegnesentral/text-anonymization-benchmark.git"


def tab_source(path: Path | None, cache: Path) -> Source:
    from .adapters import tab
    if path is None:
        path = cache / "text-anonymization-benchmark"
        if not path.exists():
            subprocess.run(["git", "clone", "--depth", "1", TAB_URL, str(path)], check=True)
    return Source("tab", lambda: _git_rev(path), lambda: tab.samples(path, load_table("tab")), lambda: {})


def gretel_source(cache: Path) -> Source:
    from .adapters import gretel
    stats = gretel.Stats()

    def version() -> str:
        from huggingface_hub import HfApi
        return f"{HfApi().dataset_info(gretel.HF_ID).sha}:{gretel.REVISION}"

    return Source("gretel", version,
                  lambda: gretel.samples(gretel.records(str(cache / "hf")), load_table("gretel"), stats),
                  lambda: {"dropped": stats.dropped, "below_quality_90": stats.low_quality})


def synthetic_source() -> Source:
    """Generated tool output from a fixed seed (maisecrets_bench/adapters/synthetic.py): nothing is fetched."""
    from .adapters import synthetic
    return Source("synthetic", synthetic.version, lambda: synthetic.samples(load_table("synthetic")), lambda: {})


def nemotron_source(cache: Path) -> Source:
    """nvidia/Nemotron-PII, CC-BY-4.0 (maisecrets_bench/adapters/nemotron.py): the test split, pinned to a revision."""
    from .adapters import nemotron
    stats = nemotron.Stats()
    sha: dict = {}

    def version() -> str:
        from huggingface_hub import HfApi
        sha["v"] = HfApi().dataset_info(nemotron.HF_ID).sha
        return f"{sha['v']}:{nemotron.REVISION}"

    return Source("nemotron", version,
                  lambda: nemotron.samples(nemotron.records(str(cache / "hf"), sha.get("v")), load_table("nemotron"),
                                           stats),
                  lambda: {"dropped": stats.dropped, "licence": "CC-BY-4.0, NVIDIA"})


def mendeley_source(cache: Path) -> Source:
    """Mendeley's synthetic financial documents, CC BY 4.0 (maisecrets_bench/adapters/mendeley.py): both
    spreadsheets, downloaded once and checked against the sha256 the API gives; the version is those hashes."""
    from .adapters import mendeley
    stats = mendeley.Stats()
    listing: list = []

    def version() -> str:
        listing[:] = mendeley.files()
        return ":".join([f["sha256"][:12] for f in sorted(listing, key=lambda f: f["name"])] + [mendeley.REVISION])

    def build() -> Iterator[Sample]:
        for path in mendeley.download(listing, cache / "mendeley"):
            yield from mendeley.samples(mendeley.read_xlsx(path), load_table("mendeley"), stats)

    return Source("mendeley", version, build, lambda: {"dropped": stats.dropped, "licence": "CC BY 4.0"})


def findocs_source() -> Source:
    """Generated tax and financial documents from a fixed seed (maisecrets_bench/adapters/findocs.py), scored."""
    from .adapters import findocs
    return Source("findocs", findocs.version, lambda: findocs.samples(load_table("findocs")), lambda: {})


def ai4privacy_source(cache: Path) -> Source:
    """Opt-in and local: academic and non-commercial use only (maisecrets_bench/adapters/ai4privacy.py)."""
    from .adapters import ai4privacy
    stats = ai4privacy.Stats()

    def version() -> str:
        from huggingface_hub import HfApi
        return HfApi().dataset_info(ai4privacy.HF_ID).sha

    return Source("ai4privacy", version,
                  lambda: ai4privacy.samples(ai4privacy.records(str(cache / "hf")), load_table("ai4privacy"), stats),
                  lambda: {"dropped": stats.dropped, "licence": "academic and non-commercial use only; local"})


def default_out() -> Path:
    return data_dir() / "parquet"
