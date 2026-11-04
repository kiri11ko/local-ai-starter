# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file, stdlib-only Python wizard (`local_ai_starter.py`) that downloads a pinned
llama.cpp build plus a Qwen GGUF model, runs `llama-server` on `127.0.0.1`, and opens the
built-in web chat — or prepares an OpenCode demo project wired to the local server. Target
users are non-technical, so everything is interactive (numbered options, Enter = default),
and all on-screen text, code comments and commit messages are in Russian. The three
`Запустить Local AI Starter.*` files are thin per-OS launchers that only find Python and run
the script.

## Commands

There is no build, linter config or test suite. Useful checks:

```bash
python3 -m py_compile local_ai_starter.py                      # syntax check
# Walk the whole flow without downloading or starting anything, in a throwaway data dir:
LOCAL_AI_STARTER_DRY_RUN=1 LOCAL_AI_STARTER_HOME="$(mktemp -d)" python3 local_ai_starter.py
```

- `LOCAL_AI_STARTER_DRY_RUN=1` — downloads, installs and server start are printed as
  `[dry-run] …` instead of executed.
- `LOCAL_AI_STARTER_HOME` — overrides the data dir (default: `local-ai/` next to the script,
  git-ignored). Use it so manual runs don't touch a real install.

Real end-to-end verification is manual (checklist in README: clean start → answer → restart →
stop → delete everything; interrupted download, busy port 8080, low disk, OpenCode tool calls).

## Architecture

- **Entry (`main`)**: if `bin/llama-server` exists → management `menu()`, otherwise
  `first_run()` (purpose → `choose_profile` by RAM/disk → plan → confirm → install → `bring_up`).
  `RuntimeError`/`OSError`/`URLError`/`CalledProcessError` are caught in `main` and shown as
  `Ошибка: …` — raise `RuntimeError` with a user-readable Russian message for expected failures;
  `Cancelled` means the user backed out.
- **Profiles (`PROFILES`)**: each maps to an `-hf repo:quant` spec; llama-server downloads the
  model itself into `models/` via `LLAMA_CACHE`. The profile `key` is also the server `--alias`
  and the OpenCode model id.
- **Engine pinning**: `LLAMA_BUILD` + `LLAMA_SHA256` (one hash per platform key from
  `llama_platform()`). Bumping the build means updating all six hashes from the release page.
  `extract()` strips the archive's top folder, guards against path traversal, and re-adds the
  exec bit (zip loses modes).
- **Server lifecycle**: `start_server` spawns detached (new session / `DETACHED_PROCESS`),
  logs to `server.log`, and records `pid/port/profile` in `state.json` (atomic write via `.tmp`).
  `wait_ready` polls `/health` (up to an hour — first run includes the model download), then
  sends a test `/v1/chat/completions` request. `bring_up` reuses a healthy server with the same
  profile, otherwise stops it and picks a free port starting at 8080.
- **OpenCode**: never touches the user's global setup — the official installer runs with
  `HOME` overridden to `local-ai/opencode-home`, and the provider config lives only in
  `demo-project/opencode.json` (`@ai-sdk/openai-compatible` → local server). Not installed on
  Windows.

## Constraints to keep

- Python 3.9+ and stdlib only (no third-party deps; `X | None` is fine only in annotations,
  thanks to `from __future__ import annotations`).
- Nothing outside the data dir: no PATH/shell-config/global-config changes; server binds
  `127.0.0.1` only.
- Cross-platform branches matter: on Windows `os.kill(pid, 0)` kills the process, so
  `pid_alive` uses `tasklist`; stopping uses `taskkill /T` vs `killpg`.
- `README.md` (English, primary) and `README.ru.md` must be kept in sync.
