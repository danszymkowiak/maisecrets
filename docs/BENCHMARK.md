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
| synthetic tool output (generated) | one filled template | injected values `pos`, digests and ids `neg` | guard: terminal output an agent sees |
| NVIDIA Nemotron-PII | a document of the test split, us or intl locale | 55 PII labels as spans | PII in English documents of 50+ industries; locale and format scored apart |
| Mendeley synthetic financial documents | a spreadsheet row | `True Predictions` spans: name, card, e-mail, URL, phone, address, company, SSN | US-style financial documents |
| findocs (generated) | one filled template | injected values with valid checksums `pos`, look-alikes `neg` | Swiss and US tax and bank documents |

Licences: CredData's tooling is Apache-2.0 and each file keeps its source project's licence
(CredData kept permissive ones); TAB is MIT; Gretel is Apache-2.0; Nemotron-PII and the Mendeley
dataset are CC BY 4.0, which holds for anyone who runs the bench (the reports name their sources).
findocs and the synthetic tool output are ours. ai4privacy allows academic and
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

### Gretel

**Quality filter and formats, 2026-10-12 (TASK-11.33).** A record below Gretel's own
`quality_score` of 90 is dropped (14,008 of 55,940; 41,932 stay), as a study that used the dataset
did. That study also dropped the rigidly structured formats (CSV, EDI, SWIFT, FIX, BAI, XBRL, FpML,
MT940); here they stay, tagged `format:structured`, because bank and tax exports look like them, and
every report scores them apart (`tags` in `metrics.json`). The filter barely moves the score (run
20261012-005108 against 20261011-220740: F1 68.6% to 68.7%, precision 75.1% to 74.7%, recall 63.1% to
63.5%). The formats differ a lot:

| Gretel | samples | TP | FP | FN | precision | recall | F1 |
|---|---|---|---|---|---|---|---|
| structured | 10,240 | 2,364 | 3,233 | 2,385 | 42.2% | 49.9% | 45.7% |
| unstructured | 31,692 | 14,084 | 2,327 | 7,116 | 85.8% | 66.6% | 75.0% |

Structured documents are a quarter of the records and 58% of the false alarms; `us-bank` alone
raises 2,663 of their 3,233. Recall is lower there for e-mail (57% against 85%), IP (67% against 93%)
and secrets (21% against 40%); the likely cause, not yet checked sample by sample, is values in
delimited fields (FIX `|`, CSV `;`, XML tags) that the rules' boundaries do not expect. Gretel's
values are weakly diverse (the same few names and domains), so its type-level recall moves in steps.

### Nemotron-PII, Mendeley and findocs

**Added 2026-10-12 (TASK-11.34, 11.35, 11.37); baseline run 20261012-012544.**

- **Nemotron-PII** (test split, 100,000 documents). Every uid has a us and an intl record with
  different text; the sample id is `locale:uid` and the uid decides the split (a first run keyed both
  by uid and scored each text with the other's detections, 63.5% precision; `schema.write` now refuses
  a repeated sample id). Precision 99.1%, recall 63.5%, F1 77.4%. E-mail (99.3%), SSN (99.7%) and ABA
  (98.0%) are found; cards (11.7%, 11,363 missed), phones (23.1%) and secrets (21.5%) are the gaps.
  The intl locale has higher recall (69.8%) than us (56.8%).
- **Mendeley synthetic financial documents** (45,030 rows). The texts carry mojibake that shifted
  8% of the offsets; the adapter repairs it and every span lands. Every e-mail address is at
  example.com, .net or .org, which the plugin leaves alone on purpose, so e-mail is out of scope there.
  Precision 100.0%, recall 90.6%, F1 95.0%: SSN 100%, phone 93.9%, card 75.7%.
- **findocs** (3,300 generated documents, ours). Precision 100.0%, recall 84.4%, F1 91.6%. The
  misses are three gaps: an IBAN after an MT940 `?31` subfield (594, TASK-22), a US phone written
  `(494) 360-7563` (600, TASK-23), and a card number after the German word `Karte` (300, TASK-24).
  AHV and UID numbers are labelled but out of scope until TASK-20 adds the Swiss types.

