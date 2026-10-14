# redact

Extracts the text of documents and redacts personal data and secrets in it before the text goes
to a language model. Design and rules: `docs/REDACT.md`.

```bash
uv tool install --python 3.12 --editable ./redact               # the rules only
uv tool install --python 3.12 --editable './redact[models]' --force   # with the local PII models (about 1 GB)
redact --help
```

A table comes out as a table: `people.csv` as `people.csv.redacted.csv` (same delimiter, the
header row kept), a workbook as one `lohn.xlsx.<sheet>.redacted.csv` per sheet. A PDF or a text
file, a HAR, a vCard or an iCalendar file comes out as `<file>.redacted.txt`. An existing output is never overwritten.

## Dependencies and licences

Every dependency and model must be usable by anyone who runs the public repository; one with
restrictive terms is opt-in and named here with them.

| dependency | used for | licence | default |
|---|---|---|---|
| pypdf (6.x) | text of digital PDFs | BSD-3-Clause | yes |
| openpyxl (3.1) | Excel workbooks (values, not formulas) | MIT | yes |
| et-xmlfile (2.x, via openpyxl) | XML for openpyxl | MIT | yes |

PyMuPDF was not taken: it is AGPL-3.0, too strong a condition for a public Apache-2.0 repository.

## Local PII models (optional extra)

`uv sync --project redact --extra models` installs torch (CPU wheels), transformers, gliner,
gliner2 with its `local` extra, sentencepiece and protobuf (all permissive). Models download once
into the Hugging Face cache; nothing is sent to a remote API. gliner2 also ships a client for
Fastino's hosted API; the tool uses only its local model class. Licences as each model's Hugging Face record states them (read 2026-10-12):

| model | licence | default | note |
|---|---|---|---|
| [urchade/gliner_multi_pii-v1](https://huggingface.co/urchade/gliner_multi_pii-v1) | Apache-2.0 | yes | multilingual GLiNER for PII; finds the most names alone |
| [knowledgator/gliner-pii-base-v1.0](https://huggingface.co/knowledgator/gliner-pii-base-v1.0) | Apache-2.0 | yes | |
| [openai/privacy-filter](https://huggingface.co/openai/privacy-filter) | Apache-2.0 | yes | token classifier, 1.5B parameters, 50M active: another architecture than the GLiNERs; a span only it finds is dropped, not reviewed |
| [fastino/gliner2-privacy-filter-PII-multi](https://huggingface.co/fastino/gliner2-privacy-filter-PII-multi) | Apache-2.0 | yes | GLiNER2, asked in its own label names |
| [gretelai/gretel-gliner-bi-large-v1.0](https://huggingface.co/gretelai/gretel-gliner-bi-large-v1.0) | Apache-2.0 | no | |
| [nvidia/gliner-PII](https://huggingface.co/nvidia/gliner-PII) | NVIDIA Open Model License | opt-in | for clinical text; not an OSI licence |
| [iiiorg/piiranha-v1-detect-personal-information](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) | CC BY-NC-ND 4.0 | opt-in | non-commercial, no derivatives |

An opt-in model runs only with `--accept-model-terms <model id>`, after you have read its terms.
The defaults were chosen on the bench datasets (TASK-34.8); `docs/REDACT.md` has the numbers.
