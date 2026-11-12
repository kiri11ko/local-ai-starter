# Local AI Starter

English | [Русский](README.ru.md)

One double-click and you get local AI on your own computer: a coding assistant
(llama.cpp or MLX, a Qwen model and OpenCode in the terminal), image and video generation
(stable-diffusion.cpp) and text-to-speech (llama.cpp). The wizard downloads what is needed
and runs it. A set of test cases compares the downloaded models on the same tasks.
macOS, Linux, Windows. No cloud, no API keys, no command-line flags.

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

1. It checks memory and disk space and asks what you want to do: code, images, video
   or speech. For code on Apple Silicon it also asks which engine to use (llama.cpp or
   MLX). Then it suggests the largest model that fits your memory.
2. A plan with download sizes, and one confirmation ("Start?").
3. It checks that GitHub and Hugging Face are reachable from your network, then
   downloads the engine, the model and OpenCode, starts the server and asks a test question.
4. For code, OpenCode opens in the `local-ai/workspace` folder. Type a request, for example
   "Change the heading in index.html and add a dark theme toggle". For images, video and
   speech you type a description (or the text to read), the file lands in `local-ai/outputs/`
   and the wizard offers to open it. An empty line goes back.

Every later run starts with a menu: each downloaded configuration is a line of its own
("Start: Code · Qwen3.5 9B · llama.cpp", "Start: Images · Flux.1 schnell", …, the last
used one first), then "Download a new configuration", "Test cases" and the management menu.

When you quit OpenCode (`/exit`) or a generation session, the management menu appears:
stop the server, keep it running, go back, another configuration, test cases, speed
test, web chat in the browser (llama.cpp only), models on disk, status and log, delete
everything. `RunMe --menu` (or `python3 local_ai_starter.py --menu`) opens this menu only.

### OpenCode in your own project

The menu item "Command for OpenCode in any folder" creates a `local-opencode` command (a small
launcher in `local-ai/bin/`) and, if you agree, links it into `~/.local/bin` (Windows:
`%LOCALAPPDATA%\Microsoft\WindowsApps`). Then, in any terminal folder:

```
cd ~/my-project
local-opencode          # starts the server with the last used model, opens OpenCode here
local-opencode --stop   # stops the model server
```

OpenCode keeps using the isolated settings from `local-ai/`, your own OpenCode setup is not touched,
and nothing is written into the project folder by the wizard. When you quit OpenCode, it asks
whether to keep the server running. "Delete everything" also removes the command from `~/.local/bin`.

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
    llama.cpp/    llama.cpp engine (pinned build, SHA-256 verified), also llama-tts for speech
    mlx/          MLX runtime on Apple Silicon: uv, its own Python 3.12, mlx-lm
    stable-diffusion.cpp/  image and video engine (pinned build, SHA-256 verified)
  models/
    gguf/qwen/    GGUF models for llama.cpp, one file each
    mlx/qwen/     MLX models, one folder each
    sd/           image and video model files; shared ones (VAE, text encoders) are stored once
    tts/          speech model files
  opencode/       OpenCode CLI (pinned version, SHA-256 verified)
  opencode-home/  OpenCode's own data, sessions and caches
  opencode.json   OpenCode settings: the local model only
  workspace/      the folder OpenCode works in
  outputs/        images, videos and speech you generated
  voices/         optional: put a voice sample here (see Speech)
  test-runs/      every test-case run: the model's files, logs, metrics.json
  test-results/   results.csv (all runs) and results.md (comparison table)
  benchmarks.csv  speed-test results
  state.json, server.log, generate.log
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

## Images, video and speech

| Kind | Model | Download | Memory | Notes |
|---|---|---|---|---|
| Images | SD-Turbo | 4.9 GB | 8 GB | 512 px, 4 steps, fastest |
| Images | Flux.1 schnell (Q4_K) | 9.7 GB | 16 GB | 1024 px, 4 steps |
| Images | Z-Image Turbo (Q8_0) | 10.4 GB | 24 GB | 1024 px, 8 steps, readable text |
| Video | Wan 2.1 1.3B (Q8_0) | 7.3 GB | 16 GB | 33 frames at 832×480, 16 fps, `.webm` |
| Video | Wan 2.2 TI2V 5B (Q8_0) | 12.0 GB | 32 GB | 33 frames at 832×480, 24 fps, `.webm` |
| Speech | Qwen3-TTS 1.7B (Q4_K_M) | 1.4 GB | 8 GB | 10 languages including Russian, `.wav` |
| Speech | Qwen3-TTS 1.7B (Q8_0) | 2.1 GB | 16 GB | same, cleaner voice |

Images and video run on stable-diffusion.cpp, speech on `llama-tts` from the same
llama.cpp build as the code models. A generation is a separate run of the engine, so the
first seconds go to loading the model. A video takes several minutes on a Mac. If a code
model server is running, the wizard stops it first to free memory. Descriptions work best
in English. Speech picks Russian when the text contains Cyrillic, English otherwise; to
make it sound like a particular voice, put a 5–15 second recording (`.wav` or `.mp3`)
into `local-ai/voices/`.

## Test cases

The `test-cases/` folder holds ready-made tasks for comparing models: start menu →
"Test cases" → kind → one case or all → one model or all downloaded ones, one after another.

