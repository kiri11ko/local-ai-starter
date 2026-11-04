# Profiles

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Поддерживаемые модели, их раскладка на диске и выбор рекомендуемой по памяти.

## Key API
- `Profile` — `local_ai_starter.py:79`: `key`, `family`, `repo`, `file`, `size` (байты),
  `sha256`, `min_ram_gb`. Свойства `path` = `models/<family>/<file>` и `url` =
  `https://huggingface.co/<repo>/resolve/main/<file>`.
- `PROFILES` — `local_ai_starter.py:97`:

  | key | Файл | Размер | Память |
  |---|---|---|---|
  | `qwen3-8b` | `qwen/Qwen3-8B-Q4_K_M.gguf` | 4,7 ГБ | 12 ГБ |
  | `qwen3-4b` | `qwen/Qwen3-4B-Q4_K_M.gguf` | 2,3 ГБ | 8 ГБ |
  | `qwen2.5-coder-7b` | `qwen/qwen2.5-coder-7b-instruct-q4_k_m.gguf` | 4,4 ГБ | 12 ГБ |

- `choose_profile()` — `local_ai_starter.py:1096`: рекомендует `qwen3-8b` при RAM ≥ 12 ГБ
  (неизвестная RAM считается как 16), иначе `qwen3-4b`. Уже скачанные помечаются ✓.
- SHA-256 и размеры взяты из LFS-метаданных Hugging Face: `/api/models/<repo>/tree/main`.
- Новое семейство (например, gemma) — ещё один `Profile` со своим `family` и ключом
  `model.<key>` в обоих языках [i18n](i18n.md).

## Collaborators
- `key` — это `--alias` сервера и id модели в OpenCode ([server-lifecycle](server-lifecycle.md),
  [opencode-integration](opencode-integration.md)).
- Таблица моделей есть и в README: при изменении `PROFILES` обновить `README.md` и `README.ru.md`.

## Known Issues
- Не проверено на реальной модели, какая из трёх лучше вызывает инструменты OpenCode.
  `qwen3-8b` рекомендована, потому что у Qwen3 tool calling через `--jinja` надёжнее,
  чем у Qwen2.5-Coder.
- Профили из версии 1 (`fast`/`general`/`code`) не распознаются: мастер просто спросит модель заново.

## Related Pages
[wizard-flow](wizard-flow.md), [architecture](../architecture.md)
