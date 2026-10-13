"""Whether the Claude Code sandbox denies reads of the vault home (TASK-45).

C8 matches Bash commands as text, so a command that builds the store's path at run time passes it. The sandbox's read
deny (`sandbox.credentials.files` with mode `deny`, or `sandbox.filesystem.denyRead`) is enforced by the operating
system for sandboxed commands. This module reads the settings layers (project, user, managed: later ones win) and
says whether that deny is configured; /maisecrets:status prints it. It cannot show what the running client enforces:
only a real session does (CLAUDE.md, Known traps).

Pure apart from reading the settings files."""
from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Layer:
    name: str        # project, user, managed
    data: dict
    root: Path       # what a relative path in it is relative to


@dataclass(frozen=True)
class Verdict:
    denied: bool
    reason: str
    source: str | None


def _managed_file() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path("/Library/Application Support/ClaudeCode/managed-settings.json")
    if system == "Windows":
        return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "ClaudeCode" / "managed-settings.json"
    return Path("/etc/claude-code/managed-settings.json")


def layers(config_dir: Path | None = None, project: Path | None = None,
           managed: Path | None = None) -> tuple[list[Layer], list[str]]:
    """The settings layers in the order they apply (a later one wins), and a line per file that could not be read."""
    config_dir = config_dir or Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    project = project or Path.cwd()
    files = [("project", project / ".claude" / "settings.json", project),
             ("project", project / ".claude" / "settings.local.json", project),
             ("user", config_dir / "settings.json", config_dir),
             ("managed", managed or _managed_file(), (managed or _managed_file()).parent)]
    out: list[Layer] = []
    problems: list[str] = []
    for name, path, root in files:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        except OSError as e:
            problems.append(f"{path}: not readable ({e.__class__.__name__})")
            continue
        try:
            data = json.loads(text)
        except ValueError:
            problems.append(f"{path}: not valid JSON")
            continue
        if isinstance(data, dict):
            out.append(Layer(name, data, root))
    return out, problems


def _resolve(raw: str, root: Path, home: Path) -> Path:
    if raw == "~" or raw.startswith("~/"):
        return Path(os.path.normpath(home / raw[2:])) if raw != "~" else home
    p = Path(raw)
    return Path(os.path.normpath(p if p.is_absolute() else root / p))


def _covers(path: Path, target: Path) -> bool:
    return target == path or path in target.parents


def verdict(stack: list[Layer], vault_home: Path, home: Path | None = None) -> Verdict:
    """Is the sandbox on, its filesystem layer on, and a read of vault_home denied? A later layer's value wins for
    `enabled` and `filesystem.disabled`; deny entries of every layer count (the client merges them)."""
    home = home or Path.home()
    enabled = None
    fs_off = False
    source = None
    for la in stack:
        sb = la.data.get("sandbox")
        if not isinstance(sb, dict):
            continue
        if isinstance(sb.get("enabled"), bool):
            enabled = sb["enabled"]
        fs = sb.get("filesystem") if isinstance(sb.get("filesystem"), dict) else {}
        if isinstance(fs.get("disabled"), bool):
            fs_off = fs["disabled"]
        paths = [e.get("path") for e in (sb.get("credentials") or {}).get("files", []) or []
                 if isinstance(e, dict) and e.get("mode", "deny") == "deny" and isinstance(e.get("path"), str)]
        paths += [p for p in fs.get("denyRead", []) or [] if isinstance(p, str)]
        if any(_covers(_resolve(p, la.root, home), vault_home) for p in paths):
            source = la.name
    if not enabled:
        return Verdict(False, "the sandbox is not enabled", None)
    if fs_off:
        return Verdict(False, "sandbox.filesystem.disabled turns the read denies off", None)
    if source is None:
        return Verdict(False, f"no read deny covers {vault_home}", None)
    return Verdict(True, "", source)


def line(v: Verdict) -> str:
    if v.denied:
        return f"sandbox read deny of the vault: on ({v.source} settings)"
    return (f"sandbox read deny of the vault: missing ({v.reason}); a Bash command that builds the store path at run "
            "time can read it (README, 'Not by the agent reading or changing the store')")
