# llama-engine

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Основной движок на всех системах: закреплённая сборка llama.cpp и модели GGUF.

## Key API
- `LLAMA_BUILD`, `LLAMA_URL`, `LLAMA_SHA256` — `local_ai_starter.py:84-94`. Одна сборка для
  всех, хеш для каждого из 6 ключей платформы.
- `llama_platform()` — `local_ai_starter.py:1071`: `macos-*`, `ubuntu-*`, `win-cpu-*` × `arm64|x64`.
- `install_llama()` — `local_ai_starter.py:1427`, через `_install_archive` (`:1427`) в
  `engines/llama.cpp/`: загрузка с докачкой и SHA-256 ([network](network.md)), exec-бит файлам `llama*`.
- GGUF-модели скачивает сам мастер (`install_model`, `local_ai_starter.py:1500`) в
  `models/gguf/<family>/`, а не `llama-server -hf`: у того своя нечитаемая раскладка кэша.
- `server_binary()` — `local_ai_starter.py:1349`. В том же архиве `llama-tts` — движок речи ([speech](speech.md)),
  exec-бит он получает вместе с остальными `llama*`.

## Collaborators
- [server-lifecycle](server-lifecycle.md) — запуск; [network](network.md) — загрузка и распаковка;
  [mlx-engine](mlx-engine.md) — второй движок на Apple Silicon; [speed-test](speed-test.md).

## Known Issues
- На Windows и Linux — CPU-сборки, GPU не настроен.

## Related Pages
[update-llama-build](../workflows/update-llama-build.md), [debugging_log](../debugging_log.md)
