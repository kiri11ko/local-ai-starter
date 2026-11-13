# Состояние

На 2026-11-13. Текущий релиз — v2.4.0 (тег на `7df43c7`). Последнее ревью — без запуска реальных моделей.

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
- Команда `local-opencode` (2026-11-12): установка скрипта и ссылки в `~/.local/bin`, повторный вызов, чужой файл, удаление, `--here` в dry-run — на временных данных; живой прогон с моделью ещё не делался ([opencode-integration](entities/opencode-integration.md)).
- Разбор потока в замере скорости — на поддельном сервере в обоих форматах ([speed-test](entities/speed-test.md)).
- OpenCode v1.19.5: установка, конфиг принимается, данные изолированы в `local-ai/opencode-home`
  ([opencode-integration](entities/opencode-integration.md)).
- Стартовое меню со всеми скачанными конфигурациями и выбор вида (код / картинки / видео / речь) —
  dry-run на обоих языках, в том числе на подделанных «скачанных» файлах ([wizard-flow](entities/wizard-flow.md)).
- Картинки и видео через stable-diffusion.cpp `master-1050-58bb3c1`, речь через `llama-tts` (Qwen3-TTS):
  пины и SHA-256 всех файлов собраны с GitHub и Hugging Face, архив sd.cpp для macOS скачан и сверен,
  команды движков собираются ([sd-engine](entities/sd-engine.md), [speech](entities/speech.md)).
- Тест-кейсы (4 кода, 3 картинки, 2 видео, 3 речи): прогон, замер пиковой памяти и токенов,
  скрытые проверки, `results.csv` и `results.md` — на поддельных OpenCode и `/metrics`
  ([test-cases](entities/test-cases.md)).
- Перенос настроек агентов (2026-11-13): юнит-тесты 5/5 и реальный прогон Claude → Codex + OpenCode
  (глобальные + 14 проектов); существующие файлы не перезаписываются, границы переноса —
  [transfer](entities/transfer.md). Автотесты в `tests/` ([test](workflows/test.md)).

## What's Broken / Not Verified

- Ревью 2026-11-09 подтвердило две ошибки основных сценариев: миграция переносит актуальные
  медиа-каталоги в GGUF, выбор нового профиля может переиспользовать сервер старой модели.
  План исправления и критерии проверки: [P0 в бэклоге](todo.md#p0--ошибки-основных-сценариев).

- Полный прогон с реальной моделью не делался ни на одном движке: загрузки 2,6–37 ГБ на
  медленном канале. Не проверено, что модели вызывают инструменты OpenCode и укладываются в
  память с контекстом 32K/64K. Пользователь сам сравнивает llama.cpp и MLX на 64-ГБ Mac и
  пришлёт отзыв.
- Полная установка mlx-lm (~300 МБ) и запуск `mlx_lm.server` не проверялись.
- Ни одной реальной генерации картинки, видео или речи и ни одного реального прогона тест-кейса:
  загрузки от 1,4 до 12 ГБ. Не проверено, что `--backend vae=cpu` нужен и достаточен для Flux на этой
  сборке, и что RSS на macOS отражает память Metal.
- Linux и Windows на реальных машинах не проверялись (меню со стрелками, `msvcrt`, `SetConsoleMode`,
  `opencode.exe`).
- Риски из кода — в Known Issues страниц [server-lifecycle](entities/server-lifecycle.md),
  [network](entities/network.md), [terminal-ui](entities/terminal-ui.md).

## In Progress

- Ничего.

## Next Steps

- Сначала выполнить [план ревью P0–P1](todo.md#по-результатам-ревью-2026-11-09): исправления
  миграции и переключения с регрессионными тестами, учёт версий, установка и процессы.

- Реальный прогон: SD-Turbo (4,9 ГБ), Qwen3-TTS Q4 (1,4 ГБ), тест-кейс `fix-failing-tests` на Qwen3.5 4B.
- Отзыв пользователя по замерам llama.cpp против MLX: оставить оба, сделать MLX движком по
  умолчанию на Mac или убрать его ([speed-test](entities/speed-test.md)).
- Прогон с моделью: правка `index.html` через OpenCode; при плохом tool calling сменить
  рекомендуемые модели ([profiles](entities/profiles.md)).
- Linux и Windows.
- GPU-сборки llama.cpp и sd.cpp для Windows/Linux (сейчас CPU), см. [todo](todo.md).
- Ещё семейства моделей (например, gemma): [update-models](workflows/update-models.md).

## Out of Scope

- Сторонние Python-зависимости, изменения PATH и глобальных конфигов.
- Доступ к серверу извне `127.0.0.1`.
