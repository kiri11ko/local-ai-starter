# llama-engine

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Закреплённая сборка llama.cpp под текущую платформу: скачать, проверить, распаковать в `bin/`.

## Key API
- `LLAMA_BUILD`, `LLAMA_URL`, `LLAMA_SHA256` — `local_ai_starter.py:52-62`. Одна сборка для
  всех, хеш для каждого из 6 ключей платформы.
- `llama_platform()` — `local_ai_starter.py:564`: `macos-*`, `ubuntu-*`, `win-cpu-*` × `arm64|x64`.
- `install_llama()` — `local_ai_starter.py:864`, через общий `_install_archive` (`:853`):
  загрузка с докачкой и SHA-256 ([network](network.md)), пересоздание `bin/`, exec-бит файлам `llama*`.
- `install_model(profile)` — `local_ai_starter.py:888`: GGUF качает сам мастер в
  `models/<family>/`, а не `llama-server -hf` (у того своя нечитаемая раскладка кэша).
- `server_binary()` — `local_ai_starter.py:831`.

## Collaborators
- [server-lifecycle](server-lifecycle.md) — запуск `server_binary()`.
- [network](network.md) — загрузка и распаковка.

## Known Issues
- На Windows и Linux — CPU-сборки, GPU не настроен.

## Related Pages
[update-llama-build](../workflows/update-llama-build.md), [debugging_log](../debugging_log.md)
