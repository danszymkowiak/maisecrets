# redact: document redaction before a language model sees the text

**Decided with the user on 2026-10-12 (TASK-34).** `redact` is a command the user runs as data
prep: it extracts the text of documents known to hold personal data (PDF, CSV, Excel, plain
text; one file or a whole directory) and redacts it before the text goes to Claude. The plugin
redacts in the moment, fast and light; `redact` can afford local models and a human review,
because nobody waits for it in a prompt.

## What it never does

- It never changes the plugin. It lives in `redact/`, its own uv project (like `bench/`), and
  imports the plugin's detector from the same checkout; `maisecrets/` and `hooks/` import nothing
  of it and nothing outside the standard library (`redact/tests/test_skeleton.py`).
- It never sends text anywhere. Models run locally on the CPU; nothing goes to a remote API.
- It never reads the plugin's store or vault, and never modifies or overwrites its input.
- It never writes an output it could not redact: with no detector available it refuses.

## Pipeline

Pure functions (`redact/maisecrets_redact/pipeline.py`); the CLI only reads and writes files.

1. **Extract** (TASK-34.2): a document becomes text plus a map from text offsets back to its
   source (PDF page; sheet, row and column). Digital PDFs only, no OCR.
2. **Detect**: the plugin's deterministic rules first (TASK-34.3: secrets, IBAN, cards, e-mail,
   phone, country IDs, the terms file), then local PII models for what rules cannot find, such
   as names and free-form addresses (TASK-34.4, an optional extra). The models read the text
   with every rule hit already replaced by `[TYPE]`, so they never see a value the rules found;
   their spans map back to the original text.
3. **Decide** (TASK-34.5): a deterministic hit is redacted; a model span is redacted when every
   configured model agrees, and goes to a person's review otherwise.
4. **Render** (TASK-34.6): `<file>.redacted.txt`, or a mirrored tree for a directory, with
   placeholders of the plugin's kind (one value, one placeholder, across the run).

Reversible mode (`--reversible`, a vault of the placeholder map) is TASK-34.7 and waits on the
user's decision. A hook that redacts on read is out of scope: a post-read hook fires after the
text is already in the model's context.

## Use

```bash
redact statement.pdf                    # writes statement.pdf.redacted.txt next to it
redact lohn.xlsx --regions ch --drop-column Name
redact notes.txt --out ~/prep           # writes ~/prep/notes.txt.redacted.txt
redact ~/tax-2025 --recursive           # mirrors the tree into ~/tax-2025.redacted/
```

A directory run redacts every supported file and mirrors the tree into `<dir>.redacted/` (or
`--out`); subfolders only with `--recursive`. Unsupported files, a PDF without text and a link
that points outside the tree are skipped with one line each; an output inside the source tree is
refused; an output that exists is kept. One value keeps one placeholder across the whole run.

Each value becomes a placeholder of its type (`⟦IBAN_1⟧`, `⟦SECRET_2⟧`); the same value keeps the
same placeholder across a run. Without `--regions` the country rules of the person's maisecrets
config apply (it is only read), and the plugin's personal terms file applies too. An existing output
is never overwritten, and the input is never changed. The summary names counts per type, never a value.

## Review

With the model extra installed, a span the models disagree on goes to you. At a terminal `redact`
asks for each (redact or keep), showing its position, its type, which models found it and the
surrounding words, with every value masked. Without a terminal it writes
`<output>.review.json` with the same items and `"decision": null`; set each to `"redact"` or
`"keep"` and run again. Nothing is written while a decision is open (exit code 3), unless
`--no-review` redacts every disputed span. A review file belongs to one version of the document:
if the document changes, it is refused as stale.

## Models on the bench (TASK-34.8, 2026-10-12)

`uv run --project redact --with pyarrow python -m maisecrets_redact.measure` runs the rules and
each permissive model on 150 documents from each of four bench datasets (findocs, Gretel,
Nemotron-PII, Mendeley; `docs/BENCHMARK.md`). It writes only offsets under the bench's data
directory (run 20261012-161906, scored on findocs with names, birth dates and streets labelled,
TASK-36). A value counts as hidden when redacted spans cover 80 % of it. A false redaction is a
span that touches no positive gold value, counted per 1,000 words. CPU only.

| configuration | names | addresses | birth dates | phones | false / 1k words | s / doc |
|---|---|---|---|---|---|---|
| rules alone | 0.2% | 0% | 0% | 79% | 0.3 | 0.002 |
| rules + urchade/gliner_multi_pii-v1 | 87% | 73% | 100% | 99% | 5.6 | 0.62 |
| rules + fastino/gliner2-privacy-filter-PII-multi | 84% | 54% | 100% | 100% | 7.4 | 0.63 |
| rules + knowledgator/gliner-pii-base-v1.0 | 66% | 73% | 73% | 99% | 4.7 | 0.36 |
| rules + openai/privacy-filter | 84% | 69% | 0% | 96% | 12.2 | 1.13 |
| rules + gretelai/gretel-gliner-bi-large-v1.0 | 37% | 39% | 37% | 97% | 2.3 | 1.42 |
| vote of the defaults, no review | 64% | 53% | 73% | 96% | 2.0 | 1.6 |
| the same, every review answered yes | 90% | 91% | 100% | 98% | 10.7 | 1.6 |

The rules find what has a shape (IBAN, AHV, SSN, e-mail, cards) and nearly nothing of names or
addresses: the models are what this tool adds. The defaults are urchade, knowledgator and
fastino. openai/privacy-filter found no date of birth, so in the vote it vetoed every one, and
it took twice the time; gretel's bi-encoder finds too little. The models' false redactions are
mostly ID-shaped numbers and dates in financial forms. A vote of two models out of three instead
of all three hides 83 % of names and 85 % of addresses, at 4.4 false redactions per 1,000
words. Which vote is the default is a question for the user (TASK-17).

## Install

```bash
uv tool install --editable ./redact     # puts `redact` on PATH, imports the detector from this checkout
redact --help
uv run --project redact python -m unittest discover -s redact/tests
```

`MAISECRETS_REPO` points the tool at another checkout. Dependencies and model licences are listed
in `redact/README.md`; every one must hold for any user of the public repository, and a
restrictive one is opt-in.
