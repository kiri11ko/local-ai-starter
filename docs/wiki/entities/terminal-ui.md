# Terminal UI

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Меню со стрелками и оформление вывода без сторонних библиотек, на всех трёх ОС.

## Key API
- `_enable_ansi()` — `local_ai_starter.py:861`. На Windows включает
  `ENABLE_VIRTUAL_TERMINAL_PROCESSING` через `SetConsoleMode`. `ANSI`, `COLOR` (учитывает
  `NO_COLOR`), `INTERACTIVE` (ANSI и stdin — TTY).
- `ask(question, options, default)` — `local_ai_starter.py:1016`. Возвращает номер с 1;
  EOF/Ctrl+C → `Cancelled`. При `INTERACTIVE` — `_ask_arrows`, иначе `_ask_numbers`.
- `_ask_arrows` — `local_ai_starter.py:957`. ↑/↓ двигают выделение (`›`, жирный циан), цифра
  выбирает сразу, Enter подтверждает. Перерисовка на месте через `ESC[nF`, курсор скрыт;
  терминал восстанавливается в `finally`.
- Клавиши: `_read_key_posix` (`termios` + `tty.setcbreak`, ESC-последовательности с
  `select` 50 мс) — `local_ai_starter.py:818`; `_read_key_windows` (`msvcrt.getwch`,
  префиксы `\x00`/`\xe0`) — `local_ai_starter.py:836`.
- Оформление: `banner`, `step`, `ok`/`fail` (✓/✗), `bold`/`dim` — `local_ai_starter.py:783-543`.
- Полоса прогресса `_progress` — `local_ai_starter.py:1205` (см. [network](network.md)).

## Collaborators
- [i18n](i18n.md) — все подписи через `t()`.
- [wizard-flow](wizard-flow.md) — все вопросы.

## Known Issues
- Меню со стрелками на Windows и Linux не проверено на реальных машинах.
- Если варианты не помещаются по ширине и переносятся, перерисовка через `ESC[nF` съедет.

## Related Pages
[test](../workflows/test.md)
