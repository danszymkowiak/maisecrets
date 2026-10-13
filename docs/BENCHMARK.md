# Rule benchmark: design

How the detection rules are measured against public labelled datasets, and how a proposed rule
change is judged. The work is TASK-11 and its subtasks in `backlog/`. Nothing here ships with the
plugin: `bench/` is developer-only, and the datasets never enter the repository.

**Current baseline: run 20261012-194832** (2026-10-12): Betterleaks v1.9.0 with the carried gitleaks rules
and the Veles rules, the clean gold (valid4, TASK-30/31), ai4privacy continuation leads uncertain (TASK-33),
findocs names, birth dates and streets labelled (TASK-36), and the plugin changes accepted on clean gold that
day (TASK-35, 11.29 to 11.31). 94 rules fire; dataset scores: ai4privacy 76.6%, CredData 71.5%, findocs 100%,
Gretel 78.6%, Mendeley 96.1%, Nemotron 83.5%, synthetic 99.3% (a guard); equal-weight mean 84.4% (was 84.1%
on 20261012-141549). The leave-one-out review (TASK-18) runs on this baseline, over Betterleaks rule IDs.

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
  misses were three gaps: an IBAN after an MT940 `?31` subfield (594, TASK-22), a US phone written
  `(494) 360-7563` (600, TASK-23), and a card number after the German word `Karte` (300, TASK-24).
  TASK-22 closed the first: run 20261012-084443 against 20261012-081433 finds the 594 IBANs, and
  nothing else moves on any dataset (lowercase IBANs, the other half of TASK-22, occur in none).
  TASK-23 closed the second (accepted by the user on 2026-10-12): a region-us rule for `(NXX) NXX-XXXX`
  (area code and exchange 2-9, no reserved middle 9). Run 20261012-135603 against 20261012-131230: PHONE
  findocs 80.0% to 100%, Gretel 56.7% to 63.3%, Nemotron 23.2% to 29.7%; false hits +40 (Gretel 22,
  Nemotron 17, ai4privacy 1), mostly real-looking numbers the datasets left unlabelled; verdict accepted.
  TASK-24 closed the third: Presidio's card words are English, and card words of the label
  languages (Karte, Kreditkarte, carte, carta, tarjeta, …) now count. Run 20261012-102454 against
  20261012-100249: findocs CARD 50% to 100%, Gretel CARD 36.3% to 44.7%, one more false positive
  (Gretel); verdict accepted.
  AHV and UID numbers map to CH_AHV and CH_UID (TASK-20, gold revision valid2). The Swiss rules
  were judged as a mutation that runs them in every language group (`bench/mutations/add-swiss-ch.toml`,
  baseline 20261012-081433, mutation run 20261012-082626): accepted, findocs AHV 900/900 and UID
  600/600, no new false alarm on CredData, Gretel, Mendeley, Nemotron or the synthetic output, 13 more
  on ai4privacy (of about 250,000 records), weighted false positives +0.000. So the dotted AHV form
  stands without a context word; the bare 13 digits keep one. 900 AHV positives are too few to prove
  the 0.999 floor (about 3,000 needed), and a plain run grouped the Swiss documents by language (`de`,
  `fr`), not region `ch`: both closed by TASK-28 (below, Regions).

**Usefulness (run 20261012-011327, before the Mendeley e-mail fix).** Each new dataset is in scope,
not saturated and moved by probes (Nemotron 22 of 30, findocs 8, Mendeley 5): keep, all three scored.
The highest overlaps are Gretel / Nemotron (61.5% of probes move both the same way) and findocs /
Mendeley (62.5%), below the 95% that would make one redundant. The synthetic tool output stays a guard
although saturated (99.2%). findocs is scored by the user's decision of 2026-10-11, with the caveat
that it is tuned to our own generator; it weighs 2.0 in the objective (user, 2026-10-12). The overall
equal-weight mean of the scored datasets is 79.8%.

### Regions

The PII rules depend on the configured regions (`maisecrets/regions.py`). Each sample runs with
`generic` plus the regions of its language (German text: `de`; Italian: `it`; …), so a country's
rules never run on another country's text. Samples are grouped by language and each group runs
with its own config. A sample whose locale tag names a country with rules of its own runs in a group
of that locale (`run.LOCALES`, TASK-28): findocs' `de_CH` and `fr_CH` documents run as `de:de_CH`
and `fr:fr_CH` with region `ch`; every other group is unchanged. findocs writes its three templates
with an AHV number four times as often (3,600 AHV, 2,400 UID), enough for the critical floor.
Baseline run 20261012-112723 (against 20261012-110134): CH_AHV 3,600/3,600, Wilson lower bound
0.99925, clears; CH_UID 2,400/2,400 clears; no false positive moved on any dataset.

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
  at 0, context requirements off) and keeps each candidate's score. An entropy rule (since TASK-19.4 the
  carried gitleaks rules; Betterleaks puts its entropy limits in filter expressions) gets a curve
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
validator would cost no valid find. Cards stayed a gap after the check, 32% on Gretel and Nemotron,
until TASK-31 found most of Nemotron's gap to be fragments of fake numbers (below).
Every Mendeley card span is a block and is trimmed to its number. CredData, ai4privacy and the
synthetic tool output have no checksummed in-scope gold. The equal-weight mean rises from 79.8% to
80.5% because invalid gold no longer counts as missed.

