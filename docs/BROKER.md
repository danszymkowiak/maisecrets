# A broker process around the store (design note, TASK-47)

Status: a note for a decision, nothing built. Requested by the user on 2026-10-13 ("strengthen the vault").

## Why

Every maisecrets hook, the agent's commands and every other program of the person run as the same user. The store
therefore answers any of them (THREAT-MODEL C12, "not A3"), and C8 only matches command text, so a command that
builds the store's path at run time reads it ("a backstop, not a boundary; a hard boundary needs a broker process").
Two cheaper steps come first and close most of the agent's path:

- TASK-45: the Claude Code sandbox with a read deny of the vault home. A sandboxed command cannot read the store,
  however it builds the path.
- TASK-46: on Linux the store's key leaves the store directory, so a copy of the disk or a backup no longer holds
  key and ciphertext side by side.

What remains after both: a command the agent runs outside the sandbox (the escape hatch, unless
`allowUnsandboxedCommands` is false), a tool the sandbox does not cover (an MCP server, a file tool that C8 does not
catch), and any other program of the person (A3).

## What a broker is

A small process that alone can open the store, running under an identity the person's programs do not have:

| OS | identity | how hooks reach it | what the OS checks |
|---|---|---|---|
| Linux | a system user (`maisecrets`), a systemd service with socket activation | a Unix socket, group-restricted | `SO_PEERCRED`: uid and pid of the caller |
| macOS | a LaunchDaemon under a dedicated user, or a signed per-user helper on the data-protection keychain | a Unix socket, or XPC | `getpeereid`, or the helper's code signature (XPC) |
| Windows | a service account | a named pipe with an ACL | `GetNamedPipeClientProcessId`, the token |

The store's files (or keychain items) belong to the broker's identity. A hook asks over the socket: "resolve
`SECRET_c3` for session S, tool T, command C". The broker applies the gates and answers with the value or a refusal.
The value then goes the way it goes today (C5: once through a FIFO the command reads first).

## What moves into the broker

- **C4 (session rule)**: the admissions (typed, minted, seen in a tool result) are recorded in the broker, not in an
  index the person's processes can edit.
- **C7 (limiter)**: the counts live in the broker; a process cannot reset them by editing `index.json`.
- **C9 (audit)**: the audit log is written by the broker, append-only for everyone else, so it can no longer be
  rewritten by the same user it records.
- **C10 (keyed fingerprints)**: the HMAC key never leaves the broker; the index the hooks read holds fingerprints
  only.
- **C12 (store)**: unchanged backends, but owned by the broker's identity.

## What it still does not stop

The hard part: the broker can tell which user calls, not which program of that user. A hook and an agent-run command
are the same uid. So:

- **A3 asking the broker as if it were a hook.** Any program of the person can open the socket and send the same
  request a hook sends. The session rule helps only as far as the program knows a session id and a key it was
  admitted to. Closing this needs one of: the sandbox denying the socket path to the agent's commands (the hooks run
  outside the sandbox, so they still reach it); or a user-presence check per resolve (Touch ID, a polkit prompt,
  Windows Hello), which turns every resolve into a dialog.
- **A5, the person**, and anyone with the person's administrator rights, who can stop the service or read its files.
- **A value after it left the broker**: the FIFO window of C5, the command's own handling of the value.

## What it costs

- An install that needs administrator rights on every OS (a system user or service account, a service, a socket
  with an ACL). A Claude Code or Codex plugin cannot do that by itself: it becomes a separate installer, and the
  plugin falls back to today's direct store access when no broker runs.
- A second component to release, sign (macOS XPC, Windows service) and update in step with the hooks; a broker that
  is down must fail closed (no value) and say so.
- A protocol with its own tests, and a harness scenario per OS; the measurements in a real sandbox (CLAUDE.md, Known
  traps) repeat for every route.
- Latency: one socket round trip per resolve (small next to today's hook start).

## Recommendation

Do TASK-45 and TASK-46 first and measure what they leave. Build a broker only if the remaining case matters: the
agent's unsandboxed commands, tools outside the sandbox, or other programs of the person reading values. If it does,
start with Linux (a systemd socket and `SO_PEERCRED` are the least work) and the sandbox deny of the socket path,
and leave user presence per resolve as an option, since it costs a dialog on every value.
