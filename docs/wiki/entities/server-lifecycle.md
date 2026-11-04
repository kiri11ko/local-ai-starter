# Server lifecycle

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Запуск `llama-server` в фоне, ожидание готовности, повторное использование и остановка;
состояние между запусками.

## Key API
- `server_command(profile, port, ctx)` — `local_ai_starter.py:925`:
  `llama-server -m <models/…gguf> --alias <key> -c <ctx> -fa on -ctk q8_0 -ctv q8_0 --jinja --host 127.0.0.1 --port <port>`.
  Флаги проверены на сборке b12110.
- `context_size()` — `local_ai_starter.py:919`: 32768, при RAM < 12 ГБ — 16384. Системный
  промпт и инструменты OpenCode занимают около 10K токенов, а KV-кэш q8_0 вдвое экономнее fp16.
- `start_server` — `local_ai_starter.py:932`: отсоединённый процесс, stdin из `/dev/null`,
  вывод в `server.log`, в `state.json` пишутся `pid`, `port`, `profile`, `ctx`, `started_at`.
- `wait_ready` — `local_ai_starter.py:953`: до 15 минут ждёт `/health` (модель уже на диске,
  идёт только загрузка в память), затем пробный `/v1/chat/completions`.
- `bring_up` — `local_ai_starter.py:1010`: здоровый сервер с тем же профилем переиспользуется,
  иначе остановка и запуск на `pick_port(8080)` (8080–8129).
- `stop_server` — `local_ai_starter.py:987`: `taskkill /T /F` или `killpg(SIGTERM)` с запасным `kill`.
- `pid_alive` — `local_ai_starter.py:600`: на Windows через `tasklist`, потому что
  `os.kill(pid, 0)` там убивает процесс.
- `read_state` / `write_state` — `local_ai_starter.py:627`, `:634` (атомарно через `.tmp`).

## Collaborators
- [llama-engine](llama-engine.md), [profiles](profiles.md), [wizard-flow](wizard-flow.md),
  [opencode-integration](opencode-integration.md) (порт и контекст попадают в `opencode.json`).

## Known Issues
- PID из `state.json` не сверяется с именем процесса. Если после перезагрузки этот PID занял
  другой процесс, `running_state` сочтёт его сервером, а `stop_server` может послать ему SIGTERM.
- `server.log` только дописывается и не ротируется.

## Related Pages
[architecture](../architecture.md), [test](../workflows/test.md)
