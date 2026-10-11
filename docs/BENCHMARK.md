# Rule benchmark: design

How the detection rules are measured against public labelled datasets, and how a proposed rule
change is judged. The work is TASK-11 and its subtasks in `backlog/`. Nothing here ships with the
plugin: `bench/` is developer-only, and the datasets never enter the repository.

## Purpose

- Score the rules as they are: precision and recall per dataset and per type, and the rules that
  never fire.
- Score a proposed rule change (a *mutation*) against that baseline, and accept it only when no
  dataset gets worse.
- Later, let an agent propose mutations from the misses and false alarms.
- Anyone, the upstream owner included, can run all of it on their own machine: one setup command,
  one run command (`bench/README.md`).

## Layout

| where | what |
|---|---|
| `bench/` (repo, developer-only) | a uv project of its own (`bench/pyproject.toml`: pyarrow, datasets); the adapters, the setup, the runner. The plugin itself stays free of dependencies. |
| `$MAISECRETS_BENCH_DATA` (default `~/.cache/maisecrets-bench`) | the downloads, the parquet files, the manifest, the run results. Never under the repository; `scripts/scan_tree.py` never sees it. |
| `../CredData`, `../text-anonymization-benchmark` | existing clones are used in place when the setup is given their path. |

The detector runs in a temp maisecrets home (`MAISECRETS_HOME`), never the real store.

## Datasets

| dataset | unit | gold | role |
|---|---|---|---|
| Samsung CredData | a file; gold per line (`meta/*.csv`: `GroundTruth` T/F/X, value span) | 15,753 T, 48,061 F, 4,082 X lines | precision and recall for secrets; values obfuscated with their shape kept |
| TAB (ECHR court texts) | a document; spans from two annotators | `DIRECT`/`QUASI`/`NO_MASK` per mention | precision on legal prose; out-of-scope coverage |
| ai4privacy `pii-masking-300k` | a record; `privacy_mask` spans | PII labels, six languages | PII: precision and recall |
| Gretel `synthetic_pii_finance_multilingual` | a document; `pii_spans` | finance PII and credentials, several languages | PII and secrets in finance text |

Each adapter notes the dataset's licence. The setup downloads; no derived file is published.

## One schema

One parquet file per dataset, one row per sample:

