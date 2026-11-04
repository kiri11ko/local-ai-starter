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
- OpenCode v1.19.5: установка, конфиг принимается, данные изолированы в `local-ai/opencode-home`
  ([opencode-integration](entities/opencode-integration.md)).

## What's Broken / Not Verified

- Полный прогон с реальной моделью не делался: загрузка 2,3–4,7 ГБ на медленном канале.
  Не проверено, что модель вызывает инструменты OpenCode и укладывается в память с контекстом 32K.
- Linux и Windows на реальных машинах не проверялись (меню со стрелками, `msvcrt`, `SetConsoleMode`,
  `opencode.exe`).
- Риски из кода — в Known Issues страниц [server-lifecycle](entities/server-lifecycle.md),
  [network](entities/network.md), [terminal-ui](entities/terminal-ui.md).

## In Progress

- Ничего.

## Next Steps

- Прогон с моделью на macOS Apple Silicon: правка `index.html` через OpenCode; при плохом
  tool calling сменить рекомендуемую модель ([profiles](entities/profiles.md)).
- Linux и Windows.
- GPU-сборки llama.cpp для Windows/Linux (сейчас CPU).
- Ещё семейства моделей (например, gemma) в `models/<family>/`.

## Out of Scope

- Сторонние Python-зависимости, изменения PATH и глобальных конфигов.
- Доступ к серверу извне `127.0.0.1`.
