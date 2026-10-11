# maisecrets rule benchmark

Measures the detection rules against public labelled datasets. The design is in
`docs/BENCHMARK.md`; this folder is developer-only and never part of the plugin release.

```bash
uv run --project bench python -m unittest discover -s bench/tests   # the bench's own tests
```

The data lives outside the repository: `$MAISECRETS_BENCH_DATA`, default `~/.cache/maisecrets-bench`.

## Setup

```bash
uv run --project bench python bench/setup.py --creddata ../CredData --tab ../text-anonymization-benchmark
```

- CredData: clone `https://github.com/Samsung/CredData` and run its `download_data.py` first (it fetches
  the source repositories; hours). Without `--creddata` it is skipped.
- TAB: an existing clone with `--tab`, or it is cloned into the data directory.
- Gretel: downloaded from Hugging Face into the data directory.

Each dataset becomes `<data>/parquet/<dataset>.parquet`; `manifest.json` records its version and counts.
A second run with the same versions builds nothing. The run command follows with TASK-11.9.
