# Состояние

На 2026-11-04.

## What Works

- Первый запуск и меню управления — см. [wizard-flow](entities/wizard-flow.md).
- Скачивание закреплённой сборки llama.cpp с проверкой SHA-256 для 6 платформ — [llama-engine](entities/llama-engine.md).
- Запуск сервера в фоне, ожидание `/health`, пробный запрос, остановка — [server-lifecycle](entities/server-lifecycle.md).
- Учебный проект OpenCode с провайдером на локальный сервер (macOS/Linux) — [opencode-integration](entities/opencode-integration.md).
- Режим dry-run для прогона сценария без загрузок — [build](workflows/build.md).

## What's Broken / Not Verified

- Автотестов нет; ручной чеклист из README ещё не пройден целиком — [test](workflows/test.md).
- Linux и Windows на реальных машинах не проверялись.
- Не проверено, что модель профиля «Для программирования» действительно вызывает инструменты OpenCode.
- Риски, найденные при чтении кода, — в разделах Known Issues сущностей
  ([server-lifecycle](entities/server-lifecycle.md), [wizard-flow](entities/wizard-flow.md), [llama-engine](entities/llama-engine.md)).

## In Progress

- Ничего.

## Next Steps

- Пройти ручной чеклист на macOS Apple Silicon, затем Linux и Windows.
- GPU-сборки llama.cpp для Windows/Linux (сейчас CPU).
- Английский интерфейс мастера (сейчас тексты только на русском).

## Out of Scope

- Сторонние Python-зависимости, изменения PATH и глобальных конфигов.
- Доступ к серверу извне `127.0.0.1`.
- Установка OpenCode на Windows силами мастера.
