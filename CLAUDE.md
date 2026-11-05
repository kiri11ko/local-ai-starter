# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file, stdlib-only Python wizard (`local_ai_starter.py`): one double-click
(`RunMe.command` / `RunMe.sh` / `RunMe.bat`) sets up local AI of four kinds. Code: an engine,
a Qwen model and a pinned OpenCode CLI, a local OpenAI-compatible server on `127.0.0.1`, OpenCode
in the same terminal in `local-ai/workspace`; two engines, llama.cpp + GGUF everywhere and MLX
(`mlx_lm.server`) on Apple Silicon. Images and video: stable-diffusion.cpp (`sd-cli`). Speech:
`llama-tts` from the same llama.cpp build. `test-cases/` holds tasks the wizard runs on the
downloaded models and measures itself, so models and engines can be compared. Target users are non-technical: arrow-key menus,
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
- `--no-update` / `LOCAL_AI_STARTER_NO_UPDATE=1`: skip the update check. `LOCAL_AI_STARTER_UPDATE_API`
  and `LOCAL_AI_STARTER_UPDATE_ZIP` (`{tag}` placeholder) point it at a local fake release for tests.
- Piped stdin, or a terminal without ANSI support, switches menus to numbered `input()`.
  That is how to script the dry run: `printf '\n\n1\n' | …`.
- To test installs without the network, serve archives with `python3 -m http.server` and
  override `LLAMA_URL` / `OPENCODE_URL` from a `python3 -c 'import local_ai_starter as m; …'`.
- Test-case plumbing without a model: fake `opencode_binary` (a script printing `step_finish` events)
  and `bring_up` (a dict with the port of a fake `/metrics` server), then `run_case`. Verifiers in
  `test-cases/code/verify/` must exit 0 on a reference solution and 1 on the original fixtures.
- Real model runs download GB-sized weights: warn the user before starting one. The MLX runtime
  can be checked cheaply: `uv venv` + `uv pip install --dry-run mlx-lm==…` with `uv_env()`.

## Architecture

- **Flow (`main` → `start_menu` → `launch` → `menu`)**: the start menu lists every installed
  profile (last used first) plus "download a new configuration", test cases, the management menu
  and exit (`Quit`). `launch` sends code profiles to `run_opencode` and media profiles to
  `media_session`. Both go through `ensure_installed()`: it plans only the missing pieces, then
  runs `check_network()` and the downloads. A new configuration is `choose_profile()`: kind →
  engine (code only) → model. `--menu` skips straight to the management menu.
- **Updates (`check_for_update` → `apply_update` → `restart`)**: the first step of `main`.
  It reads GitHub Releases `latest` (5 s timeout; any failure is one dim line, never fatal) and
  offers only a strictly newer tag than `VERSION`. A git checkout gets `git merge --ff-only <tag>`
  on a clean tree; a ZIP folder gets the release archive with changed files replaced. Then the
  wizard re-runs itself with `--no-update`. `local-ai/` is never touched.
- **Errors**: raise `RuntimeError` with a `t(...)` message for expected failures and
  `NetworkError` for unreachable hosts. `network_error()` explains the cause (timeout / DNS /
  refused / TLS / HTTP; 404 means the pin is gone, not that the network is blocked).
  `Cancelled` means the user backed out. `main` prints all of them.
- **Downloads (`download`)**: resumable `.part` + `Range`, 30 s stall timeout, 5 retries,
  SHA-256 (when known) checked before the rename. A pre-flight fetch of byte 0 (15 s) covers redirects and CDNs.
- **Pins**: `LLAMA_BUILD`/`LLAMA_SHA256`, `SD_BUILD`/`SD_ASSETS` and `OPENCODE_VERSION`/`OPENCODE_SHA256`
  (one hash per platform key; sd.cpp has no Linux/Windows arm64 builds, so media is hidden there),
  `UV_VERSION`/`UV_SHA256` and `MLX_LM_VERSION`. Its Python dependencies are
  resolved at install time and not hash-pinned. Model hashes come from Hugging Face LFS
  metadata (`/api/models/<repo>/tree/<rev>`).