| Kind | Cases |
|---|---|
| Code | `cli-log-analyzer`: a CLI tool with tests over a web log; `fix-failing-tests`: find the bugs that break the given tests; `landing-page`: a landing page with a theme toggle; `seo-audit`: an SEO audit of klukyanov.ru with web fetches |
| Images | `portrait`, `text-poster` (is the text readable), `complex-scene` (are all objects in place), fixed seed |
| Video | `cat-walk`, `city-pan` |
| Speech | `short-paragraph`, `russian-paragraph`, `long-article` (about 1.5 minutes) |

The wizard measures everything itself; the model does not report its own numbers.

After a run the wizard offers to send the numbers to the developers. It shows the exact text
first: wizard version, system, chip, RAM, and per run the model, engine, status, time, memory and
token speed. There are no prompts, model answers, file paths or user names. On "Yes" the text is
copied to the clipboard and a new GitHub issue opens: paste it and press Submit (a free GitHub
account is needed). Nothing is sent without that last click. The text is also saved as
`local-ai/test-results/share-<run>.md`.

- Code: the model works through `opencode run` in a fresh folder, OpenCode approves its
  actions on its own (inside `local-ai/test-runs/` only). Recorded: wall time, peak memory of
  the model server, tokens in / out / thinking / cached and tool calls from OpenCode's
  events, and on llama.cpp exact prompt-reading and generation speeds from the server's
  counters. On MLX generation speed is output tokens divided by the wall time. Then a hidden
  check runs: for three cases a script that compares the result with the right answer
  (the model never sees it), for the SEO audit a check for the required sections. Each code
  prompt also asks the model to write `REPORT.md` about what it did.
- Images, video, speech: wall time, peak memory of the engine, seconds per image, per
  video frame or per second of audio.

Every run goes to `local-ai/test-runs/<date>/<case>/<model>/` (the model's files in
`work/`, plus `metrics.json`, `events.jsonl`, `answer.md`, `check.log`). One line per run is
appended to `local-ai/test-results/results.csv`, and `results.md` shows the latest run of
every model side by side. The format of a case file is described in
[test-cases/README.md](test-cases/README.md), so you can add your own.

## llama.cpp or MLX

On Apple Silicon both run on the GPU: llama.cpp through Metal, MLX natively. MLX is
often faster on Macs. llama.cpp works on every system and has more mature tool
calling, which OpenCode depends on. To compare them on your machine:

1. Menu → "Another configuration", pick Code, an engine and a model.
2. Menu → "Speed test". It measures prompt reading (a ~4K-token prompt) and answer
   generation (~300 tokens), and appends a line to `local-ai/benchmarks.csv`.
3. Repeat with the other engine and the same model, then compare. Also try a real
   task in OpenCode: speed is not everything if tool calls fail.

## Updates

Every launch first asks GitHub whether a newer release of Local AI Starter is out
(5 seconds at most; without internet it just says so and goes on). If there is one,
you see what's new and choose: **Update now** (Enter), **Not now**, or **Skip this
version**. After updating, the wizard restarts on the new version. Models, engines and
settings in `local-ai/` are never touched by an update.

- Folder cloned with git: the wizard fast-forwards to the release tag (`git merge --ff-only`).
  If you changed files yourself, it leaves them alone and suggests `git pull`.
- Folder downloaded as a ZIP: the wizard downloads the release archive and replaces
  its own files.
- Only published releases count; work in progress on `main` is never offered.
- `--no-update` or `LOCAL_AI_STARTER_NO_UPDATE=1` skips the check.

## Settings

| Variable | What it does |
|---|---|
| `LOCAL_AI_STARTER_LANG=en\|ru` | force the wizard language |
| `LOCAL_AI_STARTER_HOME=<path>` | keep data somewhere other than `local-ai/` |
| `LOCAL_AI_STARTER_DRY_RUN=1` | walk through the flow without downloading or starting anything |
| `LOCAL_AI_STARTER_NO_UPDATE=1` | do not check for updates on launch |
| `HTTPS_PROXY` | standard proxy setting, honoured for all downloads |

## Limits

- The engines are CPU builds on Windows and Linux (Metal is used on Mac). GPU
  acceleration on Windows/Linux is not configured yet, so images and especially video
  are slow there. Images and video need macOS, x64 Linux or x64 Windows.
- Peak memory is the resident memory of the process. With MLX on a Mac it may not
  include all GPU memory.
- Small local models are much weaker than cloud ones: expect simple edits, not big refactors.

## Manual test checklist

macOS Apple Silicon, both engines: clean start → OpenCode edits `index.html` → `/exit` →
menu → speed test → switch engine → restart (start menu lists both) → stop → "Delete everything".
Images, video and speech: one generation each, then one test case of every kind. Interrupted model download (resume), blocked
host (message), port 8080 in use, low disk space. Linux and Windows on real machines.

## License

MIT, see [LICENSE](LICENSE). The script downloads third-party components
(llama.cpp, MLX and mlx-lm, uv, stable-diffusion.cpp, Qwen, Qwen3-TTS, FLUX.1 schnell,
Z-Image, Wan, OpenCode) under their own licenses. SD-Turbo comes under the Stability AI
Community License (free below $1M annual revenue, see stability.ai/license).
