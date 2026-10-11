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
A second run with the same versions builds nothing.

## Run

```bash
uv run --project bench python bench/run.py                      # every dataset, all cores (about 4 minutes)
uv run --project bench python bench/run.py --only gretel --limit 2000
```

It writes `<data>/runs/<time>/report.md` and `metrics.json`: per dataset, type, split and rule the counts,
precision, recall, F1, the share of clean samples and the dataset score, the equal-weight overall score, and
the rules that never fired. Counts, rates and rule ids only, never a value.

## Is each dataset worth keeping

```bash
uv run --project bench python bench/usefulness.py        # on the newest full run
```

Drops each of the 30 most-firing rules in turn and reports scope, saturation, discrimination and overlap per
dataset, with a keep or drop-candidate verdict (`usefulness.md` in the run).

## Judging a rule change

```bash
uv run --project bench python bench/mutate.py bench/mutations/*.toml --guard tab
```

A mutation file disables, changes or adds rules (format in `maisecrets_bench/mutation.py`); it is applied inside
the bench only. Each is judged against the newest full run: accepted when no dataset gets worse in recall,
precision or clean samples, ranked by the change of the mean score of the scored datasets. A `--guard` dataset
must not get worse but has no weight. A mutation that only disables rules re-runs just the samples where they
fired (seconds); any other re-runs everything (minutes).

## Reviewing the errors

```bash
uv run --project bench python bench/errors.py              # dev split of the newest run
```

Writes `errors-dev.jsonl` and `errors-dev.md` into the run: false positives by rule and misses by type, with
shapes and the common words before them. Values, names and rare words are masked (docs/BENCHMARK.md).
