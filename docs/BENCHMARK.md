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
| Samsung CredData | a file (or a window of a large one); a gold span per meta row (`meta/*.csv`: `GroundTruth` T/F/X) | 15,753 T, 48,061 F, 4,082 X rows | precision and recall for secrets; values obfuscated with their shape kept |
| TAB (ECHR court texts) | a document; spans from two annotators | `DIRECT`/`QUASI`/`NO_MASK` per mention | precision on legal prose; out-of-scope coverage |
| ai4privacy `pii-masking-300k` | a record; `privacy_mask` spans | PII labels, six languages | PII: precision and recall |
| Gretel `synthetic_pii_finance_multilingual` | a document; `pii_spans` | finance PII and credentials, several languages | PII and secrets in finance text |

Licences: CredData's tooling is Apache-2.0 and each file keeps its source project's licence
(CredData kept permissive ones); TAB is MIT; Gretel is Apache-2.0. ai4privacy allows academic and
non-commercial use only and needs a written licence for derivative works. **Decision, 2026-10-11
(user):** it is opt-in and local: the setup builds it only with `--with-ai4privacy`, for the user's
own non-commercial measurement. A report that goes upstream leaves it out, and the bench README tells
the plugin's owner to get AI4Privacy's permission (licensing@ai4privacy.com) before using it. The
setup downloads; no derived file is published.

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
- `uncertain` spans and CredData `X` rows are left out of every count.
- **A dataset judges only the types it annotates.** CredData labels credentials, so a detection of
  another type there (an e-mail address on a line it calls "not a credential") is neither right nor
  wrong: it is counted as *unjudged*. Gretel and TAB label personal data broadly and judge every type.
  (The probes found it: dropping the e-mail rule raised CredData's score.)
- The headline is *redacted or not*. A type mismatch (a `SECRET` hit on a span the gold calls an
  e-mail) is a true positive and is listed in a confusion table beside it.
- **Out-of-scope coverage** (how many out-of-scope `pos` spans a detection overlaps) is reported
  for information: it shows what `terms.txt` would have to carry.

### CredData

Each meta row is one gold span: its value (`ValueStart`/`ValueEnd` on a single line) or, when it
names no value, its lines. `T` is `pos`, `F` `neg`, `X` `uncertain`; so a credential counts once,
however many lines it covers (a PEM key spans dozens). The whole file is scanned, so a rule that
looks across lines (the AWS secret within a few lines of its `AKIA…` id, a `password =` label)
sees what it sees in real use. A file above 1 MiB (167 of 11,030 files, 745 of 969 MB) is cut into
windows of 50 lines on each side of its labelled lines, merged where they overlap.

A detection that overlaps a `pos` span is a true positive; one that overlaps no `pos` span but an
`F` span is a false positive. A detection that overlaps no labelled span counts as **unreviewed**,
reported as hits per 1,000 lines scanned (the measure of `scripts/measure_false_alarms.py`) and not
in precision: CredData never said the rest of a file is clean. This is the one difference from the
other datasets, where unlabelled text is negative. CredData's `F` rows are near misses chosen by
detectors, so its precision is pessimistic by design.

The values are obfuscated with their shape kept; a checksum or entropy rule can behave a little
differently than on the real value. The report says so.

### TAB

A mention is `pos` when **either** annotator marked it `DIRECT` or `QUASI` (the union), `neg`
when both marked it `NO_MASK`. The union keeps a detection on something one annotator wanted
hidden from counting as a false alarm. TAB has no in-scope `pos` spans, so it is scored by the
share of documents with no false alarm, and for out-of-scope coverage.

### Regions

The PII rules depend on the configured regions (`maisecrets/regions.py`). Each sample runs with
`generic` plus the regions of its language (German text: `de`; Italian: `it`; …), so a country's
rules never run on another country's text. Samples are grouped by language and each group runs
with its own config.

## Metrics

Per dataset, per type, per split, and per rule:

- TP, FP, FN (and CredData's unreviewed rate), precision, recall, F1.
- **The clean-sample rate:** the share of samples without a false positive.
- **The dataset score:** F1 where the dataset has in-scope `pos` spans; the clean-sample rate where it
  has none (TAB). Precision cannot serve there: with no true positive possible it is 0% at the first
  false alarm (the first baseline gave TAB 0% for 4 false alarms in 1,268 documents).
- **The overall score:** the mean of the dataset scores, each dataset weighted equally, because each
  stands for a different use (code, legal text, general PII, finance).
- Hits per rule; the **rules that never fire** on any dataset are listed for possible removal.
- Where a rule has a score, `bench/curves.py` re-runs the detector with the gates open (entropy thresholds
  at 0, context requirements off) and keeps each candidate's score. A gitleaks entropy rule gets a curve
  of precision over *retained* (the share of the rule's true positives at the lowest threshold that a
  threshold keeps), its area, and the point at today's threshold. A Presidio context gate is on or off,
  so it gets two points, with and without the gate. A rule without a score, or without a judged candidate,
  is n/a. The relaxed run lets a candidate take a span another rule would have claimed, so the curves are
  approximate, and a true positive there is any overlap with an in-scope positive, whatever its type.

## Is a dataset worth keeping

A dataset earns its weight only if it can tell a good rule change from a bad one. After the first
baseline run, each one is checked (TASK-11.15) and kept or dropped by the user:

- **Scope:** the share and the count of its gold positives that map to a maisecrets type. Mostly
  out of scope means it measures something maisecrets does not claim.
- **Saturation:** baseline precision and recall per type. Both near 1.0 leave no room to show an
  improvement, only a regression.
- **Discrimination:** how many rules fire on it, how many fire only there, and whether probe
  mutations (disabling each of the most-firing rules, moving a threshold) move its score at all.
- **Overlap:** a dataset whose score always moves exactly like another's adds no information.

A dropped dataset leaves the equal-weight mean; the decision and its numbers are recorded here.

**Decision, 2026-10-11 (user):** TAB is dropped. In the first full run it had no in-scope positives,
99.7% of its 1,268 documents had no false alarm (4 in 9.6 M characters), only 3 rules fired on it and
2 of 30 probes moved its score: saturated and out of scope. Its adapter stays (`--only tab`), but
setup and runs leave it out by default. CredData and Gretel stay: each has rules that fire only there
(21 and 40) and they moved together on only 16.7% of the probes.

## Judging a change

A mutation (add, disable or replace a rule, change a threshold or a word list) is applied inside
the bench, never by editing the project, and scored against the baseline on the same data.

- **Inclusion, strict (*accepted*):** on every dataset, precision, recall and the share of clean
  samples are each equal to or better than the baseline. The counts are exact, so there is no
  noise to allow for.
- **Inclusion with tolerance (*accepted within tolerance*):** not strict, but on every dataset the
  score does not fall and recall falls by at most 0.5 points (`--recall-tolerance`). Chosen
  2026-10-11: under the strict rule alone, dropping `us-bank` (mean +2.09, Gretel precision
  75.1% to 87.1%) was rejected for 0.6 points of Gretel recall. Both verdicts are shown, so the
  owner sees which changes cost a find.
- **Ranking:** strict passes first, then those within tolerance, each ordered by the change of the
  overall score (equal weights).
- **Roles:** a dataset is *scored* (in the mean) or a *guard* (it must not get worse, but has no weight);
  a saturated dataset can serve as a guard (TASK-11.15).
- A mutation that only disables rules is re-run on the samples where those rules fired in the baseline:
  elsewhere they matched nothing, so nothing can change. Any other mutation re-runs every sample.
- A rule that never fires is flagged, not removed: removal is a mutation like any other.

## Dev and check: no folds

Scoring a rule set is a count, not a statistical estimate, so there are no k folds and the scores
a person reads are on the full data. The one risk a split guards against is overfitting by the
author of a rule: an agent that reads particular misses can write a pattern that matches those
tokens and nothing else. So each dataset has one fixed split, by `group_id`, so that one repository
or document never lies on both sides:

- **dev** (about 70%): the misses and false alarms an agent may read.
- **check** (about 30%): only the totals. An agent's mutation gets the worse of its verdicts on dev
  and on check.

A change written by a person is judged on all of the data. The split is deterministic (a hash of
`group_id` with a fixed salt), so it is the same on every machine.

## Error export

`bench/errors.py` writes the false positives and misses of a run (dev split by default: an agent reads
dev errors only) with rule, type, dataset, language, the shape of the value (letters as `a`/`A` in any
script, digits as `9`) and the words before it. Masking, each rule found by checking an export against
every gold value of the split:

- a token with a capital letter, a digit or a non-ASCII letter is a shape;
- a word inside a gold span of its sample is a shape, however plain (a password can be a word);
- a first word the 40-character window cut is dropped (its tail showed part of a place name);
- a lowercase word stays readable only when the contexts of at least 5 different sources hold it
  (`routing`, `password:`); a rarer one, such as a value repeated on an unlabelled line, is a shape.

After these rules, a gold value of 6 or more characters can equal a context word only when it is a word
5 sources use. The export holds no source id.

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
