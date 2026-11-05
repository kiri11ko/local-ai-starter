# Архитектура

Один файл [`local_ai_starter.py`](../../local_ai_starter.py), только стандартная библиотека,
Python 3.9+. Внешние процессы: локальный сервер модели (`llama-server` или `mlx_lm.server`),
OpenCode CLI в том же терминале и разовые запуски `sd-cli` / `llama-tts` для картинок, видео и речи.

## Слои файла

| Строки | Слой | Страница |
|---|---|---|
| `local_ai_starter.py:38-131` | константы, пути, пины llama.cpp, sd.cpp, uv/mlx-lm, OpenCode | [llama-engine](entities/llama-engine.md), [sd-engine](entities/sd-engine.md), [mlx-engine](entities/mlx-engine.md), [opencode-integration](entities/opencode-integration.md) |
| `local_ai_starter.py:134-314` | `Component`, `Profile`, `_MODELS`, `PROFILES` | [profiles](entities/profiles.md) |
| `local_ai_starter.py:319-740` | `STRINGS`, `detect_lang`, `t`, `size_text` | [i18n](entities/i18n.md) |
| `local_ai_starter.py:741-924` | терминал: ANSI, цвета, меню со стрелками | [terminal-ui](entities/terminal-ui.md) |
| `local_ai_starter.py:925-1050` | система, порты, PID, `state.json` | [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:1051-1236` | сеть: проверка, докачка, SHA-256, распаковка | [network](entities/network.md) |
| `local_ai_starter.py:1237-1419` | компоненты: движки, OpenCode, модели | [llama-engine](entities/llama-engine.md), [sd-engine](entities/sd-engine.md), [mlx-engine](entities/mlx-engine.md) |
| `local_ai_starter.py:1420-1571` | сервер | [server-lifecycle](entities/server-lifecycle.md) |
| `local_ai_starter.py:1572-1646` | замер скорости | [speed-test](entities/speed-test.md) |
| `local_ai_starter.py:1647-1706` | OpenCode: конфиг, рабочая папка, изоляция, запуск | [opencode-integration](entities/opencode-integration.md) |
| `local_ai_starter.py:1707-1777` | замер процесса: пиковая память, время, таймаут | [test-cases](entities/test-cases.md) |
| `local_ai_starter.py:1778-1900` | картинки, видео, речь: команды движков, сеанс генерации | [sd-engine](entities/sd-engine.md), [speech](entities/speech.md) |
| `local_ai_starter.py:1901-2184` | тест-кейсы: загрузка, прогон, проверка, `results.csv`/`.md` | [test-cases](entities/test-cases.md) |
| `local_ai_starter.py:2185-2298` | обновление из GitHub Releases | [updater](entities/updater.md) |
| `local_ai_starter.py:2299-2638` | переезд раскладки, выбор конфигурации, стартовое меню, меню, `main` | [wizard-flow](entities/wizard-flow.md) |

## Поток запуска

```
main
  check_for_update                     GitHub Releases, 5 с; новее VERSION -> спросить -> обновить и перезапуститься
  migrate_layout                       раскладка v2 -> v3 на месте
  start_menu                           (пропускается при --menu)
    скачанные конфигурации -> launch(profile)
    «Скачать новую» -> launch(None) -> choose_profile: вид -> движок (код) -> модель
    «Тест-кейсы» -> run_test_cases     и снова стартовое меню
    launch
      code:  run_opencode -> ensure_installed -> bring_up -> launch_opencode
      media: media_session -> ensure_installed -> generate (sd-cli / llama-tts) в цикле
  menu                                 после выхода из OpenCode или сеанса генерации
```

## Папка данных

Корень — `ROOT` (`local_ai_starter.py:51`): `local-ai/` рядом со скриптом или
`LOCAL_AI_STARTER_HOME`. Вне неё мастер ничего не пишет. Движки и модели разных
движков лежат в разных папках и друг друга не перетирают.

```
local-ai/
  engines/llama.cpp/          llama-server, библиотеки и их symlink-и
  engines/mlx/                uv/, python/ (CPython от uv), venv/ с mlx-lm, cache/, hf/, .installed
  engines/stable-diffusion.cpp/  sd-cli, sd-server, libstable-diffusion
  models/gguf/<семейство>/<файл>.gguf
  models/mlx/<семейство>/<репозиторий>/   файлы модели + .complete
  models/sd/<файл>, models/tts/<файл>     плоско; общие файлы (VAE, энкодеры) один раз
  opencode/                   бинарник OpenCode
  opencode-home/              XDG-папки OpenCode
  opencode.json               конфиг OpenCode: только локальный провайдер
  workspace/                  рабочая папка OpenCode
  outputs/<вид>/<дата>.<ext>  результаты сеансов генерации
  voices/                     необязательный образец голоса для речи
  test-runs/<прогон>/<кейс>/<модель>/   work/, metrics.json, events.jsonl, answer.md, check.log
  test-results/               results.csv (все прогоны), results.md (сводка)
  generate.log                вывод sd-cli / llama-tts
  benchmarks.csv              результаты замеров скорости
  state.json                  profile, engine, model_id, pid, port, ctx, started_at
  server.log                  вывод сервера (дописывается, у каждого запуска заголовок)
```

## Принципы

- Пользователь не технический: меню со стрелками, Enter выбирает рекомендуемое
  ([terminal-ui](entities/terminal-ui.md)). Язык интерфейса — по системе ([i18n](entities/i18n.md)).
- Ожидаемые ошибки: `RuntimeError` с текстом через `t()`, сетевые — `NetworkError`. `main`
  печатает их и возвращает 1 (`local_ai_starter.py:2614`).
- Всё, что качается, закреплено версией или коммитом и проверяется по SHA-256 ([network](entities/network.md)).
- Сервер слушает только `127.0.0.1`.
