# Test

Автотестов нет. Проверка — синтаксис, dry-run, точечные проверки через `python3 -c` и ручной прогон.

## Быстрые проверки

```bash
python3 -m py_compile local_ai_starter.py
# Сценарий целиком, ответы подаются через stdin (без TTY — меню с номерами):
printf '\n\n1\n' | LOCAL_AI_STARTER_DRY_RUN=1 LOCAL_AI_STARTER_HOME="$(mktemp -d)" python3 local_ai_starter.py
```

- **Кириллица только в `STRINGS["ru"]`**: искать `[А-Яа-яЁё]` вне этого блока и в `RunMe.*`.
- **Меню со стрелками**: запустить мастер под `pty.fork()` и слать `\x1b[B`, `\x1b[A`, `\r`.
  Проверено 2026-11-04 на macOS.
- **Сообщения о сети**: `check_network(["https://10.255.255.1/x"])` даёт таймаут 15 с,
  `https://no-such-host.invalid/x` — DNS, несуществующий ассет GitHub — 404 ([network](../entities/network.md)).
- **Установка без интернета**: положить архивы в папку, `python3 -m http.server 8765`, подменить
  `m.LLAMA_URL` / `m.OPENCODE_URL` и вызвать `install_llama()` / `install_opencode()`, затем
  `engines/llama.cpp/llama-server --version`.
- **Докачка**: обрезанный `<file>.part` + `download()` с GitHub докачивает только хвост;
  `http.server` (без Range) — файл качается заново.
- **Среда MLX без полной загрузки**: `_install_archive(UV_URL, …)`, затем `uv venv … --python 3.12`
  и `uv pip install --dry-run mlx-lm==…` с `uv_env()` и подменённым `HOME`.
- **Список файлов MLX-модели**: подменить `m.download` заглушкой и вызвать `install_model` для
  `*-mlx` профиля — настоящий запрос к API Hugging Face, без весов.
- **Замер скорости**: поддельный SSE-сервер, отдающий дельты `reasoning_content` (как llama.cpp)
  или `reasoning` (как MLX) и `usage`; `_stream_completion` должен посчитать токены и TTFT.
- **Переезд раскладки**: создать `bin/llama-server` и `models/qwen/*.gguf.part`, вызвать `migrate_layout()`.
- **Обновление**: `LOCAL_AI_STARTER_UPDATE_API` на локальный `http.server` с `latest.json`
  (`tag_name`, `body`) и `LOCAL_AI_STARTER_UPDATE_ZIP='http://127.0.0.1:<port>/{tag}.zip'` (архив с
  верхней папкой `local-ai-starter-<ver>/`); проверить «не сейчас», «пропустить», ZIP-замену и
  перезапуск на копии без `.git`, git-режим — на клоне локального bare-репозитория с тегом и
  лишним коммитом после него ([updater](../entities/updater.md)).
- **Изоляция OpenCode**: `HOME=<пустая папка>`, `opencode models local-ai-starter` и
  `opencode debug config` с `opencode_env()` — в HOME ничего от OpenCode.
- **Стартовое меню без загрузок**: во временном `LOCAL_AI_STARTER_HOME` создать пустые файлы моделей
  (`models/gguf/qwen/<файл>.gguf`, все компоненты в `models/sd/`, `models/tts/`) и бинарники движков
  (`engines/llama.cpp/llama-server`, `llama-tts`, `engines/stable-diffusion.cpp/sd-cli`, `opencode/opencode`),
  в `state.json` — `profile`; затем dry-run: строки «Запустить: …», порядок, тест-кейсы всех видов.
- **Прогонщик тест-кейсов без модели**: подменить `m.opencode_binary` скриптом, печатающим события
  `step_finish`/`tool_use`/`text`, `m.bring_up` — словарём с портом поддельного `/metrics`
  (`http.server`), и вызвать `run_case`; проверить токены, скорости, `check` pass/fail
  ([test-cases](../entities/test-cases.md)).
- **Верификаторы кейсов**: запустить `test-cases/code/verify/*.py` в папке с эталонным решением
  (должен быть код 0) и с исходными fixtures (код 1).
- **Пиковая память**: `run_measured` на `python3 -c "x=bytearray(300_000_000); ..."` — около 290 МБ.

## Ручной чеклист (из README)

- macOS Apple Silicon, оба движка: чистый старт → OpenCode правит `index.html` → `/exit` → меню →
  замер скорости → смена движка → повторный запуск (в стартовом меню оба) → остановка → «Удалить всё».
- Картинки, видео, речь: по одной генерации и по одному тест-кейсу каждого вида; картинка Flux не белая.
- Прерванная загрузка модели (докачка), заблокированный хост (сообщение), занятый порт 8080
  ([server-lifecycle](../entities/server-lifecycle.md)), мало места на диске.
- Linux и Windows на реальных машинах.

Результаты — в [status](../status.md), найденные баги — в [debugging_log](../debugging_log.md).
Перед прогоном с реальной моделью предупредить пользователя: загрузка 2,3–4,7 ГБ.

## Related Pages
[build](build.md)
