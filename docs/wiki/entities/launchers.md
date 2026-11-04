# Launchers

Source: [`RunMe.command`](../../../RunMe.command), [`RunMe.sh`](../../../RunMe.sh),
[`RunMe.bat`](../../../RunMe.bat)

## Purpose
Запуск двойным кликом без терминала. Логики мастера в них нет.

## Key API
- `RunMe.command` (macOS) и `RunMe.sh` (Linux): переходят в папку скрипта, проверяют `python3`,
  запускают мастер с аргументами (`"$@"`), при ненулевом коде ждут Enter.
- `RunMe.bat` (Windows, CRLF): `chcp 65001`, ищет `py -3`, затем `python`, передаёт `%*`, в конце `pause`.
- Тексты только на английском: они выводятся до Python, когда [i18n](i18n.md) ещё недоступна.

## Collaborators
- [wizard-flow](wizard-flow.md) — `main(argv)`, флаг `--menu`.

## Known Issues
- На macOS первый запуск `.command` требует «правый клик → Открыть» (Gatekeeper).
- `.command` и `.sh` должны оставаться исполняемыми в git (режим 100755).

## Related Pages
[build](../workflows/build.md)
