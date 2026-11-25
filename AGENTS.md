# Repository guide

## Project and checks

- `local_ai_starter.py` is the stdlib-only Python 3.9+ wizard and entrypoint; `RunMe.command`, `RunMe.sh`, and `RunMe.bat` are platform launchers. Avoid Python 3.10+ runtime syntax/features; `X | None` is safe only in annotations with postponed evaluation.
- Syntax: `python3 -m py_compile local_ai_starter.py`. Wizard tests: `python3 -m unittest discover -s tests -v`; a single file: `python3 -m unittest discover -s tests -p 'test_transfer.py' -v`. These use stubs and temporary directories, not real models.
- Noninteractive dry run (numbered menus on piped stdin): `printf '\n\n1\n' | LOCAL_AI_STARTER_DRY_RUN=1 LOCAL_AI_STARTER_NO_UPDATE=1 LOCAL_AI_STARTER_HOME="$(mktemp -d)" python3 local_ai_starter.py`. `LOCAL_AI_STARTER_LANG=en|ru` forces language. `--menu` opens management directly.
- `test-cases/` is a model benchmark suite, not the wizard's unit tests. Case format and hidden checks: `test-cases/README.md`; additional focused recipes: `docs/wiki/workflows/test.md`. Warn before any real model run that downloads large weights.

## Architecture and constraints

- Flow: `main` → update check → `start_menu` → `launch` → `ensure_installed`; code uses llama.cpp/GGUF, Apple Silicon MLX, or Strata (`docs/wiki/entities/strata-engine.md`), plus an isolated OpenCode; image/video use stable-diffusion.cpp, speech uses llama-tts. `_MODELS` defines profiles, components, revisions and hashes; engine/model storage must not overlap. Strata is different: the wizard pins only the Terminal installer and delegates engine/model downloads to `strata launch` (env vars `STRATA_DATA_DIR`/`STRATA_BIN_DIR` keep everything inside `engines/strata/`); its API model id is fixed `"strata"`, the API key lives in `state.json` as `api_key`, there is no `/metrics` (speeds fall back to wall time), and `migrate_layout` must never see a `models/strata` folder (it would be swept into `models/gguf/`).
- All user-facing strings belong in both `STRINGS` locales. No Cyrillic in Python code outside `STRINGS["ru"]` or in launchers. Keep `README.md` and `README.ru.md` synchronized.
- Normal data lives under `local-ai/` (override with `LOCAL_AI_STARTER_HOME`); server binds only to `127.0.0.1`. Exceptions are the optional, consented command link and explicitly confirmed agent-settings transfer. `--here` must not write into the target project. OpenCode's config and XDG directories are isolated via `opencode_env()`.
- Downloads resume via `.part`/Range and verify known SHA-256; extraction must reject escaping paths and symlink targets. Preserve Windows-specific process and terminal behavior (`tasklist`, `taskkill`, `msvcrt`) when changing cross-platform code.
- MLX requests use `default_model`, not the profile key: unknown names cause `mlx_lm.server` to load another model. Flux and Z-Image use CPU VAE on macOS to avoid blank Metal output.
- Update checks can be disabled with `--no-update` or `LOCAL_AI_STARTER_NO_UPDATE=1`; `LOCAL_AI_STARTER_UPDATE_API` and `LOCAL_AI_STARTER_UPDATE_ZIP` allow local fake releases. Test updater changes in a disposable copy/clone, not the working tree.

## Project knowledge and release

- Start with `docs/wiki/index.md` and `docs/wiki/todo.md`; code is authoritative when wiki disagrees. Maintain relevant wiki pages and append `docs/wiki/log.md` when behavior changes. Known open P0s include model-layout migration and server/profile identity; check the backlog before touching either.
- Release procedure: `docs/wiki/workflows/release.md`. Match `VERSION` to the tag, commit and push before creating the GitHub release; show release notes to the user before publishing.
