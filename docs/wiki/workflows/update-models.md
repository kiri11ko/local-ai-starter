# Update models

Линейка — `_MODELS` (`local_ai_starter.py:136`), см. [profiles](../entities/profiles.md).

## Найти кандидатов

```bash
curl -s "https://huggingface.co/api/models?author=ggml-org&search=Qwen&sort=createdAt&direction=-1&limit=20"
curl -s "https://huggingface.co/api/models?author=mlx-community&search=<Модель>-4bit&limit=10"
```

GGUF брать у `ggml-org` (команда llama.cpp) или `unsloth`, MLX — у `mlx-community`. Пара
GGUF и MLX должна быть одной и той же моделью и близкой квантизацией (Q4_K_M ↔ 4-bit,
Q8_0 ↔ 8-bit), иначе [speed-test](../entities/speed-test.md) сравнивает несравнимое.

## Закрепить

- GGUF: `size` и `lfs.oid` (это SHA-256) файла из `/api/models/<repo>/tree/main`.
- MLX: `sha` из `/api/models/<repo>` — это коммит, он идёт в поле `file`; `size` — сумма
  размеров из `/api/models/<repo>/tree/<sha>?recursive=1`.

## Проверить совместимость

- Архитектура GGUF — ключ `general.architecture` в заголовке файла (первые 256 КБ через
  `Range`). Она должна быть среди строк `libllama*.dylib` закреплённой сборки ([llama-engine](../entities/llama-engine.md)).
- MLX — `model_type` в `config.json` должен быть модулем `mlx_lm/models/<type>.py` в закреплённом
  mlx-lm ([mlx-engine](../entities/mlx-engine.md)).
- Добавить подпись `model.<base>` в оба языка ([i18n](../entities/i18n.md)) и строку в таблицы README.
