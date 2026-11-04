# Server lifecycle

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Запуск `llama-server` в фоне, ожидание готовности, повторное использование и остановка;
хранение состояния между запусками мастера.

## Key API
- `start_server(profile, port)` — `local_ai_starter.py:332`. Команда:
  `llama-server -hf <hf_model> --alias <key> -c <context> --jinja --host 127.0.0.1 --port <port>`,
  `LLAMA_CACHE=models/`, вывод в `server.log`. Процесс отсоединяется
  (`start_new_session` / `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`).
- `wait_ready(state)` — `local_ai_starter.py:357`. До часа опрашивает `/health` (первый запуск
  включает скачивание модели), каждые 10 с печатает последнюю строку журнала, затем шлёт
  пробный `/v1/chat/completions`.
- `bring_up(profile)` — `local_ai_starter.py:500`. Здоровый сервер с тем же профилем
  переиспользуется, иначе остановка и новый запуск на `pick_port(8080)`.
- `stop_server()` — `local_ai_starter.py:392`: `taskkill /T /F` на Windows, `killpg(SIGTERM)`
  с запасным `kill` на POSIX; ждёт до 10 с.
- `pid_alive()` — `local_ai_starter.py:180`. На Windows через `tasklist`, потому что
  `os.kill(pid, 0)` там убивает процесс.
- `read_state()` / `write_state()` — `local_ai_starter.py:196`, `:205`. `state.json`:
  `pid`, `port`, `profile`, `started_at`; запись атомарная через `.tmp`.
- `pick_port()` — `local_ai_starter.py:173`, перебирает 8080–8129.

## Collaborators
- [llama-engine](llama-engine.md) — бинарник.
- [profiles](profiles.md) — параметры запуска.
- [wizard-flow](wizard-flow.md) — вызывает `bring_up`, `stop_server`, `show_status`.
- [opencode-integration](opencode-integration.md) — использует порт из состояния.

## Known Issues
- PID из `state.json` не сверяется с именем процесса. Если после перезагрузки PID занял
  другой процесс, `running_state` сочтёт его сервером, а `stop_server` может послать ему
  SIGTERM (через запасной `os.kill`).
- `server.log` только дописывается и не ротируется.

## Related Pages
[architecture](../architecture.md), [test](../workflows/test.md)
