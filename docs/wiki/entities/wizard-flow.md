# Wizard flow

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Сценарии: от запуска до OpenCode одним путём и меню управления после выхода из него.

## Key API
- `main(argv)` — `local_ai_starter.py:1243`. Баннер → `run_opencode(saved_profile())`
  (если нет `--menu`) → `menu()`. Ловит `Cancelled`/`KeyboardInterrupt`, `NetworkError` и
  ожидаемые ошибки.
- `run_opencode(profile)` — `local_ai_starter.py:1212`: `ensure_installed` → `bring_up` → `launch_opencode`.
- `ensure_installed(profile)` — `local_ai_starter.py:1116`. Профиль спрашивается, только если
  его нет. Задачи — только недостающие компоненты с размерами; проверка места (сумма + 1 ГБ);
  одно подтверждение; `check_network` по всем URL; шаги `[i/n]`. Сохраняет профиль в `state.json`.
- `menu(profile)` — `local_ai_starter.py:1219`. Пункты: остановить и выйти (по умолчанию),
  выйти с работающим сервером, вернуться в OpenCode, веб-чат, сменить модель, модели на диске,
  состояние, удалить всё.
- `manage_models()` — `local_ai_starter.py:1171`: список `models/*/*.gguf` с размерами, открыть
  папку, удалить модель (если она сейчас в сервере — сначала остановка).
- `show_status()` — `local_ai_starter.py:1158`, `uninstall()` — `local_ai_starter.py:1202`.

## Collaborators
- [terminal-ui](terminal-ui.md) — `ask`, `yes_no`, `step`.
- [profiles](profiles.md) — `choose_profile`.
- [network](network.md) — `check_network`.
- [llama-engine](llama-engine.md), [server-lifecycle](server-lifecycle.md),
  [opencode-integration](opencode-integration.md).

## Known Issues
- В dry-run `ensure_installed` всегда показывает полный план: проверки наличия файлов
  намеренно обходятся.

## Related Pages
[architecture](../architecture.md), [build](../workflows/build.md), [test](../workflows/test.md)
