# Profiles

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Линейка моделей, одинаковая для обоих движков, раскладка на диске и выбор рекомендуемой по памяти.

## Key API
- `Profile` — `local_ai_starter.py:93`: `key`, `base` (имя модели без движка → подпись
  `model.<base>` в [i18n](i18n.md)), `engine` (`gguf`/`mlx`), `family`, `repo`, `file`
  (GGUF — имя файла, MLX — закреплённый коммит репозитория), `quant`, `size`, `sha256` (только GGUF),
  `min_ram_gb`. Свойства: `path`, `label_path`, `url` (GGUF — `resolve/main/<file>`, MLX —
  `api/models/<repo>/tree/<commit>?recursive=1`), `installed` (GGUF — файл есть, MLX — маркер `.complete`).
- `_gguf` / `_mlx` — `local_ai_starter.py:125`, `:130`. Ключи `<base>` и `<base>-mlx`.
- `_MODELS` — `local_ai_starter.py:136`, от меньшей к большей:

  | base | GGUF | MLX (mlx-community) | Память |
  |---|---|---|---|
  | `qwen3.5-4b` | unsloth Q4_K_M, 2,6 ГБ | 4-bit, 2,9 ГБ | 8 |
  | `qwen3.5-9b` | unsloth Q4_K_M, 5,3 ГБ | 4-bit, 5,6 ГБ | 16 |
  | `qwen3.8-27b` | ggml-org Q4_K_M, 17,7 ГБ | 4-bit, 15,0 ГБ | 32 |
  | `qwen3.6-35b-a3b` | ggml-org Q4_K_M, 19,0 ГБ | 4-bit, 19,0 ГБ | 48 |
  | `qwen3.6-35b-a3b-q8` | ggml-org Q8_0, 34,4 ГБ | 8-bit, 35,2 ГБ | 64 |

- `choose_profile()` — `local_ai_starter.py:1387`: сначала `choose_engine()` ([wizard-flow](wizard-flow.md)),
  затем рекомендует самую крупную модель с `min_ram_gb` ≤ RAM (неизвестная RAM считается как 16).
  Уже скачанные помечены ✓.
- Архитектуры GGUF — `qwen35` и `qwen35moe`; закреплённый llama.cpp b12110 их знает (проверено
  по строкам `libllama` 2026-11-04). mlx-lm 0.32.2 грузит `qwen3_5`/`qwen3_5_moe` и
  отбрасывает веса зрения.

## Collaborators
- [server-lifecycle](server-lifecycle.md) — `key` как `--alias`, `api_model()`;
  [opencode-integration](opencode-integration.md); [speed-test](speed-test.md).
- Таблица моделей есть и в README: при изменении `_MODELS` обновлять `README.md` и `README.ru.md`.

## Known Issues
- Не проверено на реальной модели, какие из них надёжно вызывают инструменты OpenCode и
  как они ложатся в память с контекстом 64K.
- Профили версий 1–2 (`fast`, `qwen3-8b` и т. п.) больше не существуют: мастер спросит модель
  заново, а старые файлы видны в «Модели на диске».

## Related Pages
[update-models](../workflows/update-models.md), [wizard-flow](wizard-flow.md), [architecture](../architecture.md)
