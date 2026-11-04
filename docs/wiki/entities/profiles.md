# Profiles

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Набор поддерживаемых моделей и выбор рекомендуемой под память и диск компьютера.

## Key API
- `Profile` — `local_ai_starter.py:58`: `key`, `title`, `purpose`, `hf_model`
  (`repo:quant` для `llama-server -hf`), `context`, `download` (строка для пользователя), `min_ram_gb`.
- `PROFILES` — `local_ai_starter.py:68`:

  | key | Модель | Контекст | Загрузка | Память |
  |---|---|---|---|---|
  | `fast` | `Qwen/Qwen3-4B-GGUF:Q4_K_M` | 8192 | ~2,5 ГБ | 8 ГБ |
  | `general` | `Qwen/Qwen3-8B-GGUF:Q4_K_M` | 8192 | ~5 ГБ | 16 ГБ |
  | `code` | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M` | 32768 | ~4,7 ГБ | 16 ГБ |

- `choose_profile(purpose_code)` — `local_ai_starter.py:472`. Рекомендация: код → `code` при RAM ≥ 16,
  иначе `fast`; чат → `general` при RAM ≥ 12, иначе `fast`. Неизвестная RAM считается как 16.
  Предупреждает, если RAM ниже `min_ram_gb` или свободно меньше 12 ГБ.
- `ram_gb()` — `local_ai_starter.py:119` (sysctl / `/proc/meminfo` / `GlobalMemoryStatusEx`),
  `free_gb()` — `local_ai_starter.py:147`.

## Collaborators
- `key` профиля — это `--alias` сервера и id модели в OpenCode:
  [server-lifecycle](server-lifecycle.md), [opencode-integration](opencode-integration.md).
- Таблица моделей продублирована в README для пользователя — при изменении `PROFILES`
  обновлять `README.md` и `README.ru.md`.

## Known Issues
- Размеры загрузки — приблизительные строки, не вычисляются.

## Related Pages
[wizard-flow](wizard-flow.md), [architecture](../architecture.md)
