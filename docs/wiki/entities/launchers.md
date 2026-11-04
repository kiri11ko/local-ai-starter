# Launchers

Source: [`Запустить Local AI Starter.command`](../../../Запустить%20Local%20AI%20Starter.command),
[`.sh`](../../../Запустить%20Local%20AI%20Starter.sh), [`.bat`](../../../Запустить%20Local%20AI%20Starter.bat)

## Purpose
Запуск двойным кликом без терминала. Логики мастера в них нет.

## Key API
- `.command` (macOS) и `.sh` (Linux): переходят в папку скрипта, проверяют `python3`,
  запускают мастер; при ненулевом коде ждут Enter, чтобы окно не закрылось.
- `.bat` (Windows): `chcp 65001` для кириллицы, ищет `py -3`, затем `python`, в конце `pause`.

## Collaborators
- [wizard-flow](wizard-flow.md) — `main()` и коды возврата.

## Known Issues
- На macOS первый запуск `.command` требует «правый клик → Открыть» (Gatekeeper).
- `.command` и `.sh` должны оставаться исполняемыми (`chmod +x`) в git.

## Related Pages
[build](../workflows/build.md)
