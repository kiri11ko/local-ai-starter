# SD engine (stable-diffusion.cpp)

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Движок картинок и видео: закреплённая сборка stable-diffusion.cpp, разовый запуск `sd-cli` на каждую
генерацию, сеанс «описание → файл».

## Key API
- Пины `SD_BUILD` / `SD_URL` / `SD_ASSETS` — `local_ai_starter.py:106`. Сборка `master-1050-58bb3c1`
  (2026-11-04). Ключи — `llama_platform()`: `macos-arm64` и `macos-x64` берут один и тот же архив
  (бинарники универсальные arm64 + x86_64, с Metal; проверено `lipo -info`), `ubuntu-x64`, `win-cpu-x64`.
  Linux arm64 и Windows arm64 сборок нет — там `media_supported()` (`:1272`) ложно, и в выборе вида
  картинок и видео нет. SHA-256 — из поля `digest` ассетов GitHub, совпало с локальным `shasum`.
- `install_sd()` — `local_ai_starter.py:1334`: `_install_archive` в `engines/stable-diffusion.cpp/`,
  исполняемый бит для `sd-*`. В архиве `sd-cli`, `sd-server`, `libstable-diffusion.dylib` (rpath
  `@executable_path`), лицензии. `sd_binary()` — `:1262`.
- `media_command()` — `local_ai_starter.py:1799`: `sd-cli` + пары `флаг путь` всех компонентов +
  `args` профиля с заменами из тест-кейса (`_override`) + `mac_args` на macOS + `-p`, `-o`, `--seed`.
  В сеансе seed `-1` (случайный), в тест-кейсах — фиксированный.
- `generate()` — `local_ai_starter.py:1827`: останавливает сервер модели для кода (память), пишет
  вывод в `generate.log`, меряет через `run_measured` ([test-cases](test-cases.md)), проверяет код
  выхода и наличие файла. Единицы: 1 картинка или число кадров (`--video-frames`).
- `media_session()` — `local_ai_starter.py:1873`: цикл `ask_text` → `generate` → «Открыть результат?»
  (`open_path`). Файлы — `outputs/<вид>/<дата-время>.<ext>`. Пустая строка, EOF или Ctrl+C на вводе — назад;
  Ctrl+C во время генерации останавливает её и возвращает к вводу.
- Видео: `-M vid_gen` (без него Wan не работает), 832×480, 33 кадра, `--flow-shift 3.0`,
  `--cfg-scale 6.0`, 20 шагов, отрицательный промпт на английском. Вывод `.webm` — сборка поддерживает
  `.avi`, `.webm` и анимированный `.webp` (строки бинарника), ffmpeg не нужен.

## Collaborators
- [profiles](profiles.md) — компоненты и `args`; [network](network.md) — `download`, `_install_archive`;
  [wizard-flow](wizard-flow.md) — `launch`, `ensure_installed`, `engine_task("sd")`;
  [test-cases](test-cases.md).

## Known Issues
- На Metal VAE Flux даёт NaN, и картинка выходит белой без ошибки в журнале (опыт пользователя со
  своей сборкой sd.cpp, `~/.claude/commands/img.md`). Поэтому у Flux и Z-Image (тот же VAE `ae`)
  `--backend vae=cpu` на macOS; старый флаг `--vae-on-cpu` в этой сборке помечен deprecated. Признак
  сбоя — PNG около 17 КБ.
- Ни одной реальной генерации не делалось: проверены только dry-run, хэш и состав архива для macOS.
  Запуск скачанного `sd-cli --help` в сессии был заблокирован, справка прочитана через `strings`.
- Каждая генерация заново грузит модель (секунды-минуты). `sd-server` есть в архиве, но не используется.
- На Windows/Linux CPU-сборка: картинки медленные, видео — очень. Vulkan/CUDA-сборки есть в релизе.

## Related Pages
[speech](speech.md), [update-sd-build](../workflows/update-sd-build.md), [architecture](../architecture.md)
