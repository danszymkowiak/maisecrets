"""A generated tool-output dataset (docs/BENCHMARK.md, Synthetic tool output): what a coding agent sees in a terminal,
which the file and prose corpora do not hold. Each sample is one template (printenv, git diff, grep -n, cat -n,
kubectl get secret, docker config, curl -v, lockfiles, docker images --digests) filled from a fixed seed. Secrets
and personal data are pos spans; digests, UUIDs, commit ids and integrity strings are neg spans. Every value comes
from a generator of the rule's shape and the seed: no real token, nothing downloaded."""
from __future__ import annotations

import base64
import hashlib
import json
import random
import string
from pathlib import Path
from typing import Callable, Iterator

from ..labels import LabelTable
from ..schema import Sample, Span
from ..split import split_of

DATASET = "synthetic"
SEED = 20261011
PER_TEMPLATE = 300
ALNUM = string.ascii_letters + string.digits
B64URL = ALNUM + "-_"


def version() -> str:
    """The seed, the size and this file: a change to a generator builds the dataset again."""
    h = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    return f"seed{SEED}-n{PER_TEMPLATE}-{h}"


class Doc:
    """Text built piece by piece; pos() and neg() record the span of the piece they add."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.n = 0
        self.spans: list[tuple[int, int, str, str]] = []

    def add(self, s: str) -> "Doc":
        self.parts.append(s)
        self.n += len(s)
        return self

    def pos(self, value: str, label: str) -> "Doc":
        self.spans.append((self.n, self.n + len(value), label, "pos"))
        return self.add(value)

    def neg(self, value: str, label: str) -> "Doc":
        self.spans.append((self.n, self.n + len(value), label, "neg"))
        return self.add(value)

    @property
    def text(self) -> str:
        return "".join(self.parts)


class Gen:
    """Rule-shaped values from one seeded random source."""

    def __init__(self, rnd: random.Random) -> None:
        self.r = rnd

    def s(self, alphabet: str, n: int) -> str:
        return "".join(self.r.choice(alphabet) for _ in range(n))

    def hexs(self, n: int) -> str:
        return self.s("0123456789abcdef", n)

    # secrets
    def github(self) -> str:
        return "gh" + "p_" + self.s(ALNUM, 36)

    def gitlab(self) -> str:
        return "gl" + "pat-" + self.s(ALNUM + "-_", 20)

    def aws_id(self) -> str:
        return "AK" + "IA" + self.s(string.ascii_uppercase + "234567", 16)

    def aws_secret(self) -> str:
        return self.s(ALNUM + "/+", 40)

    def slack(self) -> str:
        return "xo" + "xb-" + self.s(string.digits, 12) + "-" + self.s(string.digits, 13) + "-" + self.s(ALNUM, 24)

    def stripe(self) -> str:
        return "sk" + "_live_" + self.s(ALNUM, 24)

    def npm(self) -> str:
        return "np" + "m_" + self.s(ALNUM, 36)

    def password(self) -> str:
        return self.s(ALNUM, 10) + self.r.choice("!#%&*+-=?@^") + self.s(ALNUM, 7)

    def jwt(self) -> str:
        def b64(d: dict) -> str:
            return base64.urlsafe_b64encode(json.dumps(d, separators=(",", ":")).encode()).decode().rstrip("=")
        payload = {"sub": self.s(string.digits, 8), "iat": 1700000000 + self.r.randrange(10 ** 7)}
        return b64({"alg": "HS256", "typ": "JWT"}) + "." + b64(payload) + "." + self.s(B64URL, 43)

    def secret(self) -> tuple[str, str]:
        kind = self.r.choice(["github", "gitlab", "aws_secret", "slack", "stripe", "password", "jwt"])
        return getattr(self, kind)(), kind

    # personal data
    def email(self) -> str:
        user = self.s(string.ascii_lowercase, self.r.randrange(4, 9)) + self.r.choice(["", ".", "_"]) + \
            self.s(string.ascii_lowercase, self.r.randrange(3, 7))
        domain = self.s(string.ascii_lowercase, self.r.randrange(5, 10))
        return f"{user.strip('._')}@{domain}.{self.r.choice(['com', 'net', 'io', 'de'])}"

    def ipv4(self) -> str:
        first = self.r.choice([23, 34, 52, 81, 93, 104, 151, 185, 203])
        return ".".join(str(x) for x in (first, self.r.randrange(256), self.r.randrange(256), self.r.randrange(1, 255)))

    def phone(self) -> str:
        return f"+1 {self.r.randrange(201, 990)} {self.r.randrange(200, 999)} {self.r.randrange(1000, 9999)}"

    # negatives
    def sha256(self) -> str:
        return self.hexs(64)

    def commit(self) -> str:
        return self.hexs(40)

    def uuid(self) -> str:
        h = self.hexs(32)
        return f"{h[:8]}-{h[8:12]}-4{h[13:16]}-{self.r.choice('89ab')}{h[17:20]}-{h[20:]}"

    def integrity(self) -> str:
        return "sha512-" + base64.b64encode(self.r.randbytes(64)).decode()

    def go_sum(self) -> str:
        return "h1:" + base64.b64encode(self.r.randbytes(32)).decode()

    def object_id(self) -> str:
        return self.hexs(24)


SECRET_NAMES = ["DATABASE_PASSWORD", "API_TOKEN", "GITHUB_TOKEN", "SECRET_KEY", "STRIPE_KEY", "SLACK_TOKEN",
                "AUTH_TOKEN", "AWS_SECRET_ACCESS_KEY"]
PLAIN_ENV = [("HOME", "/home/dev"), ("SHELL", "/bin/bash"), ("LANG", "en_US.UTF-8"), ("TERM", "xterm-256color"),
             ("PATH", "/usr/local/bin:/usr/bin:/bin"), ("EDITOR", "vim"), ("NODE_ENV", "production")]


def t_printenv(g: Gen) -> Doc:
    d = Doc()
    rows = [("plain", k, v) for k, v in g.r.sample(PLAIN_ENV, 4)]
    rows += [("secret", g.r.choice(SECRET_NAMES), None) for _ in range(g.r.randrange(1, 4))]
    rows += [("mail", "GIT_AUTHOR_EMAIL", None), ("sha", "BUILD_SHA", None)]
    g.r.shuffle(rows)
    for kind, k, v in rows:
        d.add(f"{k}=")
        if kind == "plain":
            d.add(v)
        elif kind == "secret":
            d.pos(g.secret()[0], "SECRET")
        elif kind == "mail":
            d.pos(g.email(), "EMAIL")
        else:
            d.neg(g.commit(), "COMMIT")
        d.add("\n")
    return d


def t_git_diff(g: Gen) -> Doc:
    d = Doc().add("commit ").neg(g.commit(), "COMMIT").add("\nAuthor: Dev <").pos(g.email(), "EMAIL")
    d.add(">\n\ndiff --git a/config/settings.py b/config/settings.py\nindex ").neg(g.hexs(7), "COMMIT")
    d.add("..").neg(g.hexs(7), "COMMIT").add(" 100644\n--- a/config/settings.py\n+++ b/config/settings.py\n")
    key = "API_" + "KEY"     # split: the tree scan reads a keyword and a value in one literal as a secret
    d.add(f"@@ -10,3 +10,4 @@\n DEBUG = False\n-{key} = os.environ[\"{key}\"]\n+{key} = \"")
    d.pos(g.secret()[0], "SECRET").add("\"\n ALLOWED_HOSTS = [\"*\"]\n")
    return d


def t_grep(g: Gen) -> Doc:
    d = Doc()
    for i in range(g.r.randrange(2, 5)):
        path = g.r.choice(["src/app.ts", "deploy/.env.prod", "scripts/sync.sh", "README.md"])
        d.add(f"{path}:{g.r.randrange(1, 400)}:")
        if i == 0 or g.r.random() < 0.4:
            d.add(g.r.choice(["token: ", "export SECRET_KEY=", "password = \"", "Authorization: Bearer "]))
            d.pos(g.secret()[0], "SECRET")
        else:
            d.add("const requestId = \"").neg(g.uuid(), "UUID").add("\";")
        d.add("\n")
    return d.add("src/trace.ts:12:const traceId = \"").neg(g.uuid(), "UUID").add("\";\n")


def t_cat_n(g: Gen) -> Doc:
    d = Doc()
    lines = [("[database]", None), ("host = db.internal", None), ("user = app", None), ("password = ", "secret"),
             ("", None), ("[owner]", None), ("contact = ", "mail"), ("[build]", None), ("checksum = ", "sha")]
    for n, (line, kind) in enumerate(lines, 1):
        d.add(f"{n:6}\t{line}")
        if kind == "secret":
            d.pos(g.password(), "SECRET")
        elif kind == "mail":
            d.pos(g.email(), "EMAIL")
        elif kind == "sha":
            d.neg(g.sha256(), "DIGEST")
        d.add("\n")
    return d


def t_kubectl(g: Gen) -> Doc:
    d = Doc().add("apiVersion: v1\ndata:\n  password: ")
    d.pos(base64.b64encode(g.password().encode()).decode(), "SECRET").add("\n  token: ")
    d.pos(base64.b64encode(g.secret()[0].encode()).decode(), "SECRET")
    d.add("\nkind: Secret\nmetadata:\n  name: app-credentials\n  uid: ").neg(g.uuid(), "UUID")
    d.add("\n  resourceVersion: \"").add(str(g.r.randrange(10 ** 6, 10 ** 7))).add("\"\ntype: Opaque\n")
    return d


def t_docker_config(g: Gen) -> Doc:
    user = g.s(string.ascii_lowercase, 6)
    auth = base64.b64encode(f"{user}:{g.password()}".encode()).decode()
    d = Doc().add('{\n  "auths": {\n    "registry.example.com": {\n      "auth": "').pos(auth, "SECRET")
    d.add('"\n    }\n  },\n  "credsStore": "desktop",\n  "plugins": {"buildx": {"digest": "sha256:')
    d.neg(g.sha256(), "DIGEST").add('"}}\n}\n')
    return d


def t_curl(g: Gen) -> Doc:
    d = Doc().add("*   Trying ").pos(g.ipv4(), "IP").add(":443...\n* Connected\n> GET /v1/me HTTP/2\n")
    d.add("> Host: api.service.io\n> Authorization: Bearer ").pos(g.secret()[0], "SECRET")
    d.add("\n> User-Agent: curl/8.5.0\n>\n< HTTP/2 200\n< x-request-id: ").neg(g.uuid(), "UUID")
    d.add("\n< etag: \"").neg(g.hexs(32), "DIGEST").add("\"\n<\n{\"email\": \"").pos(g.email(), "EMAIL")
    d.add("\", \"phone\": \"").pos(g.phone(), "PHONE").add("\"}\n")
    return d


def t_package_lock(g: Gen) -> Doc:
    d = Doc().add("$ cat .npmrc\n//registry.npmjs.org/:_authToken=").pos(g.npm(), "SECRET")
    d.add('\n$ cat package-lock.json\n{\n  "name": "web",\n  "lockfileVersion": 3,\n  "packages": {\n')
    for _ in range(g.r.randrange(2, 5)):
        name = g.s(string.ascii_lowercase, g.r.randrange(4, 9))
        d.add(f'    "node_modules/{name}": {{\n      "version": "{g.r.randrange(1, 9)}.{g.r.randrange(20)}.0",\n')
        d.add(f'      "resolved": "https://registry.npmjs.org/{name}/-/{name}.tgz",\n      "integrity": "')
        d.neg(g.integrity(), "INTEGRITY").add('"\n    },\n')
    return d.add("  }\n}\n")


def t_go_sum(g: Gen) -> Doc:
    d = Doc().add("$ cat ~/.netrc\nmachine github.com login dev password ").pos(g.github(), "SECRET")
    d.add("\n$ cat go.sum\n")
    for _ in range(g.r.randrange(2, 5)):
        mod = "github.com/" + g.s(string.ascii_lowercase, 6) + "/" + g.s(string.ascii_lowercase, 5)
        d.add(f"{mod} v1.{g.r.randrange(20)}.0 ").neg(g.go_sum(), "INTEGRITY").add("\n")
    return d


def t_docker_images(g: Gen) -> Doc:
    d = Doc().add("REPOSITORY   TAG       DIGEST                                                                    "
                  "IMAGE ID       SIZE\n")
    for _ in range(g.r.randrange(2, 4)):
        d.add(g.r.choice(["nginx", "postgres", "redis"]) + "        latest    sha256:").neg(g.sha256(), "DIGEST")
        d.add("   ").neg(g.hexs(12), "DIGEST").add("   187MB\n")
    d.add("$ docker run -e POSTGRES_PASSWORD=").pos(g.password(), "SECRET").add(" postgres\n")
    d.add("# mongo shell\n> db.users.findOne({_id: ObjectId(\"").neg(g.object_id(), "OBJECT_ID").add("\")})\n")
    return d


TEMPLATES: dict[str, Callable[[Gen], Doc]] = {
    "printenv": t_printenv, "git_diff": t_git_diff, "grep": t_grep, "cat_n": t_cat_n, "kubectl": t_kubectl,
    "docker_config": t_docker_config, "curl": t_curl, "package_lock": t_package_lock, "go_sum": t_go_sum,
    "docker_images": t_docker_images,
}


def samples(table: LabelTable, per_template: int = PER_TEMPLATE, seed: int = SEED) -> Iterator[Sample]:
    g = Gen(random.Random(seed))
    for name, template in TEMPLATES.items():
        for i in range(per_template):
            d = template(g)
            sid = f"{name}:{i}"
            spans = [Span(a, b, label, table.type_of(label), gold) for a, b, label, gold in d.spans]
            yield Sample(DATASET, sid, sid, "en", d.text, spans, split_of(DATASET, sid))
