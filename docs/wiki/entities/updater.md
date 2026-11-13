# Updater

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
При каждом запуске предложить новую версию мастера из GitHub Releases и поставить её, не трогая
`local-ai/` (модели, движки, настройки).

## Key API
- `VERSION` — `local_ai_starter.py:42`: должен совпадать с тегом релиза (`v2.1.0` ↔ `"2.1.0"`).
  `APP_DIR` — `:50`, папка файлов мастера; `ROOT` (данные) по умолчанию внутри неё.
- `UPDATE_REPO`, `UPDATE_API` (releases/latest), `UPDATE_ZIP` (архив тега) — `local_ai_starter.py:76`.
  Для тестов переопределяются `LOCAL_AI_STARTER_UPDATE_API` / `LOCAL_AI_STARTER_UPDATE_ZIP`.
- `check_for_update(argv)` — `local_ai_starter.py:2380`, первый шаг `main` после баннера.
  Пропускается при `--no-update`, `LOCAL_AI_STARTER_NO_UPDATE=1`, dry-run. Таймаут 5 с; любая
  ошибка (нет сети, блокировка, лимит API) — одна строка «не удалось проверить», мастер идёт дальше.
  Предлагает только строго более новый тег (`_version_tuple`, `:2187`), показывает до 15 строк
  заметок релиза. Варианты: обновить (Enter), не сейчас, пропустить версию (`skipped_version` в
  `state.json`, до следующего релиза).
- `apply_update(tag)` — `local_ai_starter.py:2408`:
  - git-клон (`APP_DIR/.git` + `git` в PATH) — `_update_git` (`:2237`): только чистое дерево,
    `git fetch --tags --force origin`, затем `git merge --ff-only refs/tags/<tag>`. Перемотка на тег,
    а не на `main`, поэтому неопубликованные коммиты не приходят. Иначе — подсказка `git pull`;
  - ZIP-папка — `_update_zip` (`:2439`): архив тега через `download()` без хеша (у архивов
    GitHub его нет), распаковка `extract()` в `local-ai/update-new/`, замена только изменённых
    файлов через временный файл и `replace()`. `local-ai/` и `.git/` пропускаются, exec-бит
    `RunMe.command`/`RunMe.sh` восстанавливается. Удалённые в релизе файлы остаются.
- `restart(argv)` — `local_ai_starter.py:2471`: запускает новый `local_ai_starter.py` с теми же
  аргументами и `--no-update` через `subprocess.call` (одинаково на всех ОС), SIGINT в родителе игнорируется.

## Collaborators
- [network](network.md) — `download`, `extract`, `http_json`; [wizard-flow](wizard-flow.md) — `main`;
  [launchers](launchers.md) — пробрасывают аргументы; [i18n](i18n.md) — ключи `update_*`.

## Known Issues
- v2.0.0 обновлятора не содержит: с неё на 2.1.0 нужно перейти один раз вручную.
- Windows: если в релизе изменился `RunMe.bat`, его замена во время работы может сбить `cmd`
  (он дочитывает .bat по смещению). Неизменённые файлы не перезаписываются, но изменение .bat
  лучше выпускать отдельно.
- Без `git` в PATH папка-клон обновляется как ZIP: файлы меняются, история git отстаёт.

## Related Pages
[release](../workflows/release.md), [test](../workflows/test.md)
