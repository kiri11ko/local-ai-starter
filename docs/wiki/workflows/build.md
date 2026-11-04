# Build and run

Сборки нет: мастер — один Python-скрипт без зависимостей (Python 3.9+).

## Запуск

```bash
python3 local_ai_starter.py
```

Для пользователей — [launchers](../entities/launchers.md) (двойной клик).

## Переменные окружения

| Переменная | Где | Что делает |
|---|---|---|
| `LOCAL_AI_STARTER_DRY_RUN=1` | `local_ai_starter.py:32` | загрузки, установки и запуск сервера только печатаются как `[dry-run] …` |
| `LOCAL_AI_STARTER_HOME=<путь>` | `local_ai_starter.py:35` | папка данных вместо `local-ai/` рядом со скриптом |

Прогон сценария, не трогая настоящую установку:

```bash
LOCAL_AI_STARTER_DRY_RUN=1 LOCAL_AI_STARTER_HOME="$(mktemp -d)" python3 local_ai_starter.py
```

Особенность dry-run с меню — см. Known Issues в [wizard-flow](../entities/wizard-flow.md).

## Related Pages
[test](test.md), [architecture](../architecture.md)