| column | type | meaning |
|---|---|---|
| `dataset` | str | `creddata`, `tab`, `ai4privacy`, `gretel` |
| `sample_id` | str | stable id within the dataset |
| `group_id` | str | the source that ties samples together: CredData repo, TAB document, record id |
| `language` | str | ISO 639-1, or `und` |
| `text` | str | the full text the detector scans |
| `spans` | list of struct | gold spans: `start`, `end` (characters), `label` (the dataset's own), `maisecrets_type` (a type, or `OUT_OF_SCOPE`), `gold` (`pos`, `neg`, `uncertain`) |
| `lines` | list of struct, CredData only | per labelled line: `line` (1-based), `gold`, `maisecrets_type` |
| `split` | str | `dev` or `check` (below) |

The label table of each dataset is explicit (`bench/labels/<dataset>.toml`). A label that is not in
it stops the setup: every new label is a decision, never a default.

## What counts

- **In scope** is what maisecrets claims: `SECRET`, `EMAIL`, `PHONE`, `IBAN`, `CARD`, `IP` and the
  region PII types (`DE_TAX_ID`, `DE_PASSPORT`, …). Names, places, dates, organisations and free
  numbers such as a court case number have no shape maisecrets claims; they are `OUT_OF_SCOPE`
  (only `terms.txt` covers them).
- **True positive:** a detection that overlaps an in-scope `pos` span (any overlap).
- **False negative:** an in-scope `pos` span that no detection overlaps.
- **False positive:** a detection that overlaps no gold span with `pos` at all, in scope or not.
  Redacting a name that maisecrets does not claim is no error.
- `uncertain` spans and CredData `X` lines are left out of every count.
- The headline is *redacted or not*. A type mismatch (a `SECRET` hit on a span the gold calls an
  e-mail) is a true positive and is listed in a confusion table beside it.
- **Out-of-scope coverage** (how many out-of-scope `pos` spans a detection overlaps) is reported
  for information: it shows what `terms.txt` would have to carry.

### CredData

The whole file is scanned, so a rule that looks across lines (the AWS secret within a few lines
of its `AKIA…` id, a `password =` label) sees what it sees in real use. Each detection is placed
by its line: on a `T` line it is a true positive, on an `F` line a false positive, on an `X` line
nothing. A detection on a line with no label counts as **unreviewed**, reported as hits per 1,000
lines (the measure of `scripts/measure_false_alarms.py`) and not in precision: the dataset never
said those lines are clean. A `T` line no detection touches is a false negative. CredData's `F`
lines are near misses chosen by detectors, so its precision is pessimistic by design.

The values are obfuscated with their shape kept; a checksum or entropy rule can behave a little
differently than on the real value. The report says so.

### TAB

A mention is `pos` when **either** annotator marked it `DIRECT` or `QUASI` (the union), `neg`
when both marked it `NO_MASK`. The union keeps a detection on something one annotator wanted
hidden from counting as a false alarm. TAB has almost no in-scope `pos` spans, so it is scored
for precision, and for out-of-scope coverage.

### Regions

The PII rules depend on the configured regions (`maisecrets/regions.py`). Each sample runs with
`generic` plus the regions of its language (German text: `de`; Italian: `it`; …), so a country's
rules never run on another country's text. Samples are grouped by language and each group runs
with its own config.

## Metrics

Per dataset, per type, per split, and per rule:

- TP, FP, FN (and CredData's unreviewed rate), precision, recall, F1.
- **The dataset score:** F1 where the dataset has in-scope `pos` spans; precision where it has none
  (TAB).
- **The overall score:** the mean of the dataset scores, each dataset weighted equally, because each
  stands for a different use (code, legal text, general PII, finance).
- Hits per rule; the **rules that never fire** on any dataset are listed for possible removal.
- Where a rule has a score (Presidio's score, an entropy threshold, a context word), precision-recall
  curves and AUC (TASK-11.11); a rule without one is a single point, and the report says n/a.

## Judging a change

A mutation (add, disable or replace a rule, change a threshold or a word list) is applied inside
the bench, never by editing the project, and scored against the baseline on the same data.

- **Inclusion:** on every dataset, precision and recall are each equal to or better than the
  baseline. The counts are exact, so there is no noise to allow for.
- **Ranking:** accepted mutations are ordered by the change of the overall score (equal weights).
- A rule that never fires is flagged, not removed: removal is a mutation like any other.

## Dev and check: no folds

Scoring a rule set is a count, not a statistical estimate, so there are no k folds and the scores
a person reads are on the full data. The one risk a split guards against is overfitting by the
author of a rule: an agent that reads particular misses can write a pattern that matches those
tokens and nothing else. So each dataset has one fixed split, by `group_id`, so that one repository
or document never lies on both sides:

- **dev** (about 70%): the misses and false alarms an agent may read.
- **check** (about 30%): only the totals. An agent's mutation must pass the inclusion rule on dev
  and on check.

A change written by a person is judged on all of the data. The split is deterministic (a hash of
`group_id` with a fixed salt), so it is the same on every machine.

## Error export

The misses and false alarms of a run go to a local file for review: rule, type, dataset, split and
a masked context (the shape of the value: letters as `a`/`A`, digits as `9`; the label words before
it). Never a value: the report and the export are what may be shared. A test checks that no gold
value appears in either.

## Hygiene

- No dataset file, value or parquet file enters the repository.
- Logs, reports and exports hold shapes and counts only.
- The detector runs with a temp maisecrets home.
- The bench is developer-only: `tests/test_release_tree.py` and `scripts/build_release_tree.py`
  keep it out of the release.

## Out of scope for now

- A dataset of our own for `terms.txt`.
- Speed tuning beyond running the samples in parallel; `--limit` with a fixed seed takes a sample
  of a large dataset for a quick run.
