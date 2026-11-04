# Update llama.cpp build

Сборка закреплена в `LLAMA_BUILD` и `LLAMA_SHA256` (`local_ai_starter.py:70-80`), см.
[llama-engine](../entities/llama-engine.md).

1. Выбрать релиз на https://github.com/ggml-org/llama.cpp/releases.
2. Взять хеши всех шести ассетов: `gh release view <build> --repo ggml-org/llama.cpp --json assets --jq '.assets[] | .name + " " + .digest'`.
   Имена: `llama-<build>-bin-{macos-arm64,macos-x64,ubuntu-x64,ubuntu-arm64}.tar.gz`,
   `llama-<build>-bin-{win-cpu-x64,win-cpu-arm64}.zip`.
3. Обновить `LLAMA_BUILD` и все хеши.
4. Скачать архив своей платформы, распаковать через `install_llama()` (см. [test](test.md)) и
   проверить `llama-server --help` на флаги `-m`, `--alias`, `-fa on`, `-ctk`, `-ctv`, `--jinja`
   ([server-lifecycle](../entities/server-lifecycle.md)).
5. Пройти ручной чеклист и записать номер сборки в [status](../status.md) и [log](../log.md).

Существующие установки не обновятся сами: `install_llama` вызывается, только если
`engines/llama.cpp/llama-server` нет ([wizard-flow](../entities/wizard-flow.md), `ensure_installed`).
