# Test cases

Source: [`local_ai_starter.py`](../../../local_ai_starter.py), [`test-cases/`](../../../test-cases/README.md)

## Purpose
Одинаковые задачи для сравнения моделей: мастер сам прогоняет кейс на одной или всех скачанных
моделях вида, меряет время, память и токены, проверяет результат и сводит всё в таблицу.

## Key API
- Кейсы — `test-cases/<kind>/<id>.md`: строки `key: value`, `---`, промпт. Формат и ключи
  (`fixtures`, `check`, `expect`, `contains`, `timeout`, `seed`, `size`, `steps`, `frames`, `lang`) —
  в `test-cases/README.md`. `load_cases()` — `local_ai_starter.py:1908`; медиапромпт склеивается в одну строку.
- Набор на 2026-11-05: code — `cli-log-analyzer`, `fix-failing-tests`, `landing-page`, `seo-audit`
  (klukyanov.ru, через webfetch OpenCode); image — `portrait`, `text-poster`, `complex-scene`;
  video — `cat-walk`, `city-pan`; speech — `short-paragraph`, `russian-paragraph`, `long-article`.
- Скрытые проверки — `test-cases/code/verify/*.py`, запускаются в рабочей папке модели
  (`check: python3 {case_dir}/verify/...`), модель их не видит. `cli-log-analyzer` сам считает истину
  по `access.log` (402 строки, одна битая, один размер `-`) и сравнивает 9 полей JSON, плюс требует
  ≥ 5 своих тестов модели; `fix-failing-tests` гоняет исходные тесты из `fixtures/` против
  `inventory.py` модели (правку тестов не засчитать); `landing-page` — 14 структурных требований.
- `run_test_cases()` — `local_ai_starter.py:2129`: вид → кейс или все → модель или все; модель во
  внешнем цикле, чтобы сервер грузился один раз на модель. Ctrl+C прерывает серию, сводка остаётся.
- `run_case()` — `local_ai_starter.py:2019`: папка `test-runs/<прогон>/<кейс>/<модель>/`, модель
  работает в `work/` (туда копируются fixtures), рядом `metrics.json`, `check.log`, для кода —
  `events.jsonl`, `opencode.log`, `answer.md`. Ошибка `RuntimeError` даёт строку со статусом `fail`.
- `_run_code_case()` — `local_ai_starter.py:2053`: `bring_up` + `opencode.json`, затем
  `opencode run --format json --auto --model local-ai-starter/<id> --dir work "<промпт>"`
  (флаги сверены с исходником `run.ts` v1.19.5: `--auto` одобряет запросы прав, без него они
  отклоняются). Токены — сумма `part.tokens` событий `step_finish` (`parse_events`, `:1946`),
  вызовы инструментов — число `tool_use`. Для llama.cpp скорости чтения и генерации — разница
  счётчиков `/metrics` до и после (`llama_metrics`, `:1928`; сервер запускается с `--metrics`).
  Для MLX — выходные токены / общее время, с пометкой в `metrics.json`.
- `run_measured()` — `local_ai_starter.py:1759` и `PeakMemory` (`:1723`): фоновый поток опрашивает RSS
  (`ps -o rss=`, на Windows `tasklist /FO CSV`) каждые 0,5 с (1 с на Windows); для кода меряется
  процесс сервера модели, для медиа — сам движок. Таймаут убивает процесс (`terminate` → `kill`).
- `run_check()` — `local_ai_starter.py:1973`: `expect`, `contains`, `check`; `python3` в `check`
  заменяется на `sys.executable`. Результат `pass`/`fail` или пусто, если проверки нет.
- `append_result()` / `write_summary()` — `local_ai_starter.py:2086`, `:2098`: строка в
  `test-results/results.csv` (колонки `RESULT_FIELDS`, `:1903`) и пересборка `results.md` —
  по каждому кейсу последний прогон каждой модели.

- Отправка результатов (добавлено 2026-11-12): после прогона `run_test_cases()` вызывает `share_results(rows, run_id)`.
  `build_report()` собирает markdown (версия, система, чип, ОЗУ, таблица и тот же CSV в `<details>`) только по
  строкам этого прогона и только по полям `SHARE_FIELDS` — без `run`, `output`, `notes` (там бывают пути).
  Пользователь видит текст целиком, выбирает «скопировать и открыть страницу» / «только файл» / «нет».
  Копирование: `copy_to_clipboard()` (pbcopy, clip с BOM UTF-16, wl-copy/xclip/xsel); страница
  `github.com/<UPDATE_REPO>/issues/new?title=…` — тело вставляет сам пользователь (в URL длинный отчёт не
  умещается). Файл `test-results/share-<run>.md` сохраняется всегда. Ни токенов, ни сервера не нужно.

## Collaborators
[opencode-integration](opencode-integration.md), [server-lifecycle](server-lifecycle.md),
[sd-engine](sd-engine.md), [speech](speech.md), [speed-test](speed-test.md) (ранний замер скорости).

## Known Issues
- RSS на macOS может не учитывать всю память Metal (особенно у MLX); не сверено с `footprint` на
  реальной модели.
- `--auto` разрешает модели запускать команды; рабочая папка — внутри `local-ai/test-runs/`, но
  команды не изолированы песочницей. Предупреждение показывается перед прогоном.
- Прогон с настоящей моделью не делался. Проверено: dry-run всех видов, `run_measured` на процессе
  с 300 МБ (пик 294 МБ) и с таймаутом, `_run_code_case` с поддельным `opencode` и поддельным
  `/metrics` (токены, скорости, check pass/fail), верификаторы на эталонных и сломанных решениях.
- `seo-audit` зависит от сети и от того, как модель пользуется webfetch; проверка только по словам.

## Related Pages
[architecture](../architecture.md), [test](../workflows/test.md), [status](../status.md)