**Validity rules for the types without a checksum (TASK-30, gold revision valid3; baseline run
20261012-094904, against 20261012-085837).** Decided 2026-10-12: clean the gold before more rule
shaping. `bench/audit.py` counts, per dataset and type, the positives that fail each candidate rule
(`maisecrets_bench/audit.py`; shapes only, never values; first run 20261012-094314), and the rules
were chosen from it:

- **Phone:** 7 to 15 digits (E.164; an `00` prefix and a `(0)` trunk do not count), no letters but
  an extension, not one repeated digit, and a number with `+1`/`1-` or a US layout follows the
  North American plan (area code and exchange start with 2-9, an area code's middle digit is not
  9). A leading 0 is a trunk prefix elsewhere (`030-438-8690`, `(022) 739-3821`): not judged by the
  US plan. Gretel's `(123) 456-7890`, `(800) 123-4567` and `555-555-5555` are placeholders.
- **E-mail:** address syntax, and not a reserved domain (example.com/.net/.org, .test, .example,
  .invalid, .localhost), which the plugin leaves alone on purpose.
- **IP:** parses, and is public (the plugin redacts public addresses only).
- **US bank number:** 4 to 17 digits, no letters. One that is a valid IBAN (Nemotron writes account
  numbers as `FR76 3000 ...`) becomes IBAN.

A failing value becomes *uncertain*. A span with nothing of its type in it (`[Phone Number]`,
"adresse e-mail professionnelle", no digit or no `@`) is a label error and becomes *negative*.
Trimming takes only a whole match of the pattern for these types (brackets and labels off): a
shortened value passes a rule without a checksum as easily as the whole one. Our generators write
only valid values (findocs and synthetic wrote a reserved area code: 59 and 35 phones; a test
checks every generated positive). Cases no rule catches go into `bench/gold_exceptions.json`
(`maisecrets_bench/exceptions.py`): place, a hash of the span's text, verdict (negative, uncertain,
drop) and a rationale; setup applies them and refuses a stale entry. It is empty so far.

| dataset | type | gold | invalid | trimmed | negative | recall before | recall on valid gold |
|---|---|---|---|---|---|---|---|
| Gretel | PHONE | 6,840 | 2,087 | 70 | 208 | 45.7% | 56.7% |
| Gretel | EMAIL | 10,639 | 1,794 | 457 | 224 | 80.9% | 99.9% |
| Gretel | IP | 2,319 | 246 | 0 | 0 | 83.4% | 93.1% |
| Nemotron | EMAIL | 53,930 | 137 | 16 | 275 | 99.3% | 100.0% |
| Nemotron | IP | 9,217 | 1,246 | 3 | 0 | 86.4% | 99.8% |
| Nemotron | US_BANK_NUMBER | 16,693 | 4,986 | 0 | 0 | 47.8% | 67.1% |
| ai4privacy | PHONE | 58,785 | 846 | 26 | 87 | 19.4% | 19.1% |
| ai4privacy | EMAIL | 74,288 | 301 | 314 | 136 | 99.3% | 99.9% |
| ai4privacy | IP | 65,569 | 2,888 | 46 | 65 | 91.4% | 95.7% |

E-mail and IP misses were almost all invalid or reserved values; on valid gold both are near 100%
on Nemotron. Phone stays the gap (Gretel 56.7%, Nemotron 23%, ai4privacy 19%). Nemotron's 47 bank
numbers that looked like valid IBANs were mostly fragments of fake ones (see the cut rule below). Precision moves by at most 0.7
points (Gretel 74.3% to 73.6%): detections of invalid gold were counted as found and are now
neutral. The equal-weight mean rises from 79.9% to 81.4%.

**ai4privacy continuation records (TASK-33, the user's decision of 2026-10-12; baseline run
20261012-140543).** ai4privacy cut long texts into records `…A`, `…B`, `…C`; a continuation starts in
the middle of a value its chunking left unlabelled. The adapter marks a continuation record's first
token as uncertain (`continuation_lead`, revision cont1), so a detection there counts neither as found
nor as a false alarm. Against 20261012-135603: ai4privacy false hits 6,140 to 4,199 (e-mail 2,498 to
1,080, IP 1,650 to 1,206), precision 96.1% to 97.3%, true hits unchanged, no other dataset moves. Every
report notes that ai4privacy's precision is a lower bound: its generator also wrote values outside the
labelled slots, which cannot be told from real false alarms without reading the text.

