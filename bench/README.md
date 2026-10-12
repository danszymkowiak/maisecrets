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
uv run --project bench python bench/setup.py                         # all but CredData, which needs --creddata <path>
uv run --project bench python bench/run.py                           # the baseline, about 4 minutes on 16 cores
uv run --project bench python bench/usefulness.py                    # is each dataset worth keeping
uv run --project bench python bench/mutate.py bench/mutations/*.toml --guard tab
uv run --project bench python bench/errors.py                        # false positives and misses, masked
uv run --project bench python bench/audit.py                         # gold that fails a validity rule, masked
uv run --project bench python bench/recommend.py --mutations <dir>   # one page per round for the plugin's owner
```

## Datasets

| dataset | what | licence | how setup gets it |
|---|---|---|---|
| CredData (Samsung) | 11,030 source files, 15,753 credentials and 48,061 near misses, values obfuscated | Apache-2.0 tooling, each file its project's licence | you clone `https://github.com/Samsung/CredData` and run its `download_data.py --data_dir data` (hours), then `--creddata <path>` |
| TAB | 1,268 ECHR court decisions, identifiers marked by two annotators | MIT | cloned into the data directory, or `--tab <path>` |
| Gretel synthetic_pii_finance_multilingual | 41,932 finance documents in 7 languages (records below quality 90 left out); structured formats scored apart | Apache-2.0 | downloaded from Hugging Face |
| NVIDIA Nemotron-PII | 100,000 English documents of 50+ industries (test split), us and intl locale, structured and unstructured | CC BY 4.0 (attribution: NVIDIA) | downloaded from Hugging Face |
| Mendeley synthetic financial documents (doi 10.17632/tzrjx692jy.1) | 45,030 auditor reports, tax filings and transaction confirmations | CC BY 4.0 (attribution: the dataset's authors on Mendeley Data) | downloaded through Mendeley's public API, checked against its sha256 |
| findocs (generated) | 3,300 Swiss salary certificates and tax returns (de, fr), bank statements, MT940 and CSV exports, QR-bills, US W-2 and 1099 forms, invoices | ours | generated from a fixed seed; nothing downloaded |
| synthetic tool output | 3,000 generated terminal outputs (printenv, git diff, kubectl, lockfiles, ...); a guard, not in the mean | ours | generated from a fixed seed; nothing downloaded |
| ai4privacy pii-masking-300k | 225,405 records in 6 languages | **academic and non-commercial use only** (AI4Privacy licence) | opt-in: `--with-ai4privacy`, for your own local measurement |
| The Learning Agency Lab - PII Data Detection (Kaggle) | about 6,800 student essays, labelled by people | **competition data: your Kaggle account must accept the competition rules**; licence not yet recorded | opt-in: `--with-kaggle-pii`, local, a guard |

Each dataset becomes `<data>/parquet/<dataset>.parquet` in one schema, with a dev or check split by source.
`manifest.json` records the versions and counts; a second setup run with the same versions builds nothing.
`--only creddata,tab` limits the setup to some datasets.

**ai4privacy and the licence.** Its licence allows academic and non-commercial use only and needs a written licence
from AI4Privacy for derivative works. The bench builds it only on request, every report that includes it says so,
and its results stay out of anything sent upstream. **If you maintain maisecrets, get AI4Privacy's permission
(licensing@ai4privacy.com) before you run the bench with it.**

**The Kaggle competition data.** Kaggle hands it out only to an account that has accepted the competition's
rules (kaggle.com/competitions/pii-detection-removal-from-educational-data, Join Competition). Put your
own API token into `KAGGLE_API_TOKEN` (the environment, or `.env` at the repository root, which git
ignores); the setup passes it to the Kaggle CLI and never prints it. Until its licence is recorded here
(TASK-11.36) its results stay local, like ai4privacy's.

**TAB** was dropped after the first run (saturated and out of scope, `docs/BENCHMARK.md`); `--only tab` still
builds it.

## Commands

| command | writes | what it tells |
|---|---|---|
| `bench/run.py [--only …] [--limit N]` | `<data>/runs/<time>/report.md`, `metrics.json`, `detections.parquet` | per dataset, type, split and rule: counts, precision, recall, F1, share of clean samples, the dataset score and the equal-weight mean; rules that never fired |
| `bench/usefulness.py [--run …]` | `usefulness.md` in the run | per dataset: in-scope share, saturation, rules firing only there, how many probes (dropping a top rule) move its score, overlap with the others; a keep or drop-candidate verdict |
| `bench/mutate.py <files> [--guard …]` | `<data>/mutations/<time>/report.md`, `results.json` | each rule change accepted (no dataset worse in recall, precision or clean samples), accepted within tolerance (no dataset's score lower, recall at most 0.5 points lower; `--recall-tolerance`) or rejected with the reason, ranked by verdict and the change of the mean score |
| `bench/perturb.py [--only …] [--per-dataset 400]` | `<data>/perturb/<time>/report.md`, `results.json` | recall per dataset when every positive is rewritten by one transform (zero-width, soft hyphen, fullwidth, homoglyph, ANSI reset, CR, wrap, base64, hex, entity, escape, truncation) |
| `bench/loo.py [--baseline …]` | `<data>/loo/<time>/report.md`, `results.json`, `mutations/` | each rule that fired, disabled on its own and judged as `mutate.py` does: an accepted removal is a candidate, the rejected ones are the rules that earn their place |
| `bench/recommend.py --mutations <dirs> [--baseline …]` | `<data>/recommendations/<time>/recommendations.md` | one page per round: baseline per dataset, recall floors per type, the accepted rule changes with per-dataset deltas, the rejected ones with their reason, the rules that never fire, how to reproduce; no local-only dataset (ai4privacy), no value (TASK-11.14) |
| `bench/audit.py [--only …]` | `<data>/audit/<time>/report.md`, `results.json` | per dataset and type: positives that fail each candidate validity rule (`maisecrets_bench/audit.py`), with example shapes; what `validgold.py` and `bench/gold_exceptions.json` are chosen from (TASK-30) |
| `bench/errors.py [--split dev]` | `errors-dev.md`, `errors-dev.jsonl` in the run | false positives by rule and misses by type, by shape and the common words before them |

## A rule change

A mutation is a TOML file (format in `maisecrets_bench/mutation.py`): disable a rule, set fields of one (regex,
keywords, entropy, score, context, validator), or add one. Three fields try an idea the plugin does not have yet:
`validator = "bench:aba"` (a checksum in `maisecrets_bench/validators.py`), `allow = [regex]` (skip a value that
matches) and `filter = "bench:name"` (a function in `maisecrets_bench/filters.py` that also sees the text around
the value). It is applied to a copy of the rule list inside the bench; the
plugin is not edited. A mutation that only disables rules re-runs just the samples where those rules fired, in
seconds; any other re-runs everything. `bench/mutations/` holds the first candidates, from the probes.

## What may be shared

`report.md`, `usefulness.md`, the mutation `report.md` and `errors-*.md` hold counts, rates, rule ids, shapes
and common words only: they may go into an issue. The parquet files and `detections.parquet` stay local: the
first hold the datasets, the second positions into them.

## An agent round

```bash
uv run --project bench python bench/round.py brief                  # what an agent may read (dev only)
uv run --project bench python bench/round.py judge bench/mutations/round1/*.toml
```

The brief holds dev scores, the rules with the most false alarms and their definitions, the misses by type and
the mutation format, all masked. `judge` scores each proposal on dev and on check; its verdict is the worse of the
two, and of check only the verdict and the change of the mean come back. `bench/mutations/round1/` is
the first round, written from a brief.

## Curves for the rules with a score

```bash
uv run --project bench python bench/curves.py     # about 5 minutes; writes curves.md into the newest full run
```

Per gitleaks entropy rule: today's threshold, its precision and retained share, the area under the curve and the
best precision that keeps 90% of the rule's finds. Per Presidio context-gated rule: true and false positives with
the gate and without it.
