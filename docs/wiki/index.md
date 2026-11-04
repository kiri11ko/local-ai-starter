# Local AI Starter — Wiki

Мастер, который ставит и запускает локальную языковую модель (llama.cpp + Qwen GGUF)
на macOS, Linux и Windows. Весь код — один файл [`local_ai_starter.py`](../../local_ai_starter.py).

## Обзор

- [architecture.md](architecture.md) — устройство мастера, поток данных, раскладка папки `local-ai/`
- [status.md](status.md) — что работает, что не проверено, что дальше
- [log.md](log.md) — хронология изменений (append-only)
- [debugging_log.md](debugging_log.md) — найденные и исправленные проблемы

## Сущности

- [wizard-flow](entities/wizard-flow.md) — `main`, первый запуск, меню управления, ввод-вывод
- [profiles](entities/profiles.md) — профили моделей и выбор по памяти и диску
- [llama-engine](entities/llama-engine.md) — закреплённая сборка llama.cpp: скачивание, SHA-256, распаковка
- [server-lifecycle](entities/server-lifecycle.md) — запуск, проверка готовности, остановка `llama-server`, `state.json`
- [opencode-integration](entities/opencode-integration.md) — установка OpenCode в изоляции и учебный проект
- [launchers](entities/launchers.md) — файлы двойного клика `.command` / `.sh` / `.bat`

## Рабочие процессы

- [build](workflows/build.md) — запуск, dry-run, переменные окружения
- [test](workflows/test.md) — проверка синтаксиса и ручной чеклист
- [update-llama-build](workflows/update-llama-build.md) — как поднять версию llama.cpp

## Внешние ссылки

- Релизы llama.cpp: https://github.com/ggml-org/llama.cpp/releases
- OpenCode: https://opencode.ai/docs
- Модели: Qwen на Hugging Face (`Qwen/Qwen3-4B-GGUF`, `Qwen/Qwen3-8B-GGUF`, `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`)
