# Состояние

На 2026-11-04.

## What Works

- Сценарий «двойной щелчок → установка → OpenCode в терминале» и меню после выхода
  ([wizard-flow](entities/wizard-flow.md)); прогнан в dry-run на обоих языках.
- Меню со стрелками и запасной режим с номерами ([terminal-ui](entities/terminal-ui.md)); на macOS через pty.
- Интерфейс en/ru по языку системы ([i18n](entities/i18n.md)).
- Проверка сети с понятными сообщениями (таймаут, DNS, 404), докачка через Range, SHA-256
  ([network](entities/network.md)); проверено на GitHub, Hugging Face и локальном сервере.
- Установка llama.cpp b12110 с symlink-ами библиотек, `llama-server --version` запускается
  ([llama-engine](entities/llama-engine.md)).
- Выбор движка на Apple Silicon и раздельное хранение `engines/` и `models/<engine>/`; переезд
  раскладки v2 ([wizard-flow](entities/wizard-flow.md)).
- Линейка Qwen3.5/3.6/3.8 для обоих движков с рекомендацией по памяти ([profiles](entities/profiles.md)).
- Среда MLX: uv 0.13.1 и CPython 3.12.15 ставятся внутрь `engines/mlx/`, зависимости mlx-lm
  0.32.2 разрешаются (`--dry-run`) ([mlx-engine](entities/mlx-engine.md)).
- Обновление при запуске из GitHub Releases: вопрос с заметками, «пропустить версию», git-перемотка на тег,
  замена файлов из ZIP, перезапуск, работа без сети — на поддельном релизе и локальном bare-репозитории
  ([updater](entities/updater.md)). Сквозная проверка на настоящем релизе v2.1.0: копия с `VERSION`
  2.0.9 предложила 2.1.0 с заметками, скачала архив и перезапустилась на 2.1.0.
- Разбор потока в замере скорости — на поддельном сервере в обоих форматах ([speed-test](entities/speed-test.md)).
- OpenCode v1.19.5: установка, конфиг принимается, данные изолированы в `local-ai/opencode-home`
  ([opencode-integration](entities/opencode-integration.md)).

## What's Broken / Not Verified

- Полный прогон с реальной моделью не делался ни на одном движке: загрузки 2,6–37 ГБ на
  медленном канале. Не проверено, что модели вызывают инструменты OpenCode и укладываются в
  память с контекстом 32K/64K. Пользователь сам сравнивает llama.cpp и MLX на 64-ГБ Mac и
  пришлёт отзыв.
- Полная установка mlx-lm (~300 МБ) и запуск `mlx_lm.server` не проверялись.
- Linux и Windows на реальных машинах не проверялись (меню со стрелками, `msvcrt`, `SetConsoleMode`,
  `opencode.exe`).
- Риски из кода — в Known Issues страниц [server-lifecycle](entities/server-lifecycle.md),
  [network](entities/network.md), [terminal-ui](entities/terminal-ui.md).

## In Progress

- Ничего.

## Next Steps

- Отзыв пользователя по замерам llama.cpp против MLX: оставить оба, сделать MLX движком по
  умолчанию на Mac или убрать его ([speed-test](entities/speed-test.md)).
- Прогон с моделью: правка `index.html` через OpenCode; при плохом tool calling сменить
  рекомендуемые модели ([profiles](entities/profiles.md)).
- Linux и Windows.
- GPU-сборки llama.cpp для Windows/Linux (сейчас CPU).
- Ещё семейства моделей (например, gemma): [update-models](workflows/update-models.md).

## Out of Scope

- Сторонние Python-зависимости, изменения PATH и глобальных конфигов.
- Доступ к серверу извне `127.0.0.1`.