**Usefulness (run 20261012-011327, before the Mendeley e-mail fix).** Each new dataset is in scope,
not saturated and moved by probes (Nemotron 22 of 30, findocs 8, Mendeley 5): keep, all three scored.
The highest overlaps are Gretel / Nemotron (61.5% of probes move both the same way) and findocs /
Mendeley (62.5%), below the 95% that would make one redundant. The synthetic tool output stays a guard
although saturated (99.2%). findocs is scored by the user's decision of 2026-10-11, with the caveat
that it is tuned to our own generator; its weight in the objective is set in TASK-21.1. The overall
equal-weight mean of the scored datasets is 79.8%.

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

### Valid gold

**2026-10-12 (TASK-21.6, `maisecrets_bench/validgold.py`; baseline run 20261012-013837).** Setup
checks every gold positive of a checksummed type with the detector's validator (IBAN mod 97, card
Luhn, the German IDs) or the bench's own where the detector has none (ABA checksum, the SSN shape
rules: no area 000, 666 or 9xx, no group 00, no serial 0000). A failing span becomes *uncertain*; a
span with a label or a card block (holder, expiry, CVC) around a valid value is trimmed to the value.

| dataset | type | gold | valid | invalid | trimmed | recall on valid gold |
|---|---|---|---|---|---|---|
| Gretel | IBAN | 1,527 | 1,184 | 312 | 31 | 96.0% |
| Gretel | CARD | 1,009 | 500 | 438 | 71 | 32.0% |
| Gretel | US_SSN | 1,117 | 714 | 255 | 148 | 63.5% |
| Gretel | ABA_ROUTING_NUMBER | 1,175 | 129 | 1,046 | 0 | 34.1% |
| Nemotron | CARD | 12,867 | 1,525 | 8,381 | 2,961 | 32.8% |
| Nemotron | US_SSN | 6,062 | 6,043 | 18 | 1 | 100.0% |
| Nemotron | ABA_ROUTING_NUMBER | 8,354 | 843 | 7,511 | 0 | 98.9% |
| Mendeley | CARD | 42,527 | 0 | 3,116 | 39,411 | 80.5% |
| Mendeley | US_SSN | 51,283 | 51,283 | 0 | 0 | 100.0% |
| findocs | IBAN, CARD, US_SSN, ABA | 5,999 | 5,999 | 0 | 0 | see above |

Gretel's IBAN recall on valid gold is 96.0%; the 97.8% of the epic was measured on the 55,940
records before the quality filter. Generated ABA numbers mostly fail their checksum (Gretel 89%,
Nemotron 90%): the `aba-routing` rule has no validator and is gated by context instead, so a
validator would cost no valid find. Cards stay a gap after the check: 32% on Gretel and Nemotron.
Every Mendeley card span is a block and is trimmed to its number. CredData, ai4privacy and the
synthetic tool output have no checksummed in-scope gold. The equal-weight mean rises from 79.8% to
80.5% because invalid gold no longer counts as missed.

## Synthetic tool output

The file and prose corpora hold no terminal output: no `printenv`, `git diff`, `grep -n`, `cat -n`,
`kubectl get secret -o yaml`, docker config, `curl -v`, lockfile or `docker images --digests`. The
setup generates such a dataset (`maisecrets_bench/adapters/synthetic.py`, TASK-11.19): ten templates,
300 samples each, from a fixed seed, in English. Secrets (GitHub, GitLab, AWS, Slack, Stripe, npm,
JWT, passwords, also base64-wrapped in a Kubernetes secret and a docker `auth`), e-mail addresses,
public IPs and phone numbers are `pos` spans; commit ids, UUIDs, SHA-256 and MD5 digests, npm
`integrity` and go.sum `h1:` strings and MongoDB ObjectIds are `neg` spans. Every value is drawn from a
generator of its rule's shape: nothing is downloaded and no real token exists anywhere. The dataset's
version is the seed, the size and a hash of the generator, so a changed generator builds it again.