**No cut drops a group of the value (TASK-31, gold revision valid4; baseline run 20261012-100249).**
Trimming shrank a value from the right until its checksum passed, to drop what a greedy pattern took
after it (the ` 12` of an expiry after a card number). It also cut fake values at a group boundary
until a prefix passed by chance (1 in 97 for an IBAN, 1 in 10 for a card): `FR72 2000 7011 5930|
2331 67` became a "valid" IBAN fragment that no detector reports, and counted as a miss. A cut is now
allowed only at a separator and when the first dropped group differs in length from the last kept
one. Trimmed cards fell from 2,961 to 2 on Nemotron, 71 to 1 on Gretel and 39,411 to 39,060 on
Mendeley; Gretel's trimmed IBANs from 31 to 7. Recall on valid gold: Nemotron CARD 32.8% to 95.7%,
Nemotron IBAN 10.6% to 83.3% (5 of 6), Gretel IBAN 95.9% to 97.9%, Gretel CARD 32.0% to 36.3%,
Mendeley CARD 80.5% to 81.1%. No false positive moved. The card gap of Nemotron was the artefact;
Gretel's remains.

### Betterleaks against gitleaks (TASK-19.3, 2026-10-12)

The switch of the vendored secret rules, judged as mutations (`bench/mutations/betterleaks/`, op
`vendored`) against baseline 20261012-113809 (gitleaks), run 20261012-123731. Betterleaks with
generic-password and generic-credential-uri off (the user, 2026-10-12).

| dataset | precision gitleaks | precision Betterleaks | recall gitleaks | recall Betterleaks |
|---|---|---|---|---|
| CredData | 78.62% | 76.13% | 63.77% | 63.92% |
| Gretel | 73.61% | 73.61% | 80.67% | 80.68% |
| Nemotron | 99.05% | 99.06% | 70.58% | 70.58% |
| synthetic (guard) | 99.96% | 99.96% | 98.65% | 98.15% |
| ai4privacy, findocs, Mendeley | unchanged | unchanged | unchanged | unchanged |

Verdict: rejected (the synthetic guard loses 28 finds; SECRET_GENERIC loses one on Nemotron), though
SECRET_PREFIXED gains 22 finds. Per rule (all datasets, true / false hits, gitleaks -> Betterleaks):

| rule | gitleaks | Betterleaks | note |
|---|---|---|---|
| generic-api-key | 5,180 / 672 | 5,078 / 1,093 | CredData +420 false; no `password` keyword any more (Betterleaks moved it into generic-password) |
| npm-access-token | 4 / 0 | 0 / 0 | the 4 synthetic tokens are missed |
| github-pat, gitlab-pat, slack-bot-token, stripe-access-token, jwt | 643 / 12 | 757 / 12 | spans generic-api-key had found, now by their own rule |
| mongodb-connection-string, posthog-project-api-key, docker-swarm-join-token, alibaba-secret-key, alibaba-sts-access-key-secret, gcp-api-key | 6 / 0 | 16 / 1 | new finds on CredData |
| gcp-service-account | 0 / 0 | 0 / 2 | false hits only: off in rules/overrides.txt |

**tokenRatio** (119 rules after the two off): (a) entropy fallback, (b) the word-likeness filter
`bench:wordlike_75`, (c) the rules dropped gave identical numbers on every dataset: none of those
rules decides a hit here. Chosen: (a), no extra machinery for no measured gain.

**The 4 rules only gitleaks has:** none fired on any dataset. datadog-access-token: let go, Betterleaks'
datadog-application-key takes the same shape. etsy-access-token, jfrog-api-key, jfrog-identity-token:
keep, carried as our own rules when gitleaks goes (TASK-19.4): with only a provider label Betterleaks
misses all three, and old JFrog keys still sit in configuration files.

**Betterleaks with gitleaks' generic-api-key (TASK-19.8, run 20261012-125555): accepted.** The bench op `carry`
puts gitleaks' generic-api-key (regex, keywords, entropy 3.5, allowlists, our fixes) in place of
Betterleaks' own. Against the gitleaks baseline: CredData 9,957 to 9,965 true hits with false hits
unchanged (2,708), every other dataset identical, SECRET_PREFIXED gap narrowed, guards unchanged
(`bench/mutations/betterleaks/d-carry-generic.toml`). The npm-access-token "losses" were no misses:
in the four synthetic documents generic-api-key claims the same token first. TASK-19.4 switches to
this configuration.

**Veles rules from Kingfisher (TASK-19.5, run 20261012-141549).** `scripts/sync_veles.py v2.11.1` vendors the
26 Veles detectors Kingfisher converts. A generated sample of each was scanned with the current rules: 8 are
already found by a Betterleaks rule (DigitalOcean, xAI, npm, Postman API key, SendGrid, three Slack tokens),
the 3 git credential URLs have their password redacted by ds-basic-auth, and 2 Packagist repository URLs and the
HCP client id are no secrets: those 14 are off in `rules/overrides.txt`. The other 12 (Bitwarden, CircleCI
project, Cloudflare, Deno, HCP client secret, Heroku platform key, OpenRouter, four Packagist tokens, Postman
collection) fire on no bench sample: no false hit over every dataset, verdict neutral; kept for the providers
they add.

