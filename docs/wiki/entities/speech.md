# Speech (llama-tts)

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Озвучка текста: `llama-tts` из уже закреплённой сборки llama.cpp и модель Qwen3-TTS 1.7B.

## Key API
- Движок `tts`: `tts_binary()` — `local_ai_starter.py:1267`, `engine_installed("tts")` проверяет
  `engines/llama.cpp/llama-tts`. Отдельной загрузки нет: `engine_task("tts")` — тот же архив llama.cpp
  ([llama-engine](llama-engine.md)). `llama-tts` есть в b12110 для macOS, Linux и Windows (проверено по
  составу архивов 2026-11-05).
- Профили `qwen3-tts-1.7b` (Q4_K_M) и `qwen3-tts-1.7b-q8` — `ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF`:
  модель (`-m`) и общий mmproj Q8_0 (`-mm`, кодек), `models/tts/`.
- `media_command()` — `local_ai_starter.py:1910`: `-p <текст> --tts-lang <ru|en> --output <wav>`;
  язык — из тест-кейса (`lang:`) или по наличию кириллицы (`has_cyrillic`, без кириллицы в коде).
  Если в `local-ai/voices/` есть `.wav`/`.mp3`, первый передаётся как `--tts-speaker-file`
  (`speaker_file()`, `:1784`).
- Длительность звука — `wav_seconds()` (stdlib `wave`); в тест-кейсах `s_per_unit` = секунды работы
  на секунду звука (RTF, меньше 1 — быстрее реального времени).

## Collaborators
[sd-engine](sd-engine.md) — общий `generate`/`media_session`; [profiles](profiles.md); [test-cases](test-cases.md).

## Known Issues
- README llama.cpp: без образца голоса качество Qwen3-TTS Base может быть хуже. Образец не поставляется;
  мастер подсказывает положить свой в `voices/`.
- В планах был OuteTTS; заменён на Qwen3-TTS, потому что `llama-tts` в b12110 переписан под Qwen3-TTS,
  Pocket TTS, Soprano и LFM3-Audio, а русский из них поддерживает только Qwen3-TTS.
- Реальный синтез не проверялся (загрузка 1,4 ГБ).

## Related Pages
[llama-engine](llama-engine.md), [architecture](../architecture.md)
