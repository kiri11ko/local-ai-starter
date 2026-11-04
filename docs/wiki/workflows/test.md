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
  `bin/llama-server --version`.
- **Докачка**: обрезанный `<file>.part` + `download()` с GitHub докачивает только хвост;
  `http.server` (без Range) — файл качается заново.
- **Изоляция OpenCode**: `HOME=<пустая папка>`, `opencode models local-ai-starter` и
  `opencode debug config` с `opencode_env()` — в HOME ничего от OpenCode.

## Ручной чеклист (из README)

- macOS Apple Silicon: чистый старт → OpenCode правит `index.html` → `/exit` → меню →
  повторный запуск → остановка → «Удалить всё».
- Прерванная загрузка модели (докачка), заблокированный хост (сообщение), занятый порт 8080
  ([server-lifecycle](../entities/server-lifecycle.md)), мало места на диске.
- Linux и Windows на реальных машинах.

Результаты — в [status](../status.md), найденные баги — в [debugging_log](../debugging_log.md).
Перед прогоном с реальной моделью предупредить пользователя: загрузка 2,3–4,7 ГБ.

## Related Pages
[build](build.md)
