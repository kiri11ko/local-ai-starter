# Local AI Starter

English | [Русский](README.ru.md)

A wizard that installs and runs a local language model on your computer
(macOS, Linux, Windows). No cloud, no API keys, no command-line flags.

> The wizard's on-screen text is currently in Russian.

## How to run

- **macOS:** double-click `Запустить Local AI Starter.command` (the first time:
  right-click → Open, Gatekeeper asks for this).
- **Windows:** double-click `Запустить Local AI Starter.bat`.
- **Linux:** in a terminal, `./"Запустить Local AI Starter.sh"` (double-click works in
  file managers that allow running scripts).
- **Any system, manually:** `python3 local_ai_starter.py`.

Requires Python 3.9+. The wizard asks questions with ready-made options; just
press **Enter** to take the recommended one.

1. "What do you need the assistant for?" — chat and writing, or coding with OpenCode.
2. It checks memory and disk space and suggests a model, showing the download size.
3. A plan and a confirmation ("Start?").
4. It downloads the engine and the model, starts the server, sends a test
   question, then opens the chat in your browser (or prepares the OpenCode demo project).

On later runs you get a menu: start and open chat, stop the server, switch model,
OpenCode demo project, status and log, delete everything.

## What goes on disk

Everything lives in the `local-ai` folder next to the script. Nowhere else:
PATH, shell configs and global OpenCode settings are never touched.

```
local-ai/
  bin/            llama.cpp engine (pinned build, SHA-256 verified)
  models/         model weights (downloaded on first run)
  opencode-home/  OpenCode, if you did not have it
  demo-project/   demo project with opencode.json
  state.json, server.log
```

To remove everything: the "delete everything" menu item, or just delete the
`local-ai` folder. The server listens on `127.0.0.1` only.

## Models

| Profile | Model | Download | Memory |
|---|---|---|---|
| Fast | Qwen3-4B Q4_K_M | ~2.5 GB | 8 GB+ |
| General | Qwen3-8B Q4_K_M | ~5 GB | 16 GB+ |
| Coding | Qwen2.5-Coder-7B Q4_K_M, 32K context | ~4.7 GB | 16 GB+ |

These are candidates, not a performance promise. Sizes are approximate.

## Limits

- The engine is a CPU build on Windows and Linux (Metal is used on Mac). GPU
  acceleration on Windows/Linux is not configured yet.
- The wizard installs OpenCode only on macOS/Linux; on Windows install it yourself (WSL recommended).
- To check the flow without installing anything: set `LOCAL_AI_STARTER_DRY_RUN=1`.

## Manual test checklist

macOS Apple Silicon: clean start → answer → restart → stop → "delete everything".
Interrupted model download, port 8080 in use, low disk space. OpenCode branch:
does the model really call tools (editing `index.html`). Linux and Windows on real machines.

## License

MIT, see [LICENSE](LICENSE). The script downloads third-party components
(llama.cpp, Qwen models, OpenCode) under their own licenses.
