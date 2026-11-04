# Wizard flow

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Сценарии: от запуска до OpenCode одним путём, выбор движка и модели, меню управления после
выхода из OpenCode.

## Key API
- `main(argv)` — `local_ai_starter.py:1580`. Баннер → `migrate_layout()` → `run_opencode(saved_profile())`
  (если нет `--menu`) → `menu()`. Ловит `Cancelled`/`KeyboardInterrupt`, `NetworkError` и ожидаемые ошибки.
- `migrate_layout()` — `local_ai_starter.py:1344`: раскладка v2 (`bin/`, `models/<family>/`) переезжает
  в `engines/llama.cpp/` и `models/gguf/<family>/`, включая недокачанные `.part`.
- `run_opencode(profile)` — `local_ai_starter.py:1546`: `ensure_installed` → `bring_up` → `launch_opencode`.
- `choose_engine()` — `local_ai_starter.py:1374`: только на Apple Silicon спрашивает llama.cpp (по
  умолчанию) или MLX; установленные помечены ✓. На остальных системах сразу `gguf`.
- `ensure_installed(profile)` — `local_ai_starter.py:1417`. Профиль спрашивается, только если его нет.
  Задачи — только недостающие: движок выбранного профиля (`engine_task`, `:1410`), модель, OpenCode.
  Дальше проверка места (сумма + 1 ГБ), одно подтверждение, `check_network` по всем URL, шаги `[i/n]`.
- `menu(profile)` — `local_ai_starter.py:1553`. Пункты: остановить и выйти (по умолчанию),
  выйти с работающим сервером, вернуться в OpenCode, сменить модель или движок, замер скорости
  ([speed-test](speed-test.md)), веб-чат (только llama.cpp, `open_chat`, `:1452`), модели на диске,
  состояние, удалить всё.
- `manage_models()` — `local_ai_starter.py:1499`, `model_entries()` — `:1487`: GGUF-файлы
  (и `.part`), MLX-папки (без `.complete` — «не докачано»). Можно открыть папку или удалить модель;
  если она в работающем сервере, сервер сначала останавливается.
- `show_status()` — `local_ai_starter.py:1463`, `uninstall()` — `:1536`.

## Collaborators
- [terminal-ui](terminal-ui.md) — `ask`, `yes_no`, `step`; [profiles](profiles.md) — `choose_profile`;
  [network](network.md) — `check_network`; [llama-engine](llama-engine.md), [mlx-engine](mlx-engine.md),
  [server-lifecycle](server-lifecycle.md), [opencode-integration](opencode-integration.md).

## Known Issues
- В dry-run `ensure_installed` всегда показывает полный план: проверки наличия файлов намеренно обходятся.

## Related Pages
[architecture](../architecture.md), [build](../workflows/build.md), [test](../workflows/test.md)
