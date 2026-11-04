# Архитектура

Один файл [`local_ai_starter.py`](../../local_ai_starter.py), только стандартная библиотека,
Python 3.9+. Внешние процессы: локальный сервер модели (`llama-server` или `mlx_lm.server`)
и OpenCode CLI, который открывается в том же терминале.

## Слои файла

| Строки | Слой | Страница |
|---|---|---|
| `local_ai_starter.py:35-89` | константы, пути, закреплённые llama.cpp, uv/mlx-lm, OpenCode | [llama-engine](entities/llama-engine.md), [mlx-engine](entities/mlx-engine.md), [opencode-integration](entities/opencode-integration.md) |
| `local_ai_starter.py:92-158` | `Profile`, `_MODELS`, `PROFILES` | [profiles](entities/profiles.md) |
| `local_ai_starter.py:163-434` | `STRINGS`, `detect_lang`, `t`, `size_text` | [i18n](entities/i18n.md) |
| `local_ai_starter.py:437-613` | терминал: ANSI, цвета, меню со стрелками | [terminal-ui](entities/terminal-ui.md) |
| `local_ai_starter.py:617-735` | система, порты, PID, `state.json` | [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:738-920` | сеть: проверка, докачка, SHA-256, распаковка | [network](entities/network.md) |
| `local_ai_starter.py:924-1054` | компоненты: движки, OpenCode, модели | [llama-engine](entities/llama-engine.md), [mlx-engine](entities/mlx-engine.md) |
| `local_ai_starter.py:1057-1206` | сервер | [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:1209-1281` | замер скорости | [speed-test](entities/speed-test.md) |
| `local_ai_starter.py:1284-1341` | OpenCode: конфиг, рабочая папка, изоляция, запуск | [opencode-integration](entities/opencode-integration.md) |
| `local_ai_starter.py:1344-1600` | переезд раскладки, сценарии, меню, `main` | [wizard-flow](entities/wizard-flow.md) |

## Поток запуска

```
main
  migrate_layout                       раскладка v2 -> v3 на месте
  run_opencode(saved_profile)          (пропускается при --menu)
    ensure_installed
      choose_profile                   только если профиль ещё не выбран
        choose_engine                  только на Apple Silicon: llama.cpp или MLX
      план недостающего -> «Начинаем?»
      check_network                    первый байт каждой загрузки, 15 с
      движок / модель / OpenCode
    bring_up                           pick_port -> start_server -> wait_ready
    launch_opencode                    opencode.json + workspace + OpenCode в этом терминале
  menu                                 после выхода из OpenCode
```

## Папка данных

Корень — `ROOT` (`local_ai_starter.py:41`): `local-ai/` рядом со скриптом или
`LOCAL_AI_STARTER_HOME`. Вне неё мастер ничего не пишет. Движки и модели разных
движков лежат в разных папках и друг друга не перетирают.

```
local-ai/
  engines/llama.cpp/          llama-server, библиотеки и их symlink-и
  engines/mlx/                uv/, python/ (CPython от uv), venv/ с mlx-lm, cache/, hf/, .installed
  models/gguf/<семейство>/<файл>.gguf
  models/mlx/<семейство>/<репозиторий>/   файлы модели + .complete
  opencode/                   бинарник OpenCode
  opencode-home/              XDG-папки OpenCode
  opencode.json               конфиг OpenCode: только локальный провайдер
  workspace/                  рабочая папка OpenCode
  benchmarks.csv              результаты замеров скорости
  state.json                  profile, engine, model_id, pid, port, ctx, started_at
  server.log                  вывод сервера (дописывается, у каждого запуска заголовок)
```

## Принципы

- Пользователь не технический: меню со стрелками, Enter выбирает рекомендуемое
  ([terminal-ui](entities/terminal-ui.md)). Язык интерфейса — по системе ([i18n](entities/i18n.md)).
- Ожидаемые ошибки: `RuntimeError` с текстом через `t()`, сетевые — `NetworkError`. `main`
  печатает их и возвращает 1 (`local_ai_starter.py:1580`).
- Всё, что качается, закреплено версией или коммитом и проверяется по SHA-256 ([network](entities/network.md)).
- Сервер слушает только `127.0.0.1`.
