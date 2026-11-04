# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file, stdlib-only Python wizard (`local_ai_starter.py`): one double-click
(`RunMe.command` / `RunMe.sh` / `RunMe.bat`) downloads a pinned llama.cpp build, a Qwen GGUF
model and a pinned OpenCode CLI, starts `llama-server` on `127.0.0.1`, and opens OpenCode in the
same terminal in `local-ai/workspace`. Target users are non-technical: arrow-key menus,
Enter = recommended option. Code, comments and launchers are English. User-facing text lives
only in `STRINGS` (`en` + `ru`, picked from the system locale). The wiki and commit messages are Russian.

## Commands

There is no build, linter config or test suite. Useful checks:

```bash
python3 -m py_compile local_ai_starter.py          # syntax; system python3 here is 3.9 = minimum
# Whole flow without downloads or server start, in a throwaway data dir:
LOCAL_AI_STARTER_DRY_RUN=1 LOCAL_AI_STARTER_HOME="$(mktemp -d)" LOCAL_AI_STARTER_LANG=en ./RunMe.sh
./RunMe.sh --menu                                   # management menu only
```

- `LOCAL_AI_STARTER_DRY_RUN=1`: downloads, installs and process starts are printed as `[dry-run] …`.
- `LOCAL_AI_STARTER_HOME`: data dir instead of `local-ai/` next to the script (git-ignored).
- `LOCAL_AI_STARTER_LANG=en|ru`: force the UI language.
- Piped stdin, or a terminal without ANSI support, switches menus to numbered `input()`.
  That is how to script the dry run: `printf '\n\n1\n' | …`.
- To test installs without the network, serve archives with `python3 -m http.server` and
  override `LLAMA_URL` / `OPENCODE_URL` from a `python3 -c 'import local_ai_starter as m; …'`.
- Real model runs download GB-sized weights: warn the user before starting one.

## Architecture

- **Flow (`main` → `run_opencode` → `menu`)**: every run goes through `ensure_installed()`.
  It asks for a profile only if none is saved, plans only the missing pieces, then runs
  `check_network()`, downloads, `bring_up()` and `launch_opencode()`. After OpenCode exits,
  the management menu opens. `--menu` skips straight to it.
- **Errors**: raise `RuntimeError` with a `t(...)` message for expected failures and
  `NetworkError` for unreachable hosts. `network_error()` explains the cause (timeout / DNS /
  refused / TLS / HTTP; 404 means the pin is gone, not that the network is blocked).
  `Cancelled` means the user backed out. `main` prints all of them.
- **Downloads (`download`)**: resumable `.part` + `Range`, 30 s stall timeout, 5 retries,
  SHA-256 checked before the rename. A pre-flight fetch of byte 0 (15 s) covers redirects and CDNs.
- **Pins**: `LLAMA_BUILD`/`LLAMA_SHA256` and `OPENCODE_VERSION`/`OPENCODE_SHA256`, one hash
  per platform key from `llama_platform()` / `opencode_platform()`. Models pin `sha256` in
  `PROFILES`, taken from Hugging Face LFS metadata (`/api/models/<repo>/tree/main`).
- **Models**: stored at `models/<family>/<file>.gguf`. The server gets `-m <path>`, never
  `-hf`, so the layout stays readable. The profile `key` is the server `--alias` and the
  OpenCode model id. Context is 32K (16K below 12 GB RAM) with a q8_0 KV cache, because
  OpenCode's prompt is ~10K tokens.
- **Archives (`extract`)**: drops a shared top folder, refuses paths and symlink targets
  outside the target, and recreates tar symlinks. llama.cpp dylibs are symlinks, and
  `llama-server` does not start without them.
- **OpenCode isolation (`opencode_env`)**: `OPENCODE_CONFIG=local-ai/opencode.json` plus
  `XDG_{CONFIG,DATA,STATE,CACHE}_HOME` under `local-ai/opencode-home/`. The user's own
  OpenCode setup is neither read nor written. SIGINT is ignored in the wizard while
  OpenCode runs.

## Constraints to keep

- Python 3.9+ and stdlib only. `X | None` only in annotations (`from __future__ import annotations`),
  and no nested same-quote f-strings (3.12+).
- Nothing outside the data dir. The server binds `127.0.0.1` only.
- No Cyrillic outside `STRINGS["ru"]`. Every new string needs both `en` and `ru`.
- Cross-platform branches matter: on Windows `os.kill(pid, 0)` kills the process (so `pid_alive`
  uses `tasklist`), keys come from `msvcrt`, ANSI is enabled via `SetConsoleMode`, and stopping
  uses `taskkill /T` instead of `killpg`.
- `README.md` (English, primary) and `README.ru.md` must be kept in sync.

## LLM Wiki Schema

Project knowledge lives in `docs/wiki/` (LLM Wiki pattern, Karpathy). Raw sources are
`local_ai_starter.py`, the launchers and the READMEs. The wiki is maintained by Claude, and
this file is the schema. Start from `docs/wiki/index.md`; current state is in `docs/wiki/status.md`.

- Structure: `index.md`, `log.md` (append-only), `status.md`, `architecture.md`,
  `debugging_log.md`, `entities/` (wizard-flow, terminal-ui, i18n, network, profiles,
  llama-engine, server-lifecycle, opencode-integration, launchers), `workflows/` (build, test,
  update-llama-build, update-opencode).
- Ingest: new info → its one canonical page → dated `log.md` entry → `status.md` if affected.
  Query: wiki first, code as fallback, file the answer back. Lint: contradictions, stale
  `file:line` refs, orphans, missing links. Full procedures are in the `/wiki` command.
- Conventions: one fact per page (link, don't copy), `file:line` refs, absolute dates
  `YYYY-MM-DD`, no emojis. Entity pages use Purpose / Key API / Collaborators / Known Issues /
  Related Pages. Wiki text is in Russian. When code is the truth and the wiki disagrees,
  fix the wiki and log it.
- Not in the wiki: code listings, conversation state, personal preferences.
