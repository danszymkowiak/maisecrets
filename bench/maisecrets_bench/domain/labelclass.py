"""The label before a value by word sets (TASK-11.23), as Bandit and CodeQL read it. The label is split into words
(camelCase, snake_case, kebab-case, dots); then:

- negative: the last word names something derived from a secret or a measure of it (token_count, password_hash,
  secret_path), or the label is a word that only contains a secret word (tokenizer, secretary, passwordless);
- strong: the last word is a secret word (password, token, secret, passphrase), or the last two are a secret pair
  (api key, private key, access key, client secret, auth token);
- weak: a weaker word is in the label (key, auth, credential, pass);
- none: nothing of the above.

One table; the bench filters (filters.py) bench:label_negative drops a negative label's hit, and
bench:label_weak_entropy also asks a weak one for entropy."""
from __future__ import annotations

import re

STRONG_LAST = {"password", "passwd", "pwd", "passphrase", "secret", "token", "apikey", "passwort", "kennwort"}
STRONG_PAIRS = {("api", "key"), ("private", "key"), ("access", "key"), ("secret", "key"), ("client", "secret"),
                ("auth", "token"), ("access", "token"), ("refresh", "token"), ("master", "key")}
WEAK = {"key", "auth", "credential", "credentials", "pass", "pw", "cred", "creds", "signature"}
NEGATIVE_LAST = {"count", "max", "min", "hash", "hashed", "path", "url", "uri", "length", "len", "file",
                 "filename", "name", "type", "size", "ttl", "timeout", "expiry", "expires", "version", "policy",
                 "prefix", "suffix", "field", "header", "param", "env", "var", "label", "placeholder", "format",
                 "pattern", "regex", "limit", "endpoint", "provider", "store", "manager", "service", "helper"}
NEGATIVE_WHOLE = {"tokenizer", "tokenize", "tokens", "secretary", "passwordless", "keyboard", "keyword", "keywords",
                  "keystore", "keychain", "author", "authority", "passenger", "bypass"}
# not negative, measured on dev of run 20261011-220740: a value after `passport` (94 finds, 39 false alarms), `id` (40 /
# 17) and `passage` (5 / 0) is mostly a real one (a passport number, an account id), whatever the keyword rule meant


def words(label: str) -> list[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", label)
    return [w.lower() for w in re.findall(r"[A-Za-z]+", spaced)]


def classify(label: str) -> str:
    ws = words(label)
    if not ws:
        return "none"
    last = ws[-1]
    if last in NEGATIVE_LAST or last in NEGATIVE_WHOLE:
        return "negative"
    if last in STRONG_LAST or tuple(ws[-2:]) in STRONG_PAIRS:
        return "strong"
    if any(w in WEAK for w in ws):
        return "weak"
    return "none"
