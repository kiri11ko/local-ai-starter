# Local AI Starter

English | [Русский](README.ru.md)

One double-click and you get a local AI coding assistant: the wizard downloads the
llama.cpp engine, a Qwen model and OpenCode, starts the model on your computer and
opens OpenCode right in the terminal, ready for your requests. macOS, Linux, Windows.
No cloud, no API keys, no command-line flags.

The wizard speaks English, or Russian if your system language is Russian.

## How to run

- **macOS:** double-click `RunMe.command` (the first time: right-click → Open,
  Gatekeeper asks for this).
- **Windows:** double-click `RunMe.bat`.
- **Linux:** `./RunMe.sh` in a terminal (double-click works in file managers that
  allow running scripts).
- **Any system, manually:** `python3 local_ai_starter.py`.

Requires Python 3.9+. Pick options with the **↑/↓** arrows (or type a number) and
press **Enter**. Enter alone takes the recommended option.

1. It checks memory and disk space. On Apple Silicon it asks which engine to use
   (llama.cpp or MLX), then suggests the largest model that fits your memory.
2. A plan with download sizes, and one confirmation ("Start?").
3. It checks that GitHub and Hugging Face are reachable from your network, then
   downloads the engine, the model and OpenCode, starts the server and asks a test question.
4. OpenCode opens in the `local-ai/workspace` folder. Type a request, for example
   "Change the heading in index.html and add a dark theme toggle".

When you quit OpenCode (`/exit`), a menu appears: stop the server, keep it running,
go back to OpenCode, switch model or engine, speed test, web chat in the browser
(llama.cpp only), models on disk, status and log, delete everything. Later runs go straight to OpenCode. `RunMe --menu`
(or `python3 local_ai_starter.py --menu`) opens the menu only.

## Blocked or slow networks

Before downloading, the wizard asks each server for its first byte and waits up to
15 seconds. If a server does not answer, it says which one, why (timeout, DNS,
refused connection, TLS interception, HTTP error) and what to try: another network,
a VPN, or a proxy via `HTTPS_PROXY`. If a download stalls for 30 seconds, it retries
and resumes where it stopped. Everything already downloaded is kept for the next run.

## What goes on disk

Everything lives in the `local-ai` folder next to the script. Nowhere else:
PATH, shell configs and your global OpenCode settings are never touched.

```
local-ai/
  engines/
    llama.cpp/    llama.cpp engine (pinned build, SHA-256 verified)
    mlx/          MLX runtime on Apple Silicon: uv, its own Python 3.12, mlx-lm
  models/
    gguf/qwen/    GGUF models for llama.cpp, one file each
    mlx/qwen/     MLX models, one folder each
  opencode/       OpenCode CLI (pinned version, SHA-256 verified)
  opencode-home/  OpenCode's own data, sessions and caches
  opencode.json   OpenCode settings: the local model only
  workspace/      the folder OpenCode works in
  benchmarks.csv  speed-test results
  state.json, server.log
```

The two engines and their models never overwrite each other. To remove one model:
menu → "Models on disk" (unfinished downloads are marked there too). To remove
everything: menu → "Delete everything", or just delete the `local-ai` folder. The
server listens on `127.0.0.1` only.

## Models

The same line-up exists for both engines, so they can be compared on the same model.
The wizard recommends the largest one that fits your memory.

| Model | GGUF (llama.cpp) | MLX | Memory |
|---|---|---|---|
| Qwen3.5 4B | Q4_K_M, 2.6 GB | 4-bit, 2.9 GB | 8 GB |
| Qwen3.5 9B | Q4_K_M, 5.3 GB | 4-bit, 5.6 GB | 16 GB |
| Qwen3.8 27B | Q4_K_M, 17.7 GB | 4-bit, 15.0 GB | 32 GB |
| Qwen3.6 35B-A3B (MoE, fast) | Q4_K_M, 19.0 GB | 4-bit, 19.0 GB | 48 GB |
| Qwen3.6 35B-A3B, 8-bit | Q8_0, 34.4 GB | 8-bit, 35.2 GB | 64 GB |

Context is 32K tokens: 16K below 12 GB of memory, 64K from 48 GB. OpenCode's
instructions alone take about 10K. These are candidates, not a performance promise.

## llama.cpp or MLX

On Apple Silicon both run on the GPU: llama.cpp through Metal, MLX natively. MLX is
often faster on Macs. llama.cpp works on every system and has more mature tool
calling, which OpenCode depends on. To compare them on your machine:

1. Menu → "Switch model or engine", pick an engine and a model.
2. Menu → "Speed test". It measures prompt reading (a ~4K-token prompt) and answer
   generation (~300 tokens), and appends a line to `local-ai/benchmarks.csv`.
3. Repeat with the other engine and the same model, then compare. Also try a real
   task in OpenCode: speed is not everything if tool calls fail.

## Settings

| Variable | What it does |
|---|---|
| `LOCAL_AI_STARTER_LANG=en\|ru` | force the wizard language |
| `LOCAL_AI_STARTER_HOME=<path>` | keep data somewhere other than `local-ai/` |
| `LOCAL_AI_STARTER_DRY_RUN=1` | walk through the flow without downloading or starting anything |
| `HTTPS_PROXY` | standard proxy setting, honoured for all downloads |

## Limits

- The engine is a CPU build on Windows and Linux (Metal is used on Mac). GPU
  acceleration on Windows/Linux is not configured yet.
- Small local models are much weaker than cloud ones: expect simple edits, not big refactors.

## Manual test checklist

macOS Apple Silicon, both engines: clean start → OpenCode edits `index.html` → `/exit` →
menu → speed test → switch engine → restart → stop → "Delete everything". Interrupted model download (resume), blocked
host (message), port 8080 in use, low disk space. Linux and Windows on real machines.

## License

MIT, see [LICENSE](LICENSE). The script downloads third-party components
(llama.cpp, MLX and mlx-lm, uv, Qwen models, OpenCode) under their own licenses.
