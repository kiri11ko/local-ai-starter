# Wizard flow

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Сценарии: стартовое меню со скачанными конфигурациями, выбор новой (вид → движок → модель), запуск
OpenCode или сеанса генерации, меню управления после выхода.

## Key API
- `main(argv)` — `local_ai_starter.py:2614`. Баннер (с `VERSION`) → `check_for_update()` ([updater](updater.md)) → `migrate_layout()` → `start_menu()`
  (если нет `--menu`) → `menu()`. Ловит `Quit` (выход из стартового меню, молча), `Cancelled`/`KeyboardInterrupt`,
  `NetworkError` и ожидаемые ошибки.
- `start_menu()` — `local_ai_starter.py:2559`. Ничего не скачано → сразу `launch(None)`. Иначе по строке
  «Запустить: …» на каждую скачанную конфигурацию (`installed_profiles()`, `:2341`, последняя запущенная
  первой), затем «Скачать новую конфигурацию», «Тест-кейсы» ([test-cases](test-cases.md), после них меню
  показывается снова), «Меню управления», «Выйти». Подпись строки — `profile_title()` (`:2331`):
  «Вид · модель · движок · квантование».
- `launch(profile)` — `local_ai_starter.py:2549`: `None` → `choose_profile()`; код → `run_opencode`,
  остальное → `media_session` ([sd-engine](sd-engine.md), [speech](speech.md)).
- `migrate_layout()` — `local_ai_starter.py:2301`: раскладка v2 (`bin/`, `models/<family>/`) переезжает
  в `engines/llama.cpp/` и `models/gguf/<family>/`, включая недокачанные `.part`.
- `run_opencode(profile)` — `local_ai_starter.py:2542`: `ensure_installed` → `bring_up` → `launch_opencode`.
- `choose_kind()` — `local_ai_starter.py:2348`: код, картинки, видео, речь (картинки и видео — только где
  есть сборка sd.cpp); виды, у которых уже есть скачанная модель, помечены ✓.
- `choose_engine()` — `local_ai_starter.py:2359`: только для кода и только на Apple Silicon спрашивает
  llama.cpp (по умолчанию) или MLX; установленные помечены ✓. На остальных системах сразу `gguf`.
- `ensure_installed(profile)` — `local_ai_starter.py:2406`. Профиль спрашивается, только если его нет.
  Задачи — только недостающие: движок профиля (`engine_task`, `:2397`: `gguf`/`tts` → llama.cpp, `mlx`, `sd`),
  модель (для медиа — только отсутствующие компоненты), OpenCode (только для кода). Дальше проверка места
  (сумма + 1 ГБ), одно подтверждение, `check_network` по всем URL, шаги `[i/n]`.
- `menu(profile)` — `local_ai_starter.py:2581`. Пункты: остановить и выйти (по умолчанию),
  выйти с работающим сервером, вернуться (в OpenCode или «Вернуться: <конфигурация>» для медиа),
  другая конфигурация, тест-кейсы, замер скорости ([speed-test](speed-test.md), для медиапрофиля
  спросит модель для кода), веб-чат (только llama.cpp, `open_chat`, `:2442`), модели на диске,
  состояние, удалить всё.
- `manage_models()` — `local_ai_starter.py:2495`, `model_entries()` — `:2479`: GGUF-файлы
  (и `.part`), MLX-папки (без `.complete` — «не докачано»), файлы `models/sd/` и `models/tts/`. Можно открыть
  папку или удалить модель; если она в работающем сервере, сервер сначала останавливается.
- `show_status()` — `local_ai_starter.py:2453`, `uninstall()` — `:2532`.

## Collaborators
- [terminal-ui](terminal-ui.md) — `ask`, `yes_no`, `step`; [profiles](profiles.md) — `choose_profile`;
  [network](network.md) — `check_network`; [llama-engine](llama-engine.md), [mlx-engine](mlx-engine.md),
  [server-lifecycle](server-lifecycle.md), [opencode-integration](opencode-integration.md).

## Known Issues
- В dry-run `ensure_installed` всегда показывает полный план: проверки наличия файлов намеренно обходятся.
  Поэтому прогон тест-кейсов вызывает его, только если не хватает движка или OpenCode.
- Стартовое меню проверено в dry-run на подделанных «скачанных» файлах (пустые файлы в
  `models/` и `engines/`), на реальных моделях — нет.

## Related Pages
[architecture](../architecture.md), [build](../workflows/build.md), [test](../workflows/test.md)
