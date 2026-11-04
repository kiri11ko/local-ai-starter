# OpenCode integration

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Главный сценарий: OpenCode CLI на локальной модели в том же терминале, полностью изолированный
от пользовательской установки OpenCode.

## Key API
- `OPENCODE_VERSION`, `OPENCODE_URL`, `OPENCODE_SHA256` — `local_ai_starter.py:65-75`.
  Официальные ассеты релиза `anomalyco/opencode`: `opencode-{darwin,linux,windows}-{arm64,x64}`,
  на Linux `.tar.gz`, на остальных `.zip`. В архиве один файл `opencode` в корне.
- `install_opencode()` — `local_ai_starter.py:877` → `local-ai/opencode/opencode[.exe]`;
  `opencode_binary()` — `:836`. Ставится и на Windows.
- `write_opencode_config(profile, port, ctx)` — `local_ai_starter.py:1027` → `local-ai/opencode.json`:
  провайдер `local-ai-starter` (`@ai-sdk/openai-compatible`, `baseURL http://127.0.0.1:<port>/v1`),
  модель `<key>` с `tool_call: true` и лимитами контекста, `model` и `small_model` на неё,
  `autoupdate: false`, `share: disabled`. Проверено: `opencode models` видит только `local-ai-starter/<key>`.
- `opencode_env()` — `local_ai_starter.py:1055`: `OPENCODE_CONFIG`, `OPENCODE_DISABLE_AUTOUPDATE=1`,
  `XDG_{CONFIG,DATA,STATE,CACHE}_HOME` → `local-ai/opencode-home/{config,data,state,cache}`.
  Проверено с подменённым `HOME`: OpenCode туда ничего не пишет.
- `prepare_workspace()` — `local_ai_starter.py:1046`: `local-ai/workspace`, учебный `index.html`
  только в пустой папке.
- `launch_opencode()` — `local_ai_starter.py:1066`: подсказка с примером задачи, затем OpenCode
  в этом терминале. SIGINT в мастере на это время игнорируется, Ctrl+C достаётся OpenCode.

## Collaborators
- [server-lifecycle](server-lifecycle.md) — порт и `ctx`, [profiles](profiles.md) — модель,
  [network](network.md) — загрузка.

## Known Issues
- Не проверено вживую, что выбранная модель вызывает инструменты (правка `index.html`).
- На Linux берётся glibc-сборка; для Alpine (musl) и x64 без AVX2 (`-baseline`) нужны другие ассеты.

## Related Pages
[update-opencode](../workflows/update-opencode.md), [wizard-flow](wizard-flow.md), [test](../workflows/test.md)