- **Profiles (`_MODELS`)**: `kind` is code / image / video / speech. Code: one line-up mirrored for
  both engines (`_gguf` / `_mlx`, keys `<base>` and `<base>-mlx`). Media (`_media`): `components`
  (`Component`: engine folder, CLI flag, repo, pinned commit, file, size, SHA-256), default `args`,
  `mac_args`, output `ext`. Ordered small → large per kind; the recommendation is the largest with
  `min_ram_gb` ≤ RAM. Labels come from `STRINGS["model.<base>"]`, the part before ":" is the short
  name. GGUF pins a file + SHA-256; MLX pins a repo commit (in `file`) and checks every LFS file.
- **Storage never overlaps**: `engines/llama.cpp/`, `engines/mlx/` (uv, uv-managed Python 3.12,
  venv with pinned `mlx-lm`), `engines/stable-diffusion.cpp/`, `models/gguf/<family>/<file>.gguf`,
  `models/mlx/<family>/<repo>/` (+ `.complete` marker), and flat `models/sd/`, `models/tts/` where
  files shared by several profiles (VAE, text encoders, TTS codec) are stored once.
  `migrate_layout()` moves the v2 layout (`bin/`, `models/<family>/`) in place.
- **Media (`generate`, `media_session`)**: one `sd-cli` / `llama-tts` run per file, measured by
  `run_measured` (wall time, peak RSS via `ps`/`tasklist`). A running code server is stopped first.
  Flux and Z-Image get `--backend vae=cpu` on macOS (Metal VAE gives a blank white image).
  Outputs go to `local-ai/outputs/<kind>/`.
- **Test cases (`run_test_cases`)**: `test-cases/<kind>/<id>.md` (header, `---`, prompt; format in
  `test-cases/README.md`). Code runs `opencode run --format json --auto --dir work`; tokens are summed
  from `step_finish` events, llama.cpp speeds come from `/metrics` deltas (server has `--metrics`).
  Hidden checks in `test-cases/code/verify/` run in the work folder via `check: python3 {case_dir}/…`.
  Each run writes `local-ai/test-runs/<run>/<case>/<model>/` and a row in `test-results/results.csv`;
  `results.md` is rebuilt with the latest run per model.
- **Server ids**: llama-server gets `--alias <key>`. `mlx_lm.server` loads any unknown
  `model` name as a new model, so OpenCode and requests use `default_model` for MLX
  (`api_model()`, stored as `model_id` in `state.json`). Context is 32K (16K below 12 GB RAM,
  64K from 48 GB) with a q8_0 KV cache on llama.cpp. OpenCode's prompt is ~10K tokens.
- **Speed test (`speed_test`)**: streams a ~4K-token prompt (prefill, TTFT) and a ~300-token
  answer (generation tok/s). It counts `content`, `reasoning_content` (llama.cpp) and `reasoning` (MLX)
  deltas and appends a row to `local-ai/benchmarks.csv`.
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
- Releasing: bump `VERSION` to match the new tag, commit, push, then `gh release create vX.Y.Z`.
  Users read the release notes in the update prompt, so show the notes to the user before
  publishing. Procedure: `docs/wiki/workflows/release.md`.

## LLM Wiki Schema

Project knowledge lives in `docs/wiki/` (LLM Wiki pattern, Karpathy). Raw sources are
`local_ai_starter.py`, the launchers and the READMEs. The wiki is maintained by Claude, and
this file is the schema. Start from `docs/wiki/index.md`; current state is in `docs/wiki/status.md`.

- Structure: `index.md`, `log.md` (append-only), `status.md`, `architecture.md`,
  `debugging_log.md`, `entities/` (wizard-flow, terminal-ui, i18n, network, profiles,
  llama-engine, mlx-engine, sd-engine, speech, test-cases, server-lifecycle, speed-test,
  opencode-integration, launchers, updater),
  `workflows/` (build, test, release, update-llama-build, update-sd-build, update-opencode, update-models),
  `todo.md` (backlog).
- Ingest: new info → its one canonical page → dated `log.md` entry → `status.md` if affected.
  Query: wiki first, code as fallback, file the answer back. Lint: contradictions, stale
  `file:line` refs, orphans, missing links. Full procedures are in the `/wiki` command.
- Conventions: one fact per page (link, don't copy), `file:line` refs, absolute dates
  `YYYY-MM-DD`, no emojis. Entity pages use Purpose / Key API / Collaborators / Known Issues /
  Related Pages. Wiki text is in Russian. When code is the truth and the wiki disagrees,
  fix the wiki and log it.
- Not in the wiki: code listings, conversation state, personal preferences.
