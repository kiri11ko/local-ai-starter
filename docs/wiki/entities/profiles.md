# Profiles

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Линейки моделей четырёх видов (код, картинки, видео, речь), раскладка на диске и выбор рекомендуемой по памяти.
Для кода линейка одинаковая у llama.cpp и MLX.

## Key API
- `Profile` — `local_ai_starter.py:155`: `key`, `base` (имя модели без движка → подпись
  `model.<base>` в [i18n](i18n.md)), `engine` (`gguf`/`mlx`), `family`, `repo`, `file`
  (GGUF — имя файла, MLX — закреплённый коммит репозитория), `quant`, `size`, `sha256` (только GGUF),
  `min_ram_gb`, а также `kind` (`code`/`image`/`video`/`speech`), `components`, `args`, `mac_args`, `ext`
  для медиамоделей. Свойства: `path`, `label_path`, `url` (GGUF — `resolve/main/<file>`, MLX —
  `api/models/<repo>/tree/<commit>?recursive=1`, медиа — первый компонент), `missing`, `installed`
  (GGUF — файл есть, MLX — маркер `.complete`, медиа — все компоненты на месте), `name` (часть подписи до двоеточия).
- `Component` — `local_ai_starter.py:135`: один файл многофайловой модели — `engine` (`sd`/`tts`, папка
  `models/<engine>/`), `flag` (флаг командной строки), `repo`, `rev` (закреплённый коммит), `file`, `size`,
  `sha256` (из LFS-метаданных HF). Путь плоский — `models/<engine>/<имя файла>`, поэтому общие файлы
  (`_AE`, `_UMT5`, `_TTS_CODEC`) у разных профилей лежат один раз.
- `_media` — `local_ai_starter.py:218`: размер профиля — сумма компонентов.
- `_gguf` / `_mlx` — `local_ai_starter.py:209`, `:214`. Ключи `<base>` и `<base>-mlx`.
- `_MODELS` — `local_ai_starter.py:240`, от меньшей к большей:

  | base | GGUF | MLX (mlx-community) | Память |
  |---|---|---|---|
  | `qwen3.5-4b` | unsloth Q4_K_M, 2,6 ГБ | 4-bit, 2,9 ГБ | 8 |
  | `qwen3.5-9b` | unsloth Q4_K_M, 5,3 ГБ | 4-bit, 5,6 ГБ | 16 |
  | `qwen3.8-27b` | ggml-org Q4_K_M, 17,7 ГБ | 4-bit, 15,0 ГБ | 32 |
  | `qwen3.6-35b-a3b` | ggml-org Q4_K_M, 19,0 ГБ | 4-bit, 19,0 ГБ | 48 |
  | `qwen3.6-35b-a3b-q8` | ggml-org Q8_0, 34,4 ГБ | 8-bit, 35,2 ГБ | 64 |

  Медиа (ключ = `base`, все на HF без gated-доступа, проверено 2026-11-05):

  | key | вид | файлы | ГБ | Память |
  |---|---|---|---|---|
  | `sd-turbo` | image | stabilityai `sd_turbo.safetensors` (`-m`) | 4,9 | 8 |
  | `flux-schnell` | image | leejet q4_k + ae + clip_l + t5xxl Q4_K_M | 9,7 | 16 |
  | `z-image-turbo` | image | leejet Q8_0 + ae + Qwen3-4B-Instruct-2507 Q8_0 (`--llm`) | 10,4 | 24 |
  | `wan2.1-1.3b` | video | calcuis q8_0 + wan_2.1_vae + umt5-xxl Q8_0 | 7,3 | 16 |
  | `wan2.2-5b` | video | QuantStack TI2V-5B Q8_0 + wan2.2_vae + umt5-xxl Q8_0 | 12,0 | 32 |
  | `qwen3-tts-1.7b` | speech | ggml-org Q4_K_M (`-m`) + mmproj Q8_0 (`-mm`) | 1,4 | 8 |
  | `qwen3-tts-1.7b-q8` | speech | ggml-org Q8_0 + mmproj Q8_0 | 2,1 | 16 |

  Параметры генерации (`args`) взяты из документации sd.cpp (`docs/flux.md`, `z_image.md`, `wan.md`).

- `choose_profile(kind=None)` — `local_ai_starter.py:2372`: сначала `choose_kind()` (если вид не задан),
  для кода `choose_engine()` ([wizard-flow](wizard-flow.md)), затем рекомендует самую крупную модель
  этого вида с `min_ram_gb` ≤ RAM (неизвестная RAM считается как 16). Уже скачанные помечены ✓.
  `available()` (`:2335`) убирает MLX вне Apple Silicon и sd-модели там, где нет сборки sd.cpp.
- Архитектуры GGUF — `qwen35` и `qwen35moe`; закреплённый llama.cpp b12110 их знает (проверено
  по строкам `libllama` 2026-11-04). mlx-lm 0.32.2 грузит `qwen3_5`/`qwen3_5_moe` и
  отбрасывает веса зрения.

## Collaborators
- [server-lifecycle](server-lifecycle.md) — `key` как `--alias`, `api_model()`;
  [opencode-integration](opencode-integration.md); [speed-test](speed-test.md); [sd-engine](sd-engine.md),
  [speech](speech.md) — команды по `components` и `args`; [test-cases](test-cases.md).
- Таблица моделей есть и в README: при изменении `_MODELS` обновлять `README.md` и `README.ru.md`.

## Known Issues
- Не проверено на реальной модели, какие из них надёжно вызывают инструменты OpenCode и
  как они ложатся в память с контекстом 64K.
- Удаление общего файла в «Модели на диске» (например, `ae.safetensors`) делает неустановленными
  все профили, которые его используют; при следующем запуске докачается только он.
- Ни одна медиамодель не прогонялась на реальной генерации (загрузки 1,4–12 ГБ).
- Профили версий 1–2 (`fast`, `qwen3-8b` и т. п.) больше не существуют: мастер спросит модель
  заново, а старые файлы видны в «Модели на диске».

## Related Pages
[update-models](../workflows/update-models.md), [wizard-flow](wizard-flow.md), [architecture](../architecture.md)
