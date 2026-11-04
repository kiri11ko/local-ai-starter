# Test

Автотестов нет. Проверка — синтаксис, dry-run и ручной прогон.

## Быстрые проверки

```bash
python3 -m py_compile local_ai_starter.py
LOCAL_AI_STARTER_DRY_RUN=1 LOCAL_AI_STARTER_HOME="$(mktemp -d)" python3 local_ai_starter.py
```

## Ручной чеклист (из README)

- macOS Apple Silicon: чистый старт → ответ модели → повторный запуск → остановка → «Удалить всё».
- Оборванная загрузка модели.
- Занят порт 8080 (мастер должен взять следующий, [server-lifecycle](../entities/server-lifecycle.md)).
- Мало места на диске (предупреждение в [profiles](../entities/profiles.md)).
- Ветка OpenCode: модель реально вызывает инструменты и правит `index.html`
  ([opencode-integration](../entities/opencode-integration.md)).
- Linux и Windows на реальных машинах.

Результаты прогонов фиксировать в [status](../status.md), найденные баги — в
[debugging_log](../debugging_log.md).

## Related Pages
[build](build.md)
