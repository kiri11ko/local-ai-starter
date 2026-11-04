# Build and run

Сборки нет: мастер — один Python-скрипт без зависимостей (Python 3.9+; системный `python3`
на машине разработки — как раз 3.9.6).

## Запуск

```bash
./RunMe.sh            # или python3 local_ai_starter.py
./RunMe.sh --menu     # только меню управления
```

Для пользователей — [launchers](../entities/launchers.md) (двойной клик).

## Переменные окружения

| Переменная | Что делает |
|---|---|
| `LOCAL_AI_STARTER_DRY_RUN=1` | загрузки, установки и запуски только печатаются как `[dry-run] …` |
| `LOCAL_AI_STARTER_HOME=<путь>` | папка данных вместо `local-ai/` рядом со скриптом |
| `LOCAL_AI_STARTER_LANG=en\|ru` | язык интерфейса ([i18n](../entities/i18n.md)) |
| `HTTPS_PROXY` | прокси для всех загрузок (стандарт `urllib`) |
| `NO_COLOR` | без цветов ([terminal-ui](../entities/terminal-ui.md)) |

Прогон сценария, не трогая настоящую установку:

```bash
LOCAL_AI_STARTER_DRY_RUN=1 LOCAL_AI_STARTER_HOME="$(mktemp -d)" LOCAL_AI_STARTER_LANG=en ./RunMe.sh
```

## Related Pages
[test](test.md), [architecture](../architecture.md)
