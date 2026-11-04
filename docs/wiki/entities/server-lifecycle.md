# Server lifecycle

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Запуск `llama-server` в фоне, ожидание готовности, повторное использование и остановка;
состояние между запусками.

## Key API
- `server_command(profile, port, ctx)` — `local_ai_starter.py:1095`. llama.cpp:
  `llama-server -m <models/gguf/…> --alias <key> -c <ctx> -fa on -ctk q8_0 -ctv q8_0 --jinja --host 127.0.0.1 --port <port>`
  (флаги проверены на b12110). MLX — см. [mlx-engine](mlx-engine.md).
- `api_model(profile)` — `local_ai_starter.py:1090`: `<key>` для llama.cpp, `default_model` для MLX.
- `context_size()` — `local_ai_starter.py:1080`: 32768; при RAM < 12 ГБ — 16384, от 48 ГБ — 65536.
  Системный промпт и инструменты OpenCode занимают около 10K токенов. KV-кэш q8_0 (llama.cpp)
  вдвое экономнее fp16.
- `start_server` — `local_ai_starter.py:1105`: отсоединённый процесс, stdin из `/dev/null`,
  вывод в `server.log` с заголовком запуска. В `state.json` пишутся `pid`, `port`, `profile`,
  `engine`, `model_id`, `ctx`, `started_at`.
- `wait_ready` — `local_ai_starter.py:1134`: до 15 минут ждёт `/health` (у обоих серверов 200,
  когда модель готова), затем пробный `/v1/chat/completions` с `model_id`.
- `bring_up` — `local_ai_starter.py:1192`: здоровый сервер с тем же профилем переиспользуется,
  иначе остановка и запуск на `pick_port(8080)` (8080–8129). Одновременно работает один сервер.
- `stop_server` — `local_ai_starter.py:1169`: `taskkill /T /F` или `killpg(SIGTERM)` с запасным `kill`.
- `pid_alive` — `local_ai_starter.py:691`: на Windows через `tasklist`, потому что
  `os.kill(pid, 0)` там убивает процесс.
- `read_state` / `write_state` — `local_ai_starter.py:718`, `:725` (атомарно через `.tmp`).

## Collaborators
- [llama-engine](llama-engine.md), [mlx-engine](mlx-engine.md), [profiles](profiles.md),
  [wizard-flow](wizard-flow.md), [speed-test](speed-test.md),
  [opencode-integration](opencode-integration.md) (порт и контекст попадают в `opencode.json`).

## Known Issues
- PID из `state.json` не сверяется с именем процесса. Если после перезагрузки этот PID занял
  другой процесс, `running_state` сочтёт его сервером, а `stop_server` может послать ему SIGTERM.
- `server.log` только дописывается и не ротируется.

## Related Pages
[architecture](../architecture.md), [test](../workflows/test.md)
