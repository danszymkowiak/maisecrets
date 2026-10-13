"""The encrypted file's key in the Secret Service (TASK-46, opt-in `key_store: "secret-service"`). On Linux the store
file and its key sat side by side in the vault home, so a backup or a copy of the disk held both (A4). With the
Secret Service the key leaves the home; without one the key file works as before. A key that moved is never replaced
silently: an unreachable Secret Service or a missing item fails closed (C12).

Every test runs a fake `secret-tool` (a script whose keyring is a file in a temp directory): no test reaches the
person's real keyring."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import vault  # noqa: E402
from maisecrets.vault import CodedError, EncryptedFileBackend  # noqa: E402

HOME = vault.HOME

FAKE = textwrap.dedent('''\
    #!{python}
    """A fake secret-tool: its keyring is a JSON file; FAKE_SS_MODE=down acts as no Secret Service."""
    import json, os, sys
    ring, mode = os.environ["FAKE_SS_RING"], os.environ.get("FAKE_SS_MODE", "up")
    with open(ring + ".argv", "a") as f:
        f.write(json.dumps(sys.argv[1:]) + "\\n")
    if mode == "down":
        sys.stderr.write("secret-tool: Cannot autolaunch D-Bus without X11 $DISPLAY\\n")
        sys.exit(1)
    data = json.load(open(ring)) if os.path.exists(ring) else {{}}
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "store":
        args = args[args.index("--label") + 2:] if "--label" in args else args
        secret = sys.stdin.read()
        data[json.dumps(args)] = secret[:-1] if mode == "corrupt" else secret
    elif cmd == "lookup":
        if json.dumps(args) not in data:
            sys.exit(1)
        sys.stdout.write(data[json.dumps(args)])
    elif cmd == "clear":
        data.pop(json.dumps(args), None)
    json.dump(data, open(ring, "w"))
''')


@unittest.skipIf(os.name == "nt" or shutil.which("openssl") is None, "the Secret Service is a Linux store; openssl")
class KeyStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ss-"))
        self.ring = self.tmp / "ring.json"
        tool = self.tmp / "secret-tool"
        tool.write_text(FAKE.format(python=sys.executable), encoding="utf-8")
        tool.chmod(0o755)
        HOME.mkdir(parents=True, exist_ok=True)
        for p in (mock.patch.object(vault, "SECRET_TOOL", str(tool)),
                  mock.patch.dict(os.environ, {"FAKE_SS_RING": str(self.ring), "FAKE_SS_MODE": "up"})):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self._clean)

    def _clean(self):
        for name in ("vault.enc.json", "key", vault.KEY_LOCATION):
            (HOME / name).unlink(missing_ok=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def mode(self, m: str):
        os.environ["FAKE_SS_MODE"] = m

    def ring_items(self) -> dict:
        return json.loads(self.ring.read_text()) if self.ring.exists() else {}

    def test_with_a_secret_service_the_key_is_not_in_the_vault_home(self):
        b = EncryptedFileBackend(key_store="secret-service")
        b.put("SECRET_c1", "ss-fake-value-1")
        self.assertEqual(b.get("SECRET_c1"), "ss-fake-value-1")
        self.assertFalse((HOME / "key").exists())
        self.assertEqual(len(self.ring_items()), 1)
        self.assertIn(str(HOME), next(iter(self.ring_items())), "the item names its vault home")
        self.assertEqual((HOME / vault.KEY_LOCATION).read_text().strip(), "secret-service")
        self.assertEqual(EncryptedFileBackend().get("SECRET_c1"), "ss-fake-value-1",
                         "the marker wins over the default: a moved key is found with key_store file too")

    def test_the_key_is_never_on_a_command_line(self):
        b = EncryptedFileBackend(key_store="secret-service")
        seen: list[list[str]] = []
        real = vault._run_store

        def spy(what, args, **kw):
            seen.append([str(a) for a in args])
            return real(what, args, **kw)
        with mock.patch.object(vault, "_run_store", spy):
            b.put("SECRET_c1", "ss-fake-value-2")
            b.get("SECRET_c1")
        key = next(iter(self.ring_items().values()))
        self.assertTrue(seen)
        self.assertFalse([a for a in seen if any(key in w for w in a)])

    def test_without_a_secret_service_the_key_file_works_as_before(self):
        for how in ("down", "no tool"):
            with self.subTest(how=how):
                self.mode("down" if how == "down" else "up")
                tool = vault.SECRET_TOOL if how == "down" else str(self.tmp / "no-such-tool")
                with mock.patch.object(vault, "SECRET_TOOL", tool):
                    b = EncryptedFileBackend(key_store="secret-service")
                    b.put("SECRET_c1", "ss-fake-value-3")
                    self.assertEqual(b.get("SECRET_c1"), "ss-fake-value-3")
                self.assertTrue((HOME / "key").exists())
                self.assertFalse((HOME / vault.KEY_LOCATION).exists())
                self.assertEqual(self.ring_items(), {})
                self._clean_store()

    def _clean_store(self):
        for name in ("vault.enc.json", "key", vault.KEY_LOCATION):
            (HOME / name).unlink(missing_ok=True)

    def test_an_existing_key_file_moves_into_the_secret_service_without_loss(self):
        old = EncryptedFileBackend()
        old.put("SECRET_c1", "ss-fake-value-4")
        key = (HOME / "key").read_text().strip()
        b = EncryptedFileBackend(key_store="secret-service")
        self.assertEqual(b.get("SECRET_c1"), "ss-fake-value-4")
        self.assertFalse((HOME / "key").exists())
        self.assertEqual(list(self.ring_items().values()), [key])
        b.put("SECRET_c2", "ss-fake-value-5")
        self.assertEqual(b.get("SECRET_c1"), "ss-fake-value-4")

    def test_a_copy_that_does_not_read_back_leaves_the_key_file(self):
        EncryptedFileBackend().put("SECRET_c1", "ss-fake-value-6")
        self.mode("corrupt")
        b = EncryptedFileBackend(key_store="secret-service")
        self.assertEqual(b.get("SECRET_c1"), "ss-fake-value-6")
        self.assertTrue((HOME / "key").exists())
        self.assertFalse((HOME / vault.KEY_LOCATION).exists())

    def test_a_moved_key_is_never_replaced_silently(self):
        b = EncryptedFileBackend(key_store="secret-service")
        b.put("SECRET_c1", "ss-fake-value-7")
        for how in ("down", "gone"):
            with self.subTest(how=how):
                if how == "down":
                    self.mode("down")
                else:
                    self.mode("up")
                    self.ring.write_text("{}")
                # a fresh backend each time: one keeps the key it read for its own life (one hook call)
                for op in (lambda: EncryptedFileBackend(key_store="secret-service").put("SECRET_c2", "ss-fake-8"),
                           lambda: EncryptedFileBackend(key_store="secret-service").get("SECRET_c1"),
                           lambda: EncryptedFileBackend().put("SECRET_c3", "ss-fake-value-9")):
                    with self.assertRaises(CodedError):
                        op()
                self.assertFalse((HOME / "key").exists(), "no new key file")
                self.assertEqual((HOME / vault.KEY_LOCATION).read_text().strip(), "secret-service")

    def test_wipe_clears_the_item_and_the_marker(self):
        b = EncryptedFileBackend(key_store="secret-service")
        b.put("SECRET_c1", "ss-fake-value-10")
        self.assertEqual(b.wipe(), 1)
        self.assertEqual(self.ring_items(), {})
        self.assertFalse((HOME / vault.KEY_LOCATION).exists())
        self.assertFalse((HOME / "vault.enc.json").exists())


class ConfigTests(unittest.TestCase):
    def test_make_backend_passes_the_key_store(self):
        b = vault.make_backend({"backend": "encrypted-file", "key_store": "secret-service"})
        self.assertEqual(b.key_store, "secret-service")
        self.assertEqual(vault.make_backend({"backend": "encrypted-file"}).key_store, "file")
        self.assertEqual(vault.DEFAULT_CONFIG["key_store"], "file")

    def test_an_unknown_key_store_is_refused(self):
        with self.assertRaises(ValueError):
            EncryptedFileBackend(key_store="tpm")


if __name__ == "__main__":
    unittest.main()
