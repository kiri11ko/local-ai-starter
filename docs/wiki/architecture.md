# Архитектура

Один файл [`local_ai_starter.py`](../../local_ai_starter.py), только стандартная библиотека,
Python 3.9+. Внешних процессов два: `llama-server` (движок, API и веб-чат) и OpenCode CLI,
который открывается в том же терминале.

## Слои файла

| Строки | Слой | Страница |
|---|---|---|
| `local_ai_starter.py:35-75` | константы, пути, закреплённые сборки llama.cpp и OpenCode | [llama-engine](entities/llama-engine.md), [opencode-integration](entities/opencode-integration.md) |
| `local_ai_starter.py:79-107` | `Profile`, `PROFILES` | [profiles](entities/profiles.md) |
| `local_ai_starter.py:110-343` | `STRINGS`, `detect_lang`, `t`, `size_text` | [i18n](entities/i18n.md) |
| `local_ai_starter.py:346-522` | терминал: ANSI, цвета, меню со стрелками | [terminal-ui](entities/terminal-ui.md) |
| `local_ai_starter.py:526-624` | система: память, диск, платформы, порты, PID | [profiles](entities/profiles.md), [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:627-644` | `state.json` | [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:647-828` | сеть: проверка, докачка, SHA-256, распаковка | [network](entities/network.md) |
| `local_ai_starter.py:831-893` | установка движка, OpenCode, модели | [llama-engine](entities/llama-engine.md) |
| `local_ai_starter.py:897-1023` | сервер | [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:1027-1083` | OpenCode: конфиг, рабочая папка, изоляция, запуск | [opencode-integration](entities/opencode-integration.md) |
| `local_ai_starter.py:1086-1263` | сценарии, меню, `main` | [wizard-flow](entities/wizard-flow.md) |

## Поток запуска

```
main
  run_opencode(saved_profile)          (пропускается при --menu)
    ensure_installed
      choose_profile                   только если профиль ещё не выбран
      план недостающего -> «Начинаем?»
      check_network                    первый байт каждой загрузки, 15 с
      install_llama / install_model / install_opencode
    bring_up                           pick_port -> start_server -> wait_ready
    launch_opencode                    opencode.json + workspace + OpenCode в этом терминале
  menu                                 после выхода из OpenCode
```

Первый и повторный запуск идут одним путём: `ensure_installed` спрашивает и качает только
то, чего ещё нет.

## Папка данных

Корень — `ROOT` (`local_ai_starter.py:41`): `local-ai/` рядом со скриптом или
`LOCAL_AI_STARTER_HOME`. Вне неё мастер ничего не пишет.

```
local-ai/
  bin/            llama.cpp (llama-server, библиотеки и их symlink-и)
  models/<семейство>/<файл>.gguf
  opencode/       бинарник OpenCode
  opencode-home/  XDG-папки OpenCode (config, data, state, cache)
  opencode.json   конфиг OpenCode: только локальный провайдер
  workspace/      рабочая папка OpenCode
  state.json      profile, pid, port, ctx, started_at
  server.log      вывод llama-server (дописывается)
```

## Принципы

- Пользователь не технический: меню со стрелками, Enter выбирает рекомендуемое
  ([terminal-ui](entities/terminal-ui.md)). Язык интерфейса — по системе ([i18n](entities/i18n.md)).
- Ожидаемые ошибки: `RuntimeError` с текстом через `t()`, сетевые — `NetworkError`. `main`
  печатает их и возвращает 1 (`local_ai_starter.py:1243`).
- Всё, что качается, закреплено версией и SHA-256 ([network](entities/network.md)).
- Сервер слушает только `127.0.0.1`.