**The switch (TASK-19.4, baseline run 20261012-131230).** Betterleaks is the vendored set; gitleaks'
generic-api-key, etsy-access-token, jfrog-api-key and jfrog-identity-token are carried in
`rules/carried.json`; generic-password, generic-credential-uri and gcp-service-account are off. Against
the last gitleaks baseline (20261012-113809): CredData 9,957 to 9,965 true hits, every other number
unchanged; verdict accepted. The gitleaks rule files and `scripts/sync_gitleaks.py` are gone.

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

### Normaliser stages (TASK-11.25, 2026-10-12)

`maisecrets/normalise.py` cleans a copy of the text and the shape rules scan it a second time; a hit
there redacts the original range, hidden characters included. Each stage was judged twice:

- **On the scored datasets** (mutation run 20261012-150659 against baseline 20261012-141549, the floor
  verdict): entity is a clean win (CredData +4 true positives, no false positive anywhere). ansi, cr,
  invisible, gutter and fullwidth are neutral: the datasets hold none of those disguises. escape passes
  the verdict only because one card is found more, while Gretel's false hits rise by 60 (5,583 to
  5,643); by the true-against-false trade (TASK-18.2) it stays off.
- **On the perturbation suite** (perturb 20261012-152034 without stages, one run per stage; 400
  samples per dataset, ai4privacy left out of the sums). Recall over all datasets, 87.8 % untouched:

| transform | stage | without | with |
|---|---|---|---|
| zero-width space | invisible | 18.6% | 88.6% |
| soft hyphen | invisible | 18.6% | 88.6% |
| fullwidth | fullwidth | 34.9% | 87.8% |
| ANSI reset | ansi | 21.0% | 89.3% |
| CR | cr | 33.3% | 88.4% |
| HTML entity | entity | 9.3% | 89.3% |
| markdown escape | escape | 60.1% | 88.1% |

No stage changes recall under another transform. The suite has no gutter transform; gutter is
neutral on the datasets and its case (a value in `cat -n`, `grep -n` or diff output) is covered by
`tests/test_normalise.py`.

**Time** (`bench/normtime.py`, ansi, cr, invisible, gutter, entity and fullwidth on, median of 15 scans,
idle machine): looking costs nothing measurable (25 KB plain +0 ms, 120 KB plain +2 ms); when a stage
changes the text the second pass scans it again in full, 25 KB +19 ms (19 to 38 ms) and 120 KB +95 ms
(95 to 190 ms), with a gutter or ANSI colour on every line. Scanning only the changed lines would cut
that.

**Guarded unwrap** (`maisecrets/unwrap.py`, the last stage): a line break inside a token is removed only
when a SECRET shape rule finds a token across it that the line before does not hold whole, so `.env`
lines stay apart. Neutral on the datasets; on the perturbation suite the line wrap rises from 30.6 % to
32.1 % (perturb 20261012-174412). It asks the rules at every break between word characters: +107 ms on
25 KB and +517 ms on 120 KB of plain prose. It stays off; TASK-37 is a cheaper guard. The cheaper guard (TASK-37,
2026-10-13) asks the rules only where the token run before the break has 8 characters and both runs together 24,
or where the run starts right after `=` or `:` (CredData's wrapped values are passwords whose halves have 4 to 7
characters): +4 ms on 120 KB of plain prose (`bench/normtime.py --stages unwrap`, idle machine). On the
perturbation suite the line wrap rises from 30.6 % to 32.1 % (perturb 20261013-104311), the same 141 finds as the
old guard; with the length condition alone it was 31.4 %. Neutral on the datasets (mutation run 20261013-104727).

### Decode and rescan (TASK-11.26, 2026-10-13)

The normaliser's `decode` stage (`maisecrets/decode.py`) replaces each base64 or hex run (24 or 32 characters at
least) whose bytes are UTF-8 text, 90 % printable, by that text; gzip inside base64 is opened and a run inside the
decoded text is decoded once more (depth 2). Every decoded character maps back to the whole run, so a hit inside it
redacts the run. Bounds: a text over 1 MB is not looked at, a run over 16 KiB is not decoded, at most 64 runs and
256 KiB of decoded bytes per text, and no new run after 20 ms.

- **Datasets** (mutation run 20261013-101635, floor rule): accepted, CredData +12 and Nemotron +4 finds for 2 false
  positives more (CredData), the SECRET_PREFIXED gap narrowed.
- **The synthetic dataset's encoded positives** (900 gold values that decode to text): the rules find 896 of them
  without the stage (through their labels and the Kubernetes Secret rule) and 896 with it.
