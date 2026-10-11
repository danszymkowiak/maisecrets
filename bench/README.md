# maisecrets rule benchmark

Measures the detection rules against public labelled datasets: precision, recall and F1 per dataset, type and
rule, the rules that never fire, and whether a proposed rule change helps without hurting any dataset. The design
and every scoring decision are in `docs/BENCHMARK.md`. This folder is developer-only: it is not part of the
plugin release, and the plugin needs nothing from it.

## Requirements

- [uv](https://docs.astral.sh/uv/) and git. uv installs the bench's own Python packages (pyarrow, datasets) into
  `bench/.venv`; the plugin stays free of dependencies.
- About 1 GB of disk for Gretel, TAB and the parquet files; CredData needs about 15 GB more.
- The data lives outside the repository: `$MAISECRETS_BENCH_DATA`, default `~/.cache/maisecrets-bench`. A
  directory inside the repository is refused.

## Quick start

From the repository root:

```bash
uv run --project bench python -m unittest discover -s bench/tests   # the bench's own tests, a few seconds
uv run --project bench python bench/setup.py                         # TAB and Gretel; CredData needs a path
uv run --project bench python bench/run.py                           # the baseline, about 4 minutes on 16 cores
uv run --project bench python bench/usefulness.py                    # is each dataset worth keeping
uv run --project bench python bench/mutate.py bench/mutations/*.toml --guard tab
uv run --project bench python bench/errors.py                        # false positives and misses, masked
```

## Datasets

| dataset | what | licence | how setup gets it |
|---|---|---|---|
| CredData (Samsung) | 11,030 source files, 15,753 credentials and 48,061 near misses, values obfuscated | Apache-2.0 tooling, each file its project's licence | you clone `https://github.com/Samsung/CredData` and run its `download_data.py --data_dir data` (hours), then `--creddata <path>` |
| TAB | 1,268 ECHR court decisions, identifiers marked by two annotators | MIT | cloned into the data directory, or `--tab <path>` |
| Gretel synthetic_pii_finance_multilingual | 55,940 finance documents in 7 languages | Apache-2.0 | downloaded from Hugging Face |
| ai4privacy pii-masking-300k | not wired: academic and non-commercial use only | AI4Privacy licence | — |

Each dataset becomes `<data>/parquet/<dataset>.parquet` in one schema, with a dev or check split by source.
`manifest.json` records the versions and counts; a second setup run with the same versions builds nothing.
`--only creddata,tab` limits the setup to some datasets.

## Commands

| command | writes | what it tells |
|---|---|---|
| `bench/run.py [--only …] [--limit N]` | `<data>/runs/<time>/report.md`, `metrics.json`, `detections.parquet` | per dataset, type, split and rule: counts, precision, recall, F1, share of clean samples, the dataset score and the equal-weight mean; rules that never fired |
| `bench/usefulness.py [--run …]` | `usefulness.md` in the run | per dataset: in-scope share, saturation, rules firing only there, how many probes (dropping a top rule) move its score, overlap with the others; a keep or drop-candidate verdict |
| `bench/mutate.py <files> [--guard …]` | `<data>/mutations/<time>/report.md`, `results.json` | each rule change accepted (no dataset worse in recall, precision or clean samples) or rejected with the reason, ranked by the change of the mean score |
| `bench/errors.py [--split dev]` | `errors-dev.md`, `errors-dev.jsonl` in the run | false positives by rule and misses by type, by shape and the common words before them |

## A rule change

A mutation is a TOML file (format in `maisecrets_bench/mutation.py`): disable a rule, set fields of one (regex,
keywords, entropy, score, context), or add one. It is applied to a copy of the rule list inside the bench; the
plugin is not edited. A mutation that only disables rules re-runs just the samples where those rules fired, in
seconds; any other re-runs everything. `bench/mutations/` holds the first candidates, from the probes.

## What may be shared

`report.md`, `usefulness.md`, the mutation `report.md` and `errors-*.md` hold counts, rates, rule ids, shapes
and common words only: they may go into an issue. The parquet files and `detections.parquet` stay local: the
first hold the datasets, the second positions into them.
