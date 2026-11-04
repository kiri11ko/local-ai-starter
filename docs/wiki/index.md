# Local AI Starter — Wiki

Мастер, который одним двойным щелчком ставит движок (llama.cpp или MLX), модель Qwen и OpenCode и открывает
OpenCode на локальной модели в терминале (macOS, Linux, Windows). Весь код — один файл
[`local_ai_starter.py`](../../local_ai_starter.py).

## Обзор

- [architecture.md](architecture.md) — слои файла, поток запуска, раскладка папки `local-ai/`
- [status.md](status.md) — что работает, что не проверено, что дальше
- [log.md](log.md) — хронология изменений (append-only)
- [debugging_log.md](debugging_log.md) — найденные и исправленные проблемы

## Сущности

- [wizard-flow](entities/wizard-flow.md) — `main`, `ensure_installed`, меню после OpenCode, модели на диске
- [terminal-ui](entities/terminal-ui.md) — меню со стрелками, ANSI, оформление вывода
- [i18n](entities/i18n.md) — `STRINGS`, определение языка системы
- [network](entities/network.md) — проверка доступности, докачка, SHA-256, распаковка
- [profiles](entities/profiles.md) — линейка моделей для обоих движков, выбор по памяти
- [llama-engine](entities/llama-engine.md) — закреплённая сборка llama.cpp, модели GGUF
- [mlx-engine](entities/mlx-engine.md) — MLX на Apple Silicon: uv, Python, mlx-lm, модели MLX
- [speed-test](entities/speed-test.md) — замер скорости и `benchmarks.csv`
- [server-lifecycle](entities/server-lifecycle.md) — запуск, контекст, готовность, остановка, `state.json`
- [opencode-integration](entities/opencode-integration.md) — закреплённый OpenCode, конфиг, изоляция, workspace
- [updater](entities/updater.md) — проверка и установка новой версии из GitHub Releases
- [launchers](entities/launchers.md) — `RunMe.command` / `.sh` / `.bat`

## Рабочие процессы

- [build](workflows/build.md) — запуск, dry-run, переменные окружения
- [test](workflows/test.md) — проверки и ручной чеклист
- [release](workflows/release.md) — как выпустить версию, чтобы её получили пользователи
- [update-llama-build](workflows/update-llama-build.md) — как поднять версию llama.cpp
- [update-opencode](workflows/update-opencode.md) — как поднять версию OpenCode
- [update-models](workflows/update-models.md) — как обновить линейку моделей

## Внешние ссылки

- Релизы llama.cpp: https://github.com/ggml-org/llama.cpp/releases
- Релизы OpenCode: https://github.com/anomalyco/opencode/releases, документация https://opencode.ai/docs
- Модели: `ggml-org/*-GGUF`, `unsloth/*-GGUF`, `mlx-community/*` на Hugging Face
- mlx-lm: https://pypi.org/project/mlx-lm/, uv: https://github.com/astral-sh/uv/releases
