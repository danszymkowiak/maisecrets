# redact

Extracts the text of documents and redacts personal data and secrets in it before the text goes
to a language model. Design and rules: `docs/REDACT.md`.

```bash
uv tool install --editable ./redact
redact --help
```

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

`uv sync --project redact --extra models` installs torch (CPU wheels), transformers and gliner
(all permissive). Models download once into the Hugging Face cache; nothing is sent to a remote
API. Licences as each model's Hugging Face record states them (read 2026-10-12):

| model | licence | default | note |
|---|---|---|---|
| [urchade/gliner_multi_pii-v1](https://huggingface.co/urchade/gliner_multi_pii-v1) | Apache-2.0 | yes | multilingual GLiNER for PII |
| [knowledgator/gliner-pii-base-v1.0](https://huggingface.co/knowledgator/gliner-pii-base-v1.0) | Apache-2.0 | yes | |
| [openai/privacy-filter](https://huggingface.co/openai/privacy-filter) | Apache-2.0 | yes | token classifier, 1.5B parameters, 50M active |
| [fastino/gliner2-privacy-filter-PII-multi](https://huggingface.co/fastino/gliner2-privacy-filter-PII-multi) | Apache-2.0 | no | needs the gliner2 backend (TASK-34.8) |
| [gretelai/gretel-gliner-bi-large-v1.0](https://huggingface.co/gretelai/gretel-gliner-bi-large-v1.0) | Apache-2.0 | no | |
| [nvidia/gliner-PII](https://huggingface.co/nvidia/gliner-PII) | NVIDIA Open Model License | opt-in | for clinical text; not an OSI licence |
| [iiiorg/piiranha-v1-detect-personal-information](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) | CC BY-NC-ND 4.0 | opt-in | non-commercial, no derivatives |

An opt-in model runs only with `--accept-model-terms <model id>`, after you have read its terms.
The defaults are provisional: TASK-34.8 measures them on the bench and settles the set.