**Role, decided 2026-10-11 (TASK-11.19): guard.** It is ours, so a rule tuned to raise its score would
be tuned to our own generator; it gets no weight in the overall mean. But it is the only dataset of
the output an agent actually reads, so a change must not make it worse (`run.GUARD`; `mutate.py` and
`round.py` apply the role without `--guard`).

**Baseline, 2026-10-11 (run 20261011-220740):** 5,540 TP, 2 FP, 86 misses: precision 100.0%, recall
98.5%, score 99.2% (dev 99.3%, check 99.0%). E-mail, IP and phone 100% recall; secrets 97.8%. The
misses are the generated 15 to 18 character passwords behind a weak label (`Authorization: Bearer`,
an environment name, a grep hit) and four base64 docker `auth` values. The two false alarms are an
`iban` on a go.sum `h1:` string and a `generic-api-key` on another. Digests, commit ids, UUIDs,
ObjectIds and `integrity` strings drew no other false alarm: in tool output of this shape they are
not the precision problem TASK-11.20 set out to fix.

**Digest filters (TASK-11.20, `bench/mutations/round3/`).** On CredData, hex values of a digest length
behind `generic-api-key` and the `ds-*` keyword rules are mostly real secrets (2,591 TP against 87 FP).
So "drop unless a strong label" would lose about 2,100 finds. The filters in `filters.py` drop only what
the text names as a digest: a digest label (`digest_label`), a `sha256:`/`sha512-`/`h1:` prefix
(`digest_prefix`), or `ObjectId(...)`/`_id` (`object_id`). Every one is accepted strictly on dev and
check, with no find lost. The combined filter removes 7 false alarms (CredData 6, synthetic 1); the
mean rises by 0.01 points.

## Perturbation

`bench/perturb.py` rewrites every in-scope positive of a fixed pick of samples per dataset (400 by
default, by a hash of the sample id) with one transform and measures recall on the result:
zero-width space and soft hyphen inside the value, fullwidth forms (NFKC folds them back), Cyrillic
look-alike letters, an ANSI reset inside the value, a carriage return, a line wrap, base64, hex,
HTML numeric entities, markdown escapes and truncation to three fifths. It shows how much a
normaliser or a decode-and-rescan step could win; the scored runs never include it.

**Baseline, 2026-10-11 (perturb 20261011-223530, 400 samples each; ai4privacy measured locally, not
shown):** recall of in-scope positives, untouched first.

| transform | CredData | Gretel | synthetic |
|---|---|---|---|
| none | 84.9% | 62.3% | 97.6% |
| zero-width space | 21.9% | 12.7% | 50.5% |
| soft hyphen | 21.9% | 12.7% | 50.5% |
| fullwidth | 70.9% | 0.6% | 6.2% |
| homoglyph | 79.4% | 27.4% | 62.6% |
| ANSI reset | 22.8% | 15.0% | 58.0% |
| CR | 50.6% | 12.7% | 59.3% |
| line wrap | 45.2% | 12.7% | 58.4% |
| base64 | 87.6% | 1.7% | 60.4% |
| hex | 20.1% | 1.3% | 48.3% |
| HTML entity | 13.9% | 0.8% | 29.1% |
| markdown escape | 81.0% | 19.0% | 51.7% |
| truncation | 11.8% | 7.3% | 31.9% |

Every transform costs recall. The invisible characters (zero-width, soft hyphen, ANSI reset) and
fullwidth forms could be undone by a normaliser with an offset map (TASK-11.25). The encodings could be
undone by decode-and-rescan (TASK-11.26). CredData keeps more under homoglyph, escape and base64 because
its keyword rules match the label and take any value after it.

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

### Recall floors first, then false positives (TASK-21, decided 2026-10-11)

The blended score let a change trade a leaked IBAN for three fewer over-redactions. The verdict is a
constrained optimisation instead: every type keeps a recall floor, and among the changes that keep
every floor, the one with the fewest false positives per 1,000 tokens wins. The cost of each error
type stays visible.

