# Архитектура

Один файл [`local_ai_starter.py`](../../local_ai_starter.py), только стандартная библиотека,
Python 3.9+. Внешних процессов два: `llama-server` (движок и веб-чат) и, по желанию, OpenCode.

## Слои файла

| Строки | Слой | Страница |
|---|---|---|
| `local_ai_starter.py:32-54` | константы, пути, закреплённая сборка | [llama-engine](entities/llama-engine.md) |
| `local_ai_starter.py:57-76` | `Profile`, `PROFILES` | [profiles](entities/profiles.md) |
| `local_ai_starter.py:80-116` | ввод-вывод: `say`, `ask`, `yes_no`, `run_cmd` | [wizard-flow](entities/wizard-flow.md) |
| `local_ai_starter.py:119-193` | система: память, диск, платформа, порты, PID | [profiles](entities/profiles.md), [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:196-211` | `state.json` | [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:214-307` | установка llama.cpp | [llama-engine](entities/llama-engine.md) |
| `local_ai_starter.py:310-412` | сервер | [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:417-468` | OpenCode | [opencode-integration](entities/opencode-integration.md) |
| `local_ai_starter.py:472-638` | сценарии и `main` | [wizard-flow](entities/wizard-flow.md) |

## Поток первого запуска

```
main -> first_run
  ask «для чего» -> choose_profile (RAM, диск) -> план -> yes_no «Начинаем?»
  install_llama          скачать архив -> SHA-256 -> распаковать в bin/
  install_opencode       только для ветки «программирование»
  bring_up               pick_port -> start_server -> wait_ready (/health + пробный вопрос)
  open_chat | launch_opencode
```

Повторный запуск: `main` видит `bin/llama-server` и открывает `menu()`
(`local_ai_starter.py:616-623`).

## Папка данных

Корень — `ROOT` (`local_ai_starter.py:35`): `local-ai/` рядом со скриптом или
`LOCAL_AI_STARTER_HOME`. Вне неё мастер ничего не пишет.

```
local-ai/
  bin/            llama.cpp (llama-server и библиотеки)
  models/         кэш моделей, LLAMA_CACHE для llama-server
  opencode-home/  подменённый HOME для установщика OpenCode
  demo-project/   index.html + opencode.json
  state.json      pid, port, profile, started_at
  server.log      stdout/stderr llama-server (дописывается)
```

## Принципы

- Пользователь не технический: только нумерованные варианты, Enter — рекомендуемый.
  Тексты интерфейса на русском.
- Ожидаемые ошибки — `RuntimeError` с понятным текстом; `main` печатает `Ошибка: …`
  и возвращает 1 (`local_ai_starter.py:631-633`).
- Сервер слушает только `127.0.0.1`.