- **Perturbation** (perturb 20261013-103401 without the stage, 20261013-112037 with it; 400 samples per dataset,
  ai4privacy left out of the sums): base64 47.7 % -> 71.1 %, hex 14.0 % -> 38.4 %. Gretel base64 2.1 % -> 61.8 %, hex
  1.2 % -> 61.6 %; findocs base64 and hex 0 % -> 72.7 %. (The first run, 20261013-102211, gave base64 63.8 %: the run
  pattern wanted 24 characters before the padding, so a 16-byte value, 22 characters and `==`, was never decoded;
  TASK-43.) A value shorter than 16 characters encodes to fewer than 24 base64
  characters and is not decoded (an SSN with its dashes has 11). Mendeley rises only to 15.2 % (TASK-43): of its 400
  samples' in-scope values every phone number (410) and SSN (473) and 124 of 357 cards are too short to be decoded,
  and 45 of the decoded cards are missed unencoded too.
- **Cost** (`bench/decodecost.py`, idle machine), bytes decoded and time of the stage per text:

| dataset | texts | changed | decoded bytes p50 / p99 / max | ms p50 / p99 / max |
|---|---|---|---|---|
| CredData | 12,057 | 419 | 88 / 2,763 / 13,280 | 0.16 / 2.86 / 25.0 |
| Gretel | 20,000 | 1 | 0 / 273 / 6,132 | 0.03 / 0.06 / 0.3 |
| synthetic | 3,000 | 836 | 63 / 267 / 267 | 0.02 / 0.05 / 0.1 |
| findocs | 6,000 | 0 | 0 / 54 / 54 | 0.01 / 0.02 / 0.1 |
| Nemotron | 20,000 | 265 | 0 / 119 / 3,534 | 0.02 / 0.08 / 0.3 |
| TAB | 1,268 | 0 | 0 / 37 / 102 | 0.11 / 0.56 / 0.6 |

  Before the 1 MB bound a 10 MB CredData file cost 225 ms, the search walking on after its budget was spent. On the
  synthetic 25 KB and 120 KB texts of `bench/normtime.py` the stage adds at most 3 ms. A text the stage changes is
  scanned a second time in full, like with every stage.

Switching the stage on waits for the user, with the other normaliser stages (TASK-17).


On clean gold (mutation runs of 2026-10-12 against 20261012-141549) the set of ansi, cr, invisible,
gutter, entity and fullwidth is accepted and narrows the SECRET_PREFIXED gap. Whether to switch it on
is the user's call (TASK-17).

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

