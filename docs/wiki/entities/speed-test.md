# Speed test

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Пункт меню «Замер скорости»: одинаковые замеры на llama.cpp и MLX, чтобы пользователь сравнил
движки на своём Mac и прислал отзыв.

## Key API
- `speed_test(profile)` — `local_ai_starter.py:1614`. Поднимает сервер профиля, делает прогрев,
  затем два запроса:
  - длинный запрос (список из 1499 чисел, ~4K токенов, `max_tokens` 16): чтение запроса,
    токены/с = `prompt_tokens / TTFT`;
  - рассказ на ~200 слов (`max_tokens` 300): генерация, токены/с = `(answer_tokens − 1) / время после первого токена`.
- `_stream_completion()` — `local_ai_starter.py:1574`. SSE со `stream_options.include_usage`;
  текстом считаются дельты `content`, `reasoning_content` (llama.cpp) и `reasoning` (MLX). Если
  сервер не прислал `usage`, считаются чанки.
- Результат дописывается строкой в `local-ai/benchmarks.csv`: `date, engine, model, chip, ram_gb,
  context, prompt_tokens, first_token_s, prefill_tok_s, answer_tokens, generation_tok_s`.
  `chip_name()` — `local_ai_starter.py:1604`.

## Collaborators
- [server-lifecycle](server-lifecycle.md) — `bring_up`, `model_id`; [wizard-flow](wizard-flow.md) — меню.

## Known Issues
- Разбор потока проверен на поддельном сервере в двух форматах, на настоящих движках — ещё нет.
- `temperature` 0 и рассуждения: у моделей с thinking часть ответа уходит в рассуждения;
  они тоже считаются, это честно для скорости, но не для «полезных» токенов.

## Related Pages
[mlx-engine](mlx-engine.md), [llama-engine](llama-engine.md), [test](../workflows/test.md)
