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
- **Изоляция OpenCode**: `HOME=<пустая папка>`, `opencode models local-ai-starter` и
  `opencode debug config` с `opencode_env()` — в HOME ничего от OpenCode.

## Ручной чеклист (из README)

- macOS Apple Silicon, оба движка: чистый старт → OpenCode правит `index.html` → `/exit` → меню →
  замер скорости → смена движка → повторный запуск → остановка → «Удалить всё».
- Прерванная загрузка модели (докачка), заблокированный хост (сообщение), занятый порт 8080
  ([server-lifecycle](../entities/server-lifecycle.md)), мало места на диске.
- Linux и Windows на реальных машинах.

Результаты — в [status](../status.md), найденные баги — в [debugging_log](../debugging_log.md).
Перед прогоном с реальной моделью предупредить пользователя: загрузка 2,3–4,7 ГБ.

## Related Pages
[build](build.md)