- **Scoring types.** A floor attaches to the type a gold span is scored as: its maisecrets type, with
  SECRET split in two (`SECRET_PREFIXED`, a token with a vendor's fixed shape; `SECRET_GENERIC`,
  keyword passwords and generic keys; `bench/floors.toml`, `[secret]`). Recall is pooled over every
  dataset that labels the type, and shown per dataset as a check.
- **Tiers** (`bench/floors.toml`, user 2026-10-11): *critical*, recall at least 0.999: IBAN, CARD,
  US_SSN, US_BANK_NUMBER, SECRET_PREFIXED (CH_AHV joins with TASK-20). *High*, at least 0.99: EMAIL,
  PHONE, IP, ABA_ROUTING_NUMBER and the German (later Swiss) tax and ID numbers. *Default*, no
  regression: SECRET_GENERIC and every type no tier lists. *None*: names, which maisecrets does not
  detect (only the terms file, C25).
- **Valid gold.** Recall counts only gold that passes its type's checksum (TASK-21.6): a span that
  fails becomes *uncertain* and counts neither as a miss nor as a false alarm; a span with a label
  around a valid value is trimmed to the value. The manifest reports valid, invalid and trimmed per
  dataset and type.
- **Sample size.** A floor is enforced through the one-sided 95% Wilson lower bound of recall
  (z = 1.645). At 0.999 that needs about 3,000 positives with no miss (the rule of three; the bound
  of 3,000 of 3,000 is 0.9991). A type's status is *clears* (the bound reaches the floor), *gap* (the
  measured recall is below the floor) or *too few* (the recall reaches the floor but the bound does
  not).
- **Below the floor.** Almost every type starts as a gap (baseline 2026-10-11: Gretel CARD 19.5%,
  US_SSN 48.2%, PHONE 45.6%). A gap must not get worse; it is listed with its distance to the floor,
  and a change that narrows it counts in its favour. A *too few* or *default* type must not get worse
  either (no regression: no find lost).
- **The objective.** False positives per 1,000 whitespace tokens, per dataset, combined as a weighted
  mean. Gretel and findocs weigh 2.0, every other scored dataset 1.0 (proposal of TASK-21.1; the
  user confirms the number). findocs is scored, not a guard (user, 2026-10-11), with the caveat that
  it is tuned to our own generator. A guard dataset weighs nothing but must not get worse.
- **What counts as a false positive.** A detection on no in-scope positive, in text the dataset labels
  as negative. A detection on an out-of-scope positive (a name), on uncertain gold, or of a type a
  dataset does not judge (CredData judges SECRET only) counts as neither. CredData's unlabelled lines
  are *unreviewed*, reported per 1,000 lines, and kept out of the objective.
- **The verdict** (TASK-21.8). *Rejected*: a type that cleared its floor no longer does, a gap gets
  worse, or a no-regression type loses a find; the report names the type and the dataset that
  decided. *Accepted*: none of that, and either the weighted false positives per 1,000 tokens fall
  or a gap narrows; the change of both is shown. *Neutral*: no effect, or more false positives with
  no gap narrowed (a trade the owner decides). Accepted changes rank by the change of the weighted
  objective.
- **Critical misses.** At 0.999 the misses of a critical type are few enough to read one by one: the
  report lists each (dataset, sample, type, masked context; `errors.py`).

The verdicts below (strict, within tolerance) came first. They stay in the reports as a comparison
column until TASK-21.10 has re-judged the mutations accepted under them.

### The earlier verdicts (for comparison)

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
- **What a mutation can change:** disable a rule, add one, or set its regex, keywords, entropy, score,
  context, stopwords or validator. Three fields exist only in the bench, so an idea can be judged
  before the plugin has it: `validator = "bench:aba"` (a checksum of `maisecrets_bench/validators.py`),
  `allow = [regex]` (a value that matches is skipped, on top of the rule's own allowlist) and
  `filter = "bench:name"` (a function of `maisecrets_bench/filters.py` that gets the value, the text
  and the value's offsets, so it can read the label before the value). A filter runs after the rule's
  validator, entropy, context and allowlist and before the hit claims its span: a dropped hit leaves
  the span to the next rule, as a failed validator does.
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
