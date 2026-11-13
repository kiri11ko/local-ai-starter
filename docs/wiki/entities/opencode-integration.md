# OpenCode integration

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Главный сценарий: OpenCode CLI на локальной модели в том же терминале, полностью изолированный
от пользовательской установки OpenCode.

## Key API
- `OPENCODE_VERSION`, `OPENCODE_URL`, `OPENCODE_SHA256` — `local_ai_starter.py:121-131`.
  Официальные ассеты релиза `anomalyco/opencode`: `opencode-{darwin,linux,windows}-{arm64,x64}`,
  на Linux `.tar.gz`, на остальных `.zip`. В архиве один файл `opencode` в корне.
- `install_opencode()` — `local_ai_starter.py:1479` → `local-ai/opencode/opencode[.exe]`;
  `opencode_binary()` — `:1248`. Ставится и на Windows.
- `write_opencode_config(profile, port, ctx)` — `local_ai_starter.py:1755` → `local-ai/opencode.json`:
  провайдер `local-ai-starter` (`@ai-sdk/openai-compatible`, `baseURL http://127.0.0.1:<port>/v1`),
  модель `api_model(profile)` (`<key>` или `default_model` для MLX, см. [mlx-engine](mlx-engine.md))
  с `tool_call: true` и лимитами контекста, `model` и `small_model` на неё,
  `autoupdate: false`, `share: disabled`. Проверено: `opencode models` видит только `local-ai-starter/<key>`.
- `opencode_env()` — `local_ai_starter.py:1784`: `OPENCODE_CONFIG`, `OPENCODE_DISABLE_AUTOUPDATE=1`,
  `XDG_{CONFIG,DATA,STATE,CACHE}_HOME` → `local-ai/opencode-home/{config,data,state,cache}`.
  Проверено с подменённым `HOME`: OpenCode туда ничего не пишет.
- `prepare_workspace()` — `local_ai_starter.py:1775`: `local-ai/workspace`, учебный `index.html`
  только в пустой папке.
- `launch_opencode()` — `local_ai_starter.py:1795`: подсказка с примером задачи, затем OpenCode
  в этом терминале. SIGINT в мастере на это время игнорируется, Ctrl+C достаётся OpenCode.

- `launch_opencode(profile, state, workdir=None)` принимает чужую папку: `prepare_workspace()` тогда
  не вызывается, OpenCode получает `--model local-ai-starter/<api_model>` (проектный `opencode.json`
  в чужой папке приоритетнее `OPENCODE_CONFIG` и мог бы подменить модель).
- Команда `local-opencode` (добавлено 2026-11-12): `write_command_script()` пишет `local-ai/bin/local-opencode[.cmd]`
  с абсолютными путями к python и мастеру и вызовом `--here "$PWD"`; `install_command()` (пункт меню
  «Команда для OpenCode в любой папке») по согласию кладёт симлинк в `~/.local/bin` (Windows: копию
  в `%LOCALAPPDATA%\Microsoft\WindowsApps`), чужой файл не перезаписывает, при отсутствии папки в `PATH`
  показывает строку для `~/.zshrc`; `remove_command()` вызывается из `uninstall()`.
  `opencode_here(argv)` — режим `--here [DIR]`: последний code-профиль → `ensure_installed` → `bring_up` →
  OpenCode в `DIR` → вопрос «оставить сервер / остановить». `--stop` останавливает сервер.
  Единственный файл вне data dir, и только с согласия пользователя.

## Collaborators
- [server-lifecycle](server-lifecycle.md) — порт и `ctx`, [profiles](profiles.md) — модель,
  [network](network.md) — загрузка.

## Known Issues
- Не проверено вживую, что выбранная модель вызывает инструменты (правка `index.html`).
- На Linux берётся glibc-сборка; для Alpine (musl) и x64 без AVX2 (`-baseline`) нужны другие ассеты.

## Related Pages
[update-opencode](../workflows/update-opencode.md), [wizard-flow](wizard-flow.md), [test](../workflows/test.md)
