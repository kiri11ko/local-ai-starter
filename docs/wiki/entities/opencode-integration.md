# OpenCode integration

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Ветка «Программирование»: поставить OpenCode, не трогая систему, и создать учебный
проект, подключённый к локальному серверу.

## Key API
- `find_opencode()` — `local_ai_starter.py:417`: сначала `opencode-home/.opencode/bin/opencode`,
  затем `opencode` из PATH.
- `install_opencode()` — `local_ai_starter.py:425`. Скачивает официальный установщик
  (`OPENCODE_INSTALL_URL`) и запускает его с `HOME=opencode-home` и `--no-modify-path`.
  На Windows не ставит, только даёт инструкцию.
- `setup_demo_project(profile, port)` — `local_ai_starter.py:451`. Пишет `index.html` и
  `opencode.json` с провайдером `local-ai-starter` (`@ai-sdk/openai-compatible`,
  `baseURL http://127.0.0.1:<port>/v1`, лимиты контекста из профиля).
- `launch_opencode()` — `local_ai_starter.py:522`, предлагает открыть OpenCode в этом окне.

## Collaborators
- [server-lifecycle](server-lifecycle.md) — порт; при смене порта `opencode.json` перезаписывается.
- [profiles](profiles.md) — профиль `code`.

## Known Issues
- Не проверено, что Qwen2.5-Coder-7B корректно вызывает инструменты OpenCode.
- `find_opencode` ищет файл без `.exe` — ветка рассчитана на macOS/Linux.

## Related Pages
[wizard-flow](wizard-flow.md), [test](../workflows/test.md)
