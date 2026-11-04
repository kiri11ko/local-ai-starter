# llama-engine

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Скачивание закреплённой сборки llama.cpp под текущую платформу с проверкой контрольной
суммы и безопасной распаковкой в `bin/`.

## Key API
- `LLAMA_BUILD`, `LLAMA_URL`, `LLAMA_SHA256` — `local_ai_starter.py:44-53`. Одна сборка для
  всех; хеш для каждого из 6 ключей платформы.
- `llama_platform()` — `local_ai_starter.py:152`: `macos-arm64|x64`, `ubuntu-arm64|x64`,
  `win-cpu-arm64|x64`.
- `install_llama()` — `local_ai_starter.py:284`. Пропускается, если `llama-server` уже есть.
  Скачивает архив, сверяет SHA-256 (при несовпадении удаляет архив и падает), пересоздаёт `bin/`.
- `extract()` / `_write_members()` — `local_ai_starter.py:245`, `:265`. Снимают общую верхнюю
  папку архива, отклоняют пути вне `target`, восстанавливают права и выставляют exec-бит
  файлам `llama*` (zip права не хранит).
- `download()` — `local_ai_starter.py:220`, с прогрессом в МБ; `sha256_of()` — `:237`.
- `server_binary()` — `local_ai_starter.py:214`.

## Collaborators
- [server-lifecycle](server-lifecycle.md) запускает `server_binary()`.
- Сами модели качает не этот модуль, а `llama-server -hf` в `models/`.

## Known Issues
- `download()` не докачивает: оборванная загрузка архива начинается заново.
- На Windows и Linux — CPU-сборки, GPU не настроен.

## Related Pages
[update-llama-build](../workflows/update-llama-build.md), [architecture](../architecture.md)
