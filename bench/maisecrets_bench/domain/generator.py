"""Seeded generators of the values the generated datasets hold (synthetic tool output, findocs): text built piece by
piece with its spans, and values of each rule's shape. Pure: one seed gives the same text on every machine."""
from __future__ import annotations

import base64
import json
import random
import string


ALNUM = string.ascii_letters + string.digits
B64URL = ALNUM + "-_"


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
        """North American numbering plan: area code N[0-8]X (a middle 9 is reserved), exchange NXX (TASK-30)."""
        area = f"{self.r.randrange(2, 10)}{self.r.randrange(0, 9)}{self.r.randrange(0, 10)}"
        return f"+1 {area} {self.r.randrange(200, 1000)} {self.r.randrange(1000, 10000)}"

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
