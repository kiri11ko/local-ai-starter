# Transfer

## Purpose

Разовый перенос настроек между AI-агентами (Claude Code, Codex, OpenCode) из меню управления:
файлы инструкций (`CLAUDE.md` ↔ `AGENTS.md`), файлы скиллов и простые Markdown-команды.
Пункт «Transfer AI agent settings» в `menu()` (`local_ai_starter.py:3026`), строки
`transfer.*` в [i18n](i18n.md) (`:756` en, `:782` ru). Только файлы: настройки, MCP, хуки,
ключи и история сознательно не переносятся — эквиваленты не выводятся никогда.

## Key API

- `transfer_home(agent, local=False)` — `local_ai_starter.py:2842`. Папка агента: Claude —
  `CLAUDE_CONFIG_DIR`/`~/.claude`, Codex — `CODEX_HOME`/`~/.codex`, OpenCode —
  `XDG_CONFIG_HOME/opencode`, при `local=True` — изолированный `OPENCODE_HOME/config`
  ([opencode-integration](opencode-integration.md)).
- `transfer_safe(path)` — `:2851`. Запрет симлинков: путь и все родители не могут быть ссылками
  (защита от записи наружу через подменённый каталог).
- `transfer_files(folder)` — `:2856`. Обход дерева без перехода по симлинкам, в детерминированном
  порядке (сортировка на каждом уровне).
- `transfer_plan(source, targets, projects, include_global, source_local=False)` — `:2867`.
  Read-only план пар (источник, приёмник). Инструкции: `CLAUDE.md` → `AGENTS.md`; у Codex
  источником служит `AGENTS.override.md`, а запись в Codex пропускается, если override существует
  (Codex игнорирует `AGENTS.md` при наличии override). Скиллы: глобальные Codex —
  `~/.agents/skills`, остальные — `<папка агента>/skills`; проектные — `.claude`, `.agents`,
  `.opencode` (команды Codex — `.codex/commands`). Команды — только между не-Codex парами,
  только `.md`, без frontmatter (`---` в начале) и без shell-подстановки `` !` `` — метаданные
  и подстановки тул-специфичны, молчаливая конвертация запрещена.
- `transfer_apply(plan)` — `:2911`. Копирование с `xb` (эксклюзивное создание): существующие
  файлы никогда не перезаписываются, считаются `skipped`; `shutil.copymode` переносит права.
  При `DRY_RUN` запись не выполняется, только счётчики.
- `transfer_settings()` — `:2934`. Диалог: источник → получатели (второй агент / оба) →
  вариант OpenCode (пользовательский / изолированный / оба) → область (глобально / один проект /
  непосредственные подпапки папки проектов / всё) → превью первых 40 операций и число остальных →
  предупреждение о границах переноса → подтверждение → отчёт «скопировано/пропущено».
  Вложенные проекты не сканируются.

## Collaborators

- [wizard-flow](wizard-flow.md) — пункт меню `transfer`; [terminal-ui](terminal-ui.md) — `ask`;
  [i18n](i18n.md) — строки `transfer.*`; [launchers](launchers.md) — не участвует.

## Known Issues

- Существующие файлы не обновляются (`xb`): повторный перенос после изменения источника
  пропустит всё уже скопированное. Проверено 2026-11-13: при реальном прогоне Claude → Codex +
  OpenCode устаревший `~/.codex/AGENTS.md` (от 2026-05-30) остался нетронутым — для обновления
  файл нужно удалить вручную и перегнать.
- Переносятся только файлы инструкций, скиллов и простые команды. Команды с frontmatter или
  shell-подстановкой (например, `release.md`, `wiki.md` из Claude Code) пропускаются — это
  видно в превью как SKIP.
- Codex slash-команды не переносятся ни в каком направлении; project-level команды Codex живут
  в `.codex/commands`, глобальных команд для Codex в этой фиче нет.
- Поведение перенесённых инструкций не гарантируется: ссылки на `~/.claude`, пути и имена
  инструментов остаются как в исходнике — нужен ручной просмотр (текст `transfer.warning`).
- Проектная область берёт только непосредственные подпапки указанной папки.

## Related Pages

[wizard-flow](wizard-flow.md), [i18n](i18n.md), [terminal-ui](terminal-ui.md),
[opencode-integration](opencode-integration.md), [test](../workflows/test.md)
