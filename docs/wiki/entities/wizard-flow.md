# Wizard flow

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Сценарии взаимодействия с пользователем: первый запуск, меню управления и общий
ввод-вывод. Пользователь отвечает номером варианта или Enter.

## Key API
- `main()` — `local_ai_starter.py:616`. Есть `bin/llama-server` → `menu()`, иначе `first_run()`
  и предложение открыть меню. Ловит `Cancelled`, `KeyboardInterrupt` и ожидаемые ошибки.
- `first_run()` — `local_ai_starter.py:536`. Цель → профиль → план → подтверждение → установка → запуск.
- `menu()` — `local_ai_starter.py:578`. Семь пунктов: запустить и открыть чат, остановить,
  сменить модель, учебный проект OpenCode, состояние, удалить всё, выход.
- `show_status()` — `local_ai_starter.py:557`, `uninstall()` — `local_ai_starter.py:569`
  (останавливает сервер и удаляет `ROOT` целиком).
- `ask(question, options, default)` — `local_ai_starter.py:88`. Возвращает номер с 1;
  EOF/Ctrl+C → `Cancelled`. `yes_no` — `local_ai_starter.py:106`.
- `run_cmd` — `local_ai_starter.py:110`, печатает команду и в dry-run её не выполняет.

## Collaborators
- [profiles](profiles.md) — `choose_profile`.
- [llama-engine](llama-engine.md) — `install_llama`.
- [server-lifecycle](server-lifecycle.md) — `bring_up`, `stop_server`, `running_state`.
- [opencode-integration](opencode-integration.md) — `install_opencode`, `launch_opencode`.

## Known Issues
- Пункт меню «Выбрать другую модель» вызывает `choose_profile(False)`
  (`local_ai_starter.py:597`), поэтому профиль «Для программирования» там не предлагается —
  только через пункт OpenCode.
- В dry-run `start_server` не пишет `state.json`, поэтому условие
  `DRY_RUN and STATE_FILE.exists()` (`local_ai_starter.py:618`) срабатывает, только если
  файл состояния создан заранее. Иначе dry-run всегда идёт по первому запуску.

## Related Pages
[architecture](../architecture.md), [build](../workflows/build.md), [test](../workflows/test.md)
