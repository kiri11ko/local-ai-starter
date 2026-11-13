# Release

Пользователи получают только опубликованные релизы ([updater](../entities/updater.md)).

1. Поднять `VERSION` в `local_ai_starter.py:42` (семантическая версия, без `v`).
2. Обновить README/Wiki, закоммитить, `git push origin main`.
3. Подготовить заметки релиза (en + ru, нейтрально, без внутренних подробностей): их увидит
   пользователь в окне обновления, показываются первые 15 строк. **Показать пользователю и
   дождаться подтверждения.**
4. `gh release create vX.Y.Z --repo kiri11ko/local-ai-starter --target main --title "Local AI Starter vX.Y.Z" --notes-file <файл>`.
5. Проверка: копия проекта без `.git` с `VERSION` ниже нового → запуск → предлагает новую версию
   с настоящими заметками → обновление → перезапуск на новой ([test](test.md)).

   Рабочий рецепт (проверен 2026-11-13 на v2.4.0):

   ```bash
   tmp=$(mktemp -d); mkdir -p "$tmp/app" "$tmp/data"
   rsync -a --exclude .git --exclude local-ai --exclude .promts \
         --exclude test-cases --exclude docs --exclude .gitignore ./ "$tmp/app/"
   sed -i '' 's/VERSION = "2.4.0"/VERSION = "2.3.9"/' "$tmp/app/local_ai_starter.py"  # минус один патч
   printf '1\n1\n' | LOCAL_AI_STARTER_LANG=en LOCAL_AI_STARTER_HOME="$tmp/data" \
         python3 "$tmp/app/local_ai_starter.py" --menu
   ```

   Ожидаемый результат: предложение новой версии с заметками en+ru (первые 15 строк) →
   «Update now» → скачивание архива (сотни КБ, без моделей) → «Updated to …» →
   перезапуск с баннером новой версии → меню → «1» (Stop the server and exit), код 0.

   Грабли: `LOCAL_AI_STARTER_DRY_RUN=1` отключает проверку обновлений — для этого теста
   нужен реальный запуск; после перезапуска с пустым `HOME` поток уходит в `choose_kind()`,
   у которого нет выхода — запуск с `--menu` ведёт сразу в меню управления с «Stop and exit».

6. Записать версию и коммит в [log](../log.md) и [status](../status.md).

История:
- `v2.0.0` — `f473427` (без обновлятора).
- `v2.1.0` — `ca3f133`, 2026-11-04: MLX, новая линейка Qwen, замер скорости, обновление при запуске.
- `v2.2.0` — `30dc02e`, 2026-11-05: стартовое меню, картинки/видео/речь, тест-кейсы.
- `v2.3.0` — `674c572`, 2026-11-12: команда `local-opencode`, отправка результатов тестов.
- `v2.4.0` — `7df43c7`, 2026-11-13: перенос настроек AI-агентов, автотесты, устойчивая проверка обновлений.

`gh release create --target` принимает ветку или полный хеш коммита. Сокращённый хеш даёт
`HTTP 422: tag_name is not a valid tag`.
