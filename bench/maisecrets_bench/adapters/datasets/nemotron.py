"""nvidia/Nemotron-PII (docs/BENCHMARK.md, TASK-11.34): synthetic English documents of 50+ industries, CC-BY-4.0, not
gated, so the licence holds for anyone who runs the bench. One sample per record of the test split (100,000: 50,000
us and 50,000 intl locale; the train split is the same generator and stays out). Its spans are the gold; unlabelled
text is negative. The spans column is a Python literal: it is read with ast.literal_eval, never run.

A span's own text differs from the text at its offsets only in case or type in the data (black over Black, the
number 42 for "42"); such a span is kept. A span outside the text, or over other text, is dropped and counted.
Locale and document format become tags (locale:us, format:structured), which the report scores apart. Every uid
has a us and an intl record with different text: the sample id is locale:uid, and the uid is the group, so both
records land in the same split."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterable, Iterator

from ...domain.labels import LabelTable
from ...domain.bench_error import BenchError
from ...domain.samples import Sample, Span
from ...domain.split import split_of

DATASET = "nemotron"
HF_ID = "nvidia/Nemotron-PII"
SPLITS = ("test",)
REVISION = "locale-uid"     # part of the version: a change here builds the parquet again
# every label of the data (both splits, revision b70ffaf5): the table must map each one
LABELS = {
    "account_number", "age", "api_key", "bank_routing_number", "biometric_identifier", "blood_type",
    "certificate_license_number", "city", "company_name", "coordinate", "country", "county", "credit_debit_card",
    "customer_id", "cvv", "date", "date_of_birth", "date_time", "device_identifier", "education_level", "email",
    "employee_id", "employment_status", "fax_number", "first_name", "gender", "health_plan_beneficiary_number",
    "http_cookie", "ipv4", "ipv6", "language", "last_name", "license_plate", "mac_address", "medical_record_number",
    "national_id", "occupation", "password", "phone_number", "pin", "political_view", "postcode", "race_ethnicity",
    "religious_belief", "sexuality", "ssn", "state", "street_address", "swift_bic", "tax_id", "time", "unique_id",
    "url", "user_name", "vehicle_identifier",
}


@dataclass
class Stats:
    dropped: int = 0


def _spans(sid: str, raw: str) -> list:
    try:
        got = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        raise BenchError(f"{DATASET}: {sid}: the spans column is not a literal list") from None
    if not isinstance(got, list):
        raise BenchError(f"{DATASET}: {sid}: the spans column is not a list")
    return got


def samples(records: Iterable[dict], table: LabelTable, stats: Stats) -> Iterator[Sample]:
    for r in records:
        sid = f"{r['locale']}:{r['uid']}"     # a uid has a us and an intl record; both go to the uid's split
        text = r["text"]
        spans = []
        for m in _spans(sid, r["spans"]):
            t = table.type_of(m["label"])
            if not 0 <= m["start"] < m["end"] <= len(text) or \
                    text[m["start"]:m["end"]].lower() != str(m["text"]).lower():
                stats.dropped += 1
                continue
            spans.append(Span(m["start"], m["end"], m["label"], t, "pos"))
        spans.sort(key=lambda s: (s.start, s.end))
        yield Sample(DATASET, sid, r["uid"], "en", text, spans, split_of(DATASET, r["uid"]),
                     [f"locale:{r['locale']}", f"format:{r['document_format']}"])


def records(cache_dir: str, revision: str | None = None) -> Iterator[dict]:
    """The records of SPLITS, downloaded once into the bench's cache."""
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    for split in SPLITS:
        path = hf_hub_download(HF_ID, f"data/{split}-00000-of-00001.parquet", repo_type="dataset",
                               cache_dir=cache_dir, revision=revision)
        cols = ["uid", "locale", "document_format", "text", "spans"]
        for r in pq.read_table(path, columns=cols).to_pylist():
            yield {**r, "_split": split}
