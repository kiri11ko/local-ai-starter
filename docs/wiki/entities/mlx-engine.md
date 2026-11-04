# mlx-engine

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Второй движок на Apple Silicon: `mlx_lm.server` на моделях MLX. Нужен, чтобы сравнить его с
llama.cpp на одной и той же модели.

## Key API
- Закрепления — `local_ai_starter.py:69-76`: `UV_VERSION` 0.13.1 + `UV_SHA256` (только
  `aarch64-apple-darwin`), `MLX_PYTHON` 3.12, `MLX_LM_VERSION` 0.32.2. mlx-lm требует
  Python ≥ 3.11, а системный `python3` на macOS — 3.9, поэтому Python ставит uv.
- `install_mlx()` — `local_ai_starter.py:993`. Скачивает uv (SHA-256), затем
  `uv venv engines/mlx/venv --python 3.12 --clear` и `uv pip install mlx-lm==0.32.2`. В конце
  пишет маркер `.installed` с версией.
- `uv_env()` — `local_ai_starter.py:987`: `UV_PYTHON_INSTALL_DIR`, `UV_CACHE_DIR` внутри
  `engines/mlx/`, `UV_PYTHON_PREFERENCE=only-managed`, `UV_NO_CONFIG=1`. Проверено с
  подменённым `HOME`: в него ничего не пишется.
- `mlx_installed()` — `local_ai_starter.py:942`: маркер совпадает с `MLX_LM_VERSION`.
  При смене версии мастер переустановит среду.
- `mlx_files()` / `install_model()` — `local_ai_starter.py:1024`, `:1034`. Список файлов
  репозитория берётся на закреплённом коммите; `.gitattributes` и `README.md` пропускаются.
  LFS-файлы проверяются по SHA-256, мелкие JSON — без хеша. Уже скачанные файлы нужного
  размера пропускаются. В конце пишется маркер `.complete`.
- Запуск — `server_command()` (`local_ai_starter.py:1095`):
  `python -m mlx_lm.server --model <папка> --host 127.0.0.1 --port <p> --max-tokens 8192`,
  с `HF_HOME` внутри `engines/mlx/` и `HF_HUB_OFFLINE=1`.
- Имя модели в API — `default_model` (`api_model()`, `local_ai_starter.py:1090`). Любое
  другое имя `mlx_lm.server` пытается загрузить как новую модель.

## Collaborators
- [network](network.md) — загрузки; [server-lifecycle](server-lifecycle.md) — запуск и `/health`
  (200/503); [speed-test](speed-test.md); [wizard-flow](wizard-flow.md) — `choose_engine`.

## Known Issues
- Python-зависимости mlx-lm (34 пакета на 2026-11-04) разрешаются при установке и не
  закреплены хешами.
- Полная установка (~300 МБ) и запуск сервера на реальной модели не проверялись. Проверены
  uv, `uv venv` (CPython 3.12.15) и `uv pip install --dry-run`.
- У mlx-lm нет веб-чата и ограничения контекста: KV-кэш растёт по мере диалога.
- Вызов инструментов работает, только если у токенайзера модели есть парсер
  (`tokenizer.has_tool_calling`). Иначе сервер отвечает ошибкой на запрос с `tools`.

## Related Pages
[llama-engine](llama-engine.md), [architecture](../architecture.md)
