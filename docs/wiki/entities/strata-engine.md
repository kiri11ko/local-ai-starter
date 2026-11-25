# strata-engine

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose

Третий движок кода (помимо llama.cpp и MLX): терминал [Strata](https://github.com/Niko1221/Strata)
(v0.2.21), созданный под Qwen3.8-Flash-Next (MoE 125B, 6B активных). В отличие от остальных
движков мастер не скачивает веса сам: `strata launch` сам доставляет движок под видеокарту и
модель (десятки ГБ), мастер закрепляет только установщик терминала. Всё хранится внутри
`engines/strata/` — правило «ничего вне каталога данных» соблюдается без исключений.

## Key API

- Пины — `STRATA_VERSION` 0.2.21, `STRATA_CONTROL_VERSION` 0.1.68, `STRATA_FEED` (релиз v0.2.21),
  `STRATA_INSTALLERS` (install.sh/install.ps1 + SHA-256 со страницы релиза), `STRATA_SIZE_MB` 200.
  Установщик сам проверяет манифест и подписанный фид; после установки пишет `.installed`.
- `strata_env()` — `STRATA_DATA_DIR=engines/strata/`, `STRATA_BIN_DIR=engines/strata/bin` для
  установщика и каждого вызова `strata` (установщик обе переменные документирует).
- `install_strata()` — скачивает закреплённый установщик (`download` + SHA-256), запускает
  `sh install.sh` / `powershell … install.ps1` с `strata_env()`; ошибка — `strata_launch_failed`.
- `strata_installed()` — `terminal/<control-версия>/bin/strata` или ссылка `bin/strata`;
  `strata_binary()` — оба суффикса на Windows (`.exe`, `.cmd`).
- `strata_control(*args)` — один вызов CLI с `strata_env()`, cwd `engines/strata/`.
- `strata_supported()` — Darwin arm64 + macOS ≥ 15; Linux x86_64/aarch64; Windows x86_64.
  Гейтится в `available()` и `choose_engine()`.
- `strata_plan(profile)` — `strata launch --plan --family … --model … --data-dir … --output json`:
  размер загрузки (`download.gb`), `engine_missing`, `engine_usable`, предупреждения. Вызывается
  в `ensure_installed` до экрана плана; `strata_check_plan()` отказывает только при
  `engine_usable=false` **без** `engine_missing` (иначе «движок просто ещё не скачан»).
- Профили — `_strata()`: `family` = селектор семейства Strata (`qwen`, `coder`,
  `inkling-2-mini`), `file` = селектор размера (`q2_0`, `IQ1_M`, `SQ-10`…), `repo` пустой.
  Пять профилей: SQ-10 (16 ГБ), SQ-15 (24), Coder IQ1_M (32), Q2_0 (48), IQ2_XS (48).
- `strata_models(refresh)` — кэш `strata models list --installed --output json`;
  `strata_profile_installed()` матчит запись по подстрокам `file`+`family` (формат записей CLI
  на реальной модели не проверен — см. Known Issues). Кэш сбрасывается после первого запуска.
- Запуск — `start_strata()` (`start_server` ветвится по `engine == "strata"`): форграундный
  `strata launch --family … --model … --context <tokens> --port … --data-dir engines/strata/data
  --api-key-env LOCAL_AI_STARTER_STRATA_KEY --yes --no-tui --output json`; прогресс в
  `server.log`, раз в 20 с — последняя строка в консоль. Ключ генерирует мастер
  (`secrets.token_urlsafe`), живёт в `state.json` как `api_key`.
- API: OpenAI-совместимый на `127.0.0.1:<port>/v1`; id модели в запросах — фиксированный
  `strata` (`api_model`). `/health` без ключа; защищённые запросы — `Authorization: Bearer <ключ>`
  (тест готовности в `wait_ready`, `_stream_completion` в замере скорости). Flash-Next по
  умолчанию думает (`enable_thinking`), тестовый запрос шлёт `chat_template_kwargs` и при
  отказе повторяется без них.
- Остановка — `stop_server()` ветка strata: `strata launch --stop`, затем ожидание, пока
  `/health` не отвалится. `running_state()` для strata смотрит только здоровье порта (pid
  не наш: сервер переживает процесс `strata launch`).

## Collaborators

- [profiles](profiles.md) — профили `_strata`, гейтинг `min_ram_gb`;
- [wizard-flow](wizard-flow.md) — `choose_engine` (третий пункт), `ensure_installed` (терминал +
  модель-задача «скачается при первом старте»);
- [server-lifecycle](server-lifecycle.md) — запуск/стоп/повторное использование;
- [opencode-integration](opencode-integration.md) — `write_opencode_config` добавляет `apiKey`;
- [speed-test](speed-test.md), [test-cases](test-cases.md) — счёт токенов как у llama.cpp
  (`reasoning_content`), скорости по стенному времени (ветка MLX), `/metrics` нет.

## Known Issues

- Живой прогон модели через Strata не выполнялся (загрузка 11–71 ГБ): проверены установка
  терминала во временном `LOCAL_AI_STARTER_HOME`, подпись, `--plan` (Inkling SQ-10, 11.1 ГБ),
  юнит-тесты на заглушках и dry-run en. На машине разработки (16 ГБ) Flash-Next не влезает.
- Формат записей `strata models list --installed` снят только с пустого списка; матчинг
  `strata_profile_installed` эвристический (подстроки). Если запись не матчится, профиль
  считается неустановленным — повторный `launch` идемпотентен.
- `install.ps1` на Windows: предположение, что он чтит `STRATA_DATA_DIR`/`STRATA_BIN_DIR` как
  install.sh, не проверено (нет Windows-машины); если нет — терминал уйдёт в домашнюю папку.
- «Модели на диске» не показывает и не удаляет файлы Strata (они вне `MODELS_DIR`); освобождение
  места — «Удалить всё» или сам Strata. Точка расширения: `strata models inspect/move`.
- На картах без движка Strata провалится на первом запуске (текст из журнала в
  `strata_launch_failed`); план не всегда различает «нет движка для карты» и «движок не скачан».
- Qwen3.6-35B-A3B через Strata не включена (на Mac-движке не работает, дублирует llama.cpp/MLX).

## Related Pages

[llama-engine](llama-engine.md), [mlx-engine](mlx-engine.md), [profiles](profiles.md),
[wizard-flow](wizard-flow.md), [server-lifecycle](server-lifecycle.md),
[opencode-integration](opencode-integration.md)
