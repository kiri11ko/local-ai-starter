# Update llama.cpp build

Сборка закреплена в `LLAMA_BUILD` и `LLAMA_SHA256` (`local_ai_starter.py:44-53`), см.
[llama-engine](../entities/llama-engine.md).

1. Выбрать релиз на https://github.com/ggml-org/llama.cpp/releases.
2. Проверить, что для всех шести ключей есть архивы с теми же именами:
   `llama-<build>-bin-{macos-arm64,macos-x64,ubuntu-x64,ubuntu-arm64}.tar.gz`,
   `llama-<build>-bin-{win-cpu-x64,win-cpu-arm64}.zip`.
3. Обновить `LLAMA_BUILD` и все шесть хешей (со страницы релиза или `shasum -a 256` по скачанным архивам).
4. Убедиться, что в архиве по-прежнему есть `llama-server` и он поддерживает флаги
   `-hf`, `--alias`, `--jinja` ([server-lifecycle](../entities/server-lifecycle.md)).
5. Пройти ручной чеклист [test](test.md) и обновить номер сборки в [status](../status.md) и [log](../log.md).

Существующие установки не обновятся сами: `install_llama` пропускается, если `bin/llama-server`
уже есть (`local_ai_starter.py:285`).