A mutation (add, disable or replace a rule, change a threshold or a word list, or switch off one named check of
the detector's `FIXES` with `op = "unfix"`, TASK-26) is applied inside
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
  mean. Gretel and findocs weigh 2.0, every other scored dataset 1.0 (proposed in TASK-21.1,
  confirmed by the user on 2026-10-12, together with the split of SECRET into prefixed and generic). findocs is scored, not a guard (user, 2026-10-11), with the caveat that
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
- **Critical misses.** At 0.999 the misses of a critical type are few enough to read one by one. A run
  writes their positions to `critical_misses.tsv` (dataset, sample, type, offsets; no value) and counts
  them per type in its report; `errors.py` exports the misses with their shape and the words before
  them, masked. Today they number in the thousands (cards above all), so the counts come first.

**Baseline, 2026-10-12 (run 20261012-020214; scored datasets pooled, valid gold).** Every type is
below its floor, so every change today is judged by "no gap worse", and the gaps rank the work:

| type | tier | finds | recall | to the floor |
|---|---|---|---|---|
| US_SSN | critical | 58,473 / 58,789 | 99.5% | 0.4 points |
| IBAN | critical | 4,771 / 5,414 | 88.1% | 11.8 |
| SECRET_PREFIXED | critical | 1,628 / 2,045 | 79.6% | 20.3 |
| CARD | critical | 33,689 / 45,068 | 74.8% | 25.1 |
| US_BANK_NUMBER | critical | 8,862 / 17,593 | 50.4% | 49.5 |
| EMAIL | high | 137,470 / 140,357 | 97.9% | 1.1 |
| ABA_ROUTING_NUMBER | high | 1,478 / 1,572 | 94.0% | 5.0 |
| IP | high | 69,844 / 77,105 | 90.6% | 8.4 |
| PHONE | high | 64,386 / 142,206 | 45.3% | 53.7 |
| SECRET_GENERIC | default | 19,193 / 74,241 | 25.9% | no regression |

Weighted false positives per 1,000 tokens: 0.291 (Gretel 0.784, ai4privacy 0.577, CredData 0.118,
Nemotron 0.064, Mendeley and findocs 0).

The verdicts below (strict, within tolerance) came first. They stay in the reports as a comparison
column until TASK-21.10 has re-judged the mutations accepted under them.

### Entropy variants (TASK-11.21, 2026-10-12)

`bench/curves.py` on baseline 20261012-194832 sweeps raw, normalised (raw over the alphabet's bits), length-corrected
and min-entropy for the one entropy rule left, generic-api-key. Area under precision over retained: raw 89.7 %,
normalised 92.8 %, length-corrected 85.8 %, min 90.4 %. Normalised wins as one threshold for every value, but with
one threshold per charset it makes exactly the cuts raw makes (it is raw divided by a constant per charset), so the
candidate is raw entropy per charset, each threshold chosen on dev: hex 3.449, base32 3.584, base62 3.322, base64
3.252, base64url 3.426, printable 3.594 (today one 3.5). Length-corrected and min-entropy lose on check (base64url
24 to 31 false positives where raw keeps 4) and are not taken.

Judged (`bench:entropy_charset`, run 20261012-225924): accepted, SECRET_GENERIC +112 finds and 11 false positives fewer
(CredData -11, ai4privacy -1, Gretel +1). It gains finds and removes false positives at once, where a flat 3.3
(TASK-21.9) gains 259 finds for 101 more false positives. Applying it waits for the user (TASK-41).

### Operating points (TASK-21.9, 2026-10-12)

From the curves of baseline 20261012-194832 (`bench/curves.py`): one entropy rule is left (generic-api-key, 3.5)
and the Presidio rules have a context gate, on or off. Each candidate was judged as a mutation (run
20261012-224331); the counts are the finds gained and false positives added over the whole bench.

| change | verdict | finds gained | false positives added |
|---|---|---|---|
| credit-card without its context gate | accepted | CARD +325, US_BANK_NUMBER +12 | +66 |
| generic-api-key entropy 3.3 (today 3.5) | accepted | SECRET_GENERIC +259 | +101 |
| us-ssn#0 without its gate | accepted | PHONE +175 (a phone number in an SSN shape) | +86 |
| us-itin#0 without its gate | accepted | PHONE +51 | +6 |
| us-npi#1 without its gate | accepted | PHONE +5 | +2 |
| aba-routing#0 without its gate | accepted | ABA +18, PHONE +227, US_BANK_NUMBER +26 | +2,503 |
| iban, ip#2, ip#3, us-ssn#2 without their gate | neutral | - | - |
| generic-api-key entropy 3.4 | neutral | - | - |
| generic-api-key entropy 3.6 to 4.0 | rejected | generic secrets lost | - |

Floors come first, so a narrowed gap accepts a change that adds false positives. Of these, two gain finds of their
own type at a fair price: credit-card without the gate and generic-api-key at 3.3. Applied together (run
20261012-224916) they are accepted: CARD +325, SECRET_GENERIC +259, US_BANK_NUMBER +12, 167 more false positives,
weighted false positives per 1,000 tokens +0.003, mean score +0.22. The ID rules gain only phone numbers they mistype,
and aba-routing#0 pays 2,503 false alarms for them. Applying the pair waits for the user (TASK-40).

### Leave-one-out (TASK-18, 2026-10-12)

Each of the 94 rules that fire in baseline 20261012-194832 was left out on its own (`bench/loo.py`, run
20261012-200148) and the removals ranked by `bench/rank.py`: pure wins (false positives saved, no find lost),
then trades by weighted false positives saved per weighted find lost (lost finds weigh 100 critical, 10 high, 1 no
regression), then the protected rules (a floor broken, a gap worse or a guard lost).

The first ranking was wrong in one way that matters: the floors only see the types the plugin claims, so a rule
that finds passports, ID cards or licences, which the datasets label as out of scope, looked like a pure win. The
ranking now counts those finds too, weighted 10 (mutation run 20261012-212629 re-ran the 33 candidates):

| rule | false positives saved | finds lost | unscored finds lost | verdict of the ranking |
|---|---|---|---|---|
| es-passport | 89 | 0 | 5,541 passports | keep |
| us-license#0 | 156 | 24 | 2,231 driving licences | keep |
| es-nif | 65 | 0 | 1,412 ID cards | keep |
| it-passport | 29 | 0 | 539 passports | keep |
| medical-license | 9 | 0 | 280 (health plan, licence numbers) | keep |
| us-npi#0 | 51 | 0 | 18 | keep |
| uk-nino | 16 | 0 | 8 national insurance numbers | keep |
| de-vat-id#0 | 60 | 0 | 0 | candidate: require a context word (TASK-38) |
| de-handelsregister | 32 | 0 | 0 | candidate: drop (TASK-39) |
| de-tax-number#2 | 7 | 0 | 0 | keep: its hits are real tax numbers after "Steuernummer:", which Gretel does not label |

Reading the hits mattered as much as the counts. de-vat-id#0's hits are FIX and XML identifiers that pass the
checksum, so a VAT context word removes them; de-handelsregister's are real register numbers, of companies, not
people. No trade saves more weighted false positives than it costs except url-query-secret (48 saved for 3 secrets
and 3 unscored finds, ratio 1.5, weak evidence), which stays. The protected list holds every rule behind a
floor: credit-card, email, us-bank, phone, iban, ch-ahv, ip, us-ssn, private-key, jwt, aws-access-token, the
keyword rules and generic-api-key among them.

### The earlier accepted changes under the floor rule (TASK-21.10, 2026-10-12)

Every change accepted in rounds 1 to 3 (strictly or within tolerance), judged again against baseline 20261012-194832
(mutation runs 20261012-173742 and 20261012-211246). Four were already applied after an earlier re-judge (TASK-11.29
to 11.31, 11.32 was closed by the user).

| change | earlier verdict | floor verdict | deciding type |
|---|---|---|---|
| Drop uk-postcode | accepted | accepted, applied (TASK-11.31) | - |
| Keyword rules: skip an UPPER-UPPER-…_ identifier | accepted | accepted, applied (TASK-11.30) | - |
| ds-keyword-colon: skip digits:word | accepted | accepted, applied (TASK-11.30) | - |
| Drop de-vat-id#0 | within tolerance | accepted | - |
| Generic rules: skip label-negative | accepted | accepted | - |
| Generic rules: skip digest any / prefix / label | accepted | accepted | - |
| Generic rules: skip object id | accepted | neutral | - |
| us-bank: context word just before the number | within tolerance | rejected, not applied (TASK-11.28) | US_BANK_NUMBER, ABA, CARD, PHONE gaps worse |
| us-bank: a bank word before, not after a SWIFT tag | within tolerance | rejected | the same gaps worse |
| us-bank: not a SWIFT MT field tag's number | within tolerance | rejected | CARD gap worse (3 finds on Gretel) |
| se-personnummer: Luhn | within tolerance | rejected, not applied (TASK-11.29) | US_SSN gap worse (10 on Gretel) |
| Generic rules: skip wordlike-75 | within tolerance | rejected | SECRET_GENERIC, a find lost on CredData |

Every change the tolerance let through on 2026-10-11 fails the floor rule except de-vat-id#0.

### Word-likeness and the label's word sets (TASK-11.22, TASK-11.23, 2026-10-13)

The round 3 filters of the generic keyword rules (generic-api-key, ds-keyword-colon, ds-keyword-equal-signs,
ds-basic-auth, ds-keyword-arrow-function-sign-quotes-required, ds-keyword-quotes-and-semicolon), judged under the
floor rule against baseline 20261012-194832 (mutation run 20261013-090847):

| filter | verdict | CredData false positives | finds lost (SECRET_GENERIC) |
|---|---|---|---|
| label-negative (a negative label: token_count, password_hash, tokenizer) | accepted | 2,298 -> 2,249 | none |
| wordlike-75 (word coverage above 0.75, outside a strong label) | rejected | 2,298 -> 2,051 | 1 (CredData) |
| wordlike-44 | rejected | 2,298 -> 1,491 | 62 (ai4privacy 53, CredData 9) |
| label-weak-entropy (label-negative, and a weak label needs 3 bits) | rejected | 2,298 -> 2,237 | 44 |
| bigram-309 (letter-bigram log-odds) | rejected | 2,298 -> 2,284 | 21 |

Weighted false positives per 1,000 tokens change by less than 0.01 in every row; the other datasets move by at
most 24 false positives. label-negative drops, per rule, 186 hits of ds-keyword-colon, 16 of ds-keyword-equal-signs,
13 of generic-api-key and 2 of ds-keyword-quotes-and-semicolon (3 of them on ai4privacy), none of them a find; 49 are
scored false positives (the rest sit on uncertain or out-of-scope gold). It makes no check of `detect.py`
redundant: `_DERIVED_LABEL_RE` (uuid-elided-or-derived) also drops `id`, `arn`, `ref` and `rules` labels, which the
word-set table keeps out of its negatives by dev evidence, and `hashed_secret`; `_MEASURE_LABEL_RE`
(measure-number) reads the whole label (`TTL_REFRESH_TOKEN`) and only for a number. It would be an addition.

The one find wordlike-75 loses has a word coverage of 0.871; no other find of these rules on the whole bench is
above 0.667 (ai4privacy's highest is 0.75). wordlike-90 cuts above it (see round 6 below); that threshold is read
off all data, not dev, so its margin is thin. The report's claim (Betterleaks: F1 0.874 with token efficiency and a
word filter, 0.325 with entropy, on CredData candidates) does not carry over: here a word filter removes at most 35 % of
CredData's false positives (wordlike-44), and every cut below 0.871 costs a find.

**Round 6** (mutation run 20261013-095827, same baseline): wordlike-90 is accepted, 163 false positives fewer
(CredData 147, Nemotron 7, ai4privacy 5, Gretel 4) and no find lost.

### Repeat count and a learned filter (TASK-11.27, 2026-10-13)

The generic keyword rules (ds-keyword-colon 1,093, ds-keyword-equal-signs 886, generic-api-key 672 false positives
in baseline 20261012-194832) are where most false alarms of secrets remain, and the cheaper filters above remove at
most 163 of them (wordlike-90). Two last ideas:

- **Repeat count**: skip a value of these rules that occurs several times in the same text (a placeholder, a shared
  constant). Three times (mutation run 20261013-105756): CredData false positives 2,298 -> 1,055, but 154 finds lost
  (Nemotron 151, Gretel 2, ai4privacy 1: a password a document repeats), rejected. Counted per hit, no find on the
  bench repeats ten times or more, while 353 CredData false positives do; repeat10 is accepted on dev (CredData 1,752
  -> 1,541) and on check (round 20261013-105913). The threat model speaks against it: a debug log that prints the
  same `password=` line on every request repeats a real value, and the filter would let exactly that through.
- **Learned filter** (`maisecrets_bench/learned.py`, `bench/learn.py`): a logistic regression over 28 numbers of a
  hit (length, character classes, three entropies, word coverage, the label's class, quoting, shapes, the rule),
  trained on the dev split only (15,930 finds, 2,021 false positives); the table of coefficients is
  `maisecrets_bench/learned_table.py`. To keep every dev find its threshold has to sit below the worst-scored find,
  and there it drops 42 of the 2,021 dev false positives. The round accepts it (dev: CredData 1,752 -> 1,731; check:
  weighted false positives per 1,000 tokens -0.001), but it removes fewer false positives than wordlike-90 or the
  repeat count, on the data it was trained on. The strongest weights: word coverage (negative), normalised entropy,
  lower-case share, `-` or `_` in the value (negative), all-hex.

**Go or no-go:** no-go for the learned filter. Under recall floors a model is held to its worst-scored find, and the
finds and false positives of these rules overlap too much in every feature tried for a threshold that keeps all
finds to remove more than 2 %. The remaining false positives are values that look like secrets after a secret's
label; telling them apart needs what the text means, which is redact's model step, not a filter in a hook.
repeat10 passes the bench, but whether its risk is acceptable is the user's call.

### Presidio's remaining checksums (TASK-11.24, 2026-10-13)

Presidio 2.2.364 validates more recognizers than the plugin's port does. `maisecrets_bench/validators.py` ports
seven of them (es-nif, es-nie, it-vat-code, nhs, us-npi, se-organisationsnummer, uk-vehicle-registration), each
tested with the vectors of Presidio's own tests at that tag and compared with Presidio itself on 20,000 random
values per recognizer: no disagreement. medical-license (a DEA check) has no published test vector in Presidio's
repository and is left out. The other candidates of the task (PESEL, Aadhaar, the Finnish HETU, the Canadian SIN,
and the Dutch BSN, French NIR, Danish CPR, Norwegian fodselsnummer and Croatian OIB, which have no rule at all)
never fire on the bench: not testable here.

First the risk: a generator that invents ID numbers ignores their check digit, and a checksum then drops true
finds. `bench/passrate.py` counts how many of a rule's hits on labelled gold (any label) pass (baseline
20261012-194832, `passrate.md` in the run):

| rule | dataset | hits on gold | pass | hits elsewhere | pass |
|---|---|---|---|---|---|
| es-nif | ai4privacy | 1,413 (IDCARD) | 3.5% | 20 | 0.0% |
| es-nif | Gretel | 0 | - | 46 | 13.0% |
| es-nie | ai4privacy | 41 (IDCARD) | 0.0% | 0 | - |
| it-vat-code | Gretel | 3 (phone numbers) | 0.0% | 132 | 1.5% |
| nhs | Gretel | 3 (phone numbers) | 0.0% | 1 | 0.0% |
| us-npi | Gretel, Nemotron, ai4privacy | 22 | 4.5% | 53 | 0.0% |
| se-organisationsnummer | Gretel | 1 | 0.0% | 34 | 14.7% |
| uk-vehicle-registration | Nemotron, Gretel | 94 (licence plates) | 100.0% | 3 | 66.7% |

ai4privacy's IDCARD values are random runs without any country's format (its label table says so), so the Spanish
rules' recall cannot be measured here: they are recorded as not testable for recall. Elsewhere the checksums remove
almost every hit, and the hits on gold they remove are other values the pattern caught by chance (phone numbers,
customer ids).

Judged under the floor rule (mutation runs 20261013-095827 and 20261013-101635):

| checksum | verdict | false positives removed | finds lost |
|---|---|---|---|
| es-nif | accepted | 59 (Gretel 40, ai4privacy 19) | none |
| us-npi | accepted | 51 (Gretel 39, Nemotron 10, ai4privacy 2) | none |
| se-organisationsnummer | accepted | 29 (Gretel) | none |
| uk-vehicle-registration | accepted | 1 | none |
| es-nie | neutral | 0 | none |
| it-vat-code | rejected | 131 | 1 phone number (ai4privacy): PHONE gap worse |
| nhs | rejected | 0 | 1 phone number (Gretel): PHONE gap worse |
| the four accepted together | accepted | 140 (Gretel 109, ai4privacy 21, Nemotron 10) | none |

it-vat-code and nhs are rejected because each pattern happened to find one phone number the phone rule misses;
the floor rule does not trade a find for false positives. Porting the four into the plugin waits for the user.

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
