# Update stable-diffusion.cpp build

Как поднять закреплённую сборку sd.cpp ([sd-engine](../entities/sd-engine.md)).

1. Выбрать релиз: `gh release list -R leejet/stable-diffusion.cpp -L 10`. Теги вида
   `master-<n>-<commit>`, выходят по нескольку в день.
2. Имена и хэши ассетов: `gh release view <tag> -R leejet/stable-diffusion.cpp --json assets -q
   '.assets[] | "\(.name) \(.digest)"'`. Нужны: `…-bin-Darwin-macOS-<ver>-arm64.zip` (универсальный,
   идёт и в `macos-x64`), `…-bin-Linux-Ubuntu-<ver>-x86_64.zip`, `…-bin-win-cpu-x64.zip`. Имя
   macOS-ассета содержит версию macOS сборщика и меняется.
3. Обновить `SD_BUILD` и `SD_ASSETS` (`local_ai_starter.py:106`).
4. Скачать macOS-архив, сверить `shasum -a 256`, проверить состав (`unzip -l`: `sd-cli`, библиотека),
   `lipo -info sd-cli`, и что флаги профилей ещё существуют: `strings sd-cli | grep -E '^--'`
   (`--backend`, `--video-frames`, `--flow-shift`, `--llm`, `-M`).
5. Если флаги поменялись — поправить `args`/`mac_args` профилей ([profiles](../entities/profiles.md))
   по `docs/*.md` репозитория sd.cpp.
6. Dry-run генерации, затем одна реальная картинка (предупредить пользователя о загрузке).
