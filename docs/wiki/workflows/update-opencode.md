# Update OpenCode

Версия закреплена в `OPENCODE_VERSION` и `OPENCODE_SHA256` (`local_ai_starter.py:92-102`), см.
[opencode-integration](../entities/opencode-integration.md).

1. Найти релиз: `gh release view --repo anomalyco/opencode` (репозиторий раньше назывался `sst/opencode`).
2. Хеши шести CLI-ассетов (не `opencode-desktop-*`):
   `gh release view <ver> --repo anomalyco/opencode --json assets --jq '.assets[] | select(.name|test("^opencode-(darwin|linux|windows)-(arm64|x64)\\.(zip|tar.gz)$")) | .name + " " + .digest'`.
3. Обновить `OPENCODE_VERSION`, хеши и при заметном изменении `OPENCODE_SIZE_MB`.
4. Проверить, что в архиве по-прежнему один файл `opencode` в корне, и что
   `opencode debug config` с `opencode_env()` принимает наш `opencode.json` (см. [test](test.md)).
5. Записать версию в [log](../log.md).
