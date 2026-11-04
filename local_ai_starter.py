#!/usr/bin/env python3
"""Local AI Starter: one click from nothing to OpenCode on a local model.

Run with no arguments: ``python3 local_ai_starter.py`` (or double-click RunMe.*).
``--menu`` opens the management menu without starting OpenCode. Every launch first checks
GitHub Releases for a newer version (``--no-update`` skips that).

Everything the script downloads or creates lives in the ``local-ai`` folder next to
it: engines (``engines/llama.cpp``, ``engines/mlx``), models (``models/<engine>/<family>/``),
OpenCode, its settings, the workspace, the log and speed-test results. Deleting that folder removes everything. The server listens on 127.0.0.1
only. PATH, shell configs and global OpenCode settings are never touched.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from dataclasses import dataclass
from pathlib import Path

VERSION = "2.1.0"  # must match the GitHub release tag (vX.Y.Z)

DRY_RUN = os.environ.get("LOCAL_AI_STARTER_DRY_RUN") == "1"
DEFAULT_PORT = 8080
NET_CHECK_TIMEOUT = 15   # seconds to wait for a host to answer the pre-flight check
STALL_TIMEOUT = 30       # seconds without a single byte before a download is retried
DOWNLOAD_ATTEMPTS = 5

APP_DIR = Path(__file__).resolve().parent  # the wizard's own files; updates replace them
ROOT = Path(os.environ.get("LOCAL_AI_STARTER_HOME") or (APP_DIR / "local-ai"))
ENGINES_DIR = ROOT / "engines"
LLAMA_DIR = ENGINES_DIR / "llama.cpp"
MLX_DIR = ENGINES_DIR / "mlx"
MODELS_DIR = ROOT / "models"
OPENCODE_DIR = ROOT / "opencode"
OPENCODE_HOME = ROOT / "opencode-home"
OPENCODE_CONFIG = ROOT / "opencode.json"
WORKSPACE_DIR = ROOT / "workspace"
STATE_FILE = ROOT / "state.json"
LOG_FILE = ROOT / "server.log"
BENCH_FILE = ROOT / "benchmarks.csv"

ENGINE_NAMES = {"gguf": "llama.cpp", "mlx": "MLX"}

# Updates come from GitHub Releases only, so unreleased pushes to main never reach users.
# The two overrides exist for testing against a local server.
UPDATE_REPO = "kiri11ko/local-ai-starter"
UPDATE_API = (os.environ.get("LOCAL_AI_STARTER_UPDATE_API")
              or f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest")
UPDATE_ZIP = (os.environ.get("LOCAL_AI_STARTER_UPDATE_ZIP")
              or f"https://github.com/{UPDATE_REPO}/archive/refs/tags/{{tag}}.zip")
UPDATE_TIMEOUT = 5

# Pinned llama.cpp build: one version for everyone, hashes from the release page.
LLAMA_BUILD = "b12110"
LLAMA_URL = "https://github.com/ggml-org/llama.cpp/releases/download/{build}/llama-{build}-bin-{plat}.{ext}"
LLAMA_SHA256 = {
    "macos-arm64": "4f5b8de12e0b9516658ca6a5764c6ffb3d7c659c3dd538556b1413c7b4050662",
    "macos-x64": "c8094268b6bf62f4998f0e45656fd9f5e2d4afb6b1cd0044d761db64be1dd47d",
    "ubuntu-x64": "368227edcc229be5f9bed16a2223d79b5e41d0ac2e19bcf5825e82291c060e55",
    "ubuntu-arm64": "4758b51335e37b4346251f2687d64841ff1c07ecb27fc46323945bb2ec9c44d2",
    "win-cpu-x64": "98901e327c252875accaf2d1bf364e10e868843b0b63468baad1aa945cdc5da2",
    "win-cpu-arm64": "f8d20fb07d0b499988ced8963afcd5ded2d2cdd9983b757fbc7e51c4abd722e8",
}
LLAMA_SIZE_MB = 40

# MLX (Apple Silicon only): mlx-lm needs Python 3.11+, so a pinned uv brings its own Python.
UV_VERSION = "0.13.1"
UV_URL = f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-aarch64-apple-darwin.tar.gz"
UV_SHA256 = "cfe454573412ff7380d15fc7dae5997ab53ffce72fce0a78e91ddbc84001acd2"
MLX_PYTHON = "3.12"
MLX_LM_VERSION = "0.32.2"
MLX_PYPI_URL = f"https://pypi.org/pypi/mlx-lm/{MLX_LM_VERSION}/json"
MLX_SIZE_MB = 300  # uv + Python + mlx, mlx-lm and their dependencies, roughly

# Pinned OpenCode CLI build, same idea: official GitHub release asset + SHA-256.
OPENCODE_VERSION = "v1.19.5"
OPENCODE_URL = "https://github.com/anomalyco/opencode/releases/download/{ver}/opencode-{plat}.{ext}"
OPENCODE_SHA256 = {
    "darwin-arm64": "c1c9e62521192192ef4c3ed1355ada2144055bddb61682217e997b03c55203c1",
    "darwin-x64": "b0212efa6db347187225a17fa3a31c6b261bf4c9f1589a290b0ca902d720d250",
    "linux-arm64": "fae5be262d693b7c5e562856cc473e59e741772936db0c0600ac0d5ed5bd088b",
    "linux-x64": "588310a336fa3b9df36b3f0225b26f679d453efaad0cf3d66c3651ef3ec1647a",
    "windows-arm64": "5d49139bd917511ff35a3c06065c9f47918346668f05ea020e778286f302fbb7",
    "windows-x64": "09a6e693157f0887e504f2cf4357a8cbddc5ead5d0dffb9a269dcc47c48640f5",
}
OPENCODE_SIZE_MB = 80


@dataclass(frozen=True)
class Profile:
    key: str          # unique id, kept in state.json; llama-server --alias
    base: str         # model name shared by both engines, picks the label in STRINGS
    engine: str       # "gguf" (llama.cpp) or "mlx"
    family: str       # folder under models/<engine>/
    repo: str         # Hugging Face repository
    file: str         # gguf: file name; mlx: pinned commit of the repository
    quant: str
    size: int         # bytes
    sha256: str       # gguf only; MLX files are checked against the LFS hashes of the pinned commit
    min_ram_gb: int

    @property
    def path(self) -> Path:
        name = self.file if self.engine == "gguf" else self.repo.split("/")[-1]
        return MODELS_DIR / self.engine / self.family / name

    @property
    def label_path(self) -> str:
        return str(self.path.relative_to(MODELS_DIR))

    @property
    def url(self) -> str:
        if self.engine == "gguf":
            return f"https://huggingface.co/{self.repo}/resolve/main/{self.file}"
        return f"https://huggingface.co/api/models/{self.repo}/tree/{self.file}?recursive=1"

    @property
    def installed(self) -> bool:
        return self.path.is_file() if self.engine == "gguf" else (self.path / ".complete").exists()


def _gguf(base, repo, file, quant, size, sha256, ram):
    return Profile(base if quant.startswith("Q4") else f"{base}-q8", base if quant.startswith("Q4") else f"{base}-q8",
                   "gguf", "qwen", repo, file, quant, size, sha256, ram)


def _mlx(base, repo, commit, quant, size, ram):
    return Profile(f"{base}-mlx", base, "mlx", "qwen", repo, commit, quant, size, "", ram)


# Ordered from small to large; the recommendation is the largest one that fits the memory.
# GGUF and MLX lines mirror each other, so both engines can be compared on the same model.
_MODELS = [
    _gguf("qwen3.5-4b", "unsloth/Qwen3.5-4B-GGUF", "Qwen3.5-4B-Q4_K_M.gguf", "Q4_K_M", 2740937888,
          "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4", 8),
    _gguf("qwen3.5-9b", "unsloth/Qwen3.5-9B-GGUF", "Qwen3.5-9B-Q4_K_M.gguf", "Q4_K_M", 5680522464,
          "03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8", 16),
    _gguf("qwen3.8-27b", "ggml-org/Qwen3.8-27B-GGUF", "Qwen3.8-27B-Q4_K_M.gguf", "Q4_K_M", 18973870528,
          "c600de0300ae8a0eb3a6c0b8b5561b8b96f16bd2c863c2a66c42de29d391a747", 32),
    _gguf("qwen3.6-35b-a3b", "ggml-org/Qwen3.6-35B-A3B-GGUF", "Qwen3.6-35B-A3B-Q4_K_M.gguf", "Q4_K_M", 20419565568,
          "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7", 48),
    _gguf("qwen3.6-35b-a3b", "ggml-org/Qwen3.6-35B-A3B-GGUF", "Qwen3.6-35B-A3B-Q8_0.gguf", "Q8_0", 36903139328,
          "d8d7842cc657d720f39546878e431937c84473aa130c36371669ac17c80c7361", 64),
    _mlx("qwen3.5-4b", "mlx-community/Qwen3.5-4B-4bit", "0e7ffd5c629ef7719d4cbc04069232580bfa9d9c",
         "4-bit", 3061130647, 8),
    _mlx("qwen3.5-9b", "mlx-community/Qwen3.5-9B-4bit", "8b2b98c00a6b4d291155e4890773ca8f769aee53",
         "4-bit", 5977073303, 16),
    _mlx("qwen3.8-27b", "mlx-community/Qwen3.8-27B-4bit", "10c35caafbb80f7dc6a7a432cdd11af10a6d4818",
         "4-bit", 16081490933, 32),
    _mlx("qwen3.6-35b-a3b", "mlx-community/Qwen3.6-35B-A3B-4bit", "38740b847e4cb78f352aba30aa41c76e08e6eb46",
         "4-bit", 20429169263, 48),
    _mlx("qwen3.6-35b-a3b-q8", "mlx-community/Qwen3.6-35B-A3B-8bit", "e06a74e6236a60c8367e1a3214e83d8b61b637b0",
         "8-bit", 37748367994, 64),
]
PROFILES = {profile.key: profile for profile in _MODELS}


# ───────────────────────────── strings ─────────────────────────────

STRINGS = {
    "en": {
        "title": "Local AI Starter",
        "tagline": "A local AI assistant on your computer. No cloud, no keys.",
        "hint_arrows": "↑/↓ to move, Enter to choose",
        "hint_numbers": "Type a number or just press Enter.",
        "bad_number": "Type a number from 1 to {n}, or just press Enter.",
        "yes": "Yes", "no": "No",
        "recommended": "recommended",
        "cancelled": "Cancelled.",
        "gb": "GB", "mb": "MB", "mbs": "MB/s", "eta": "left",
        "error": "Error: {error}",
        "system_check": "Checking your computer",
        "system": "System", "memory": "Memory", "disk_free": "Free disk space",
        "unknown": "unknown",
        "pick_model": "Which model should the assistant use?",
        "model.qwen3.5-4b": "Qwen3.5 4B: fast, fits 8 GB",
        "model.qwen3.5-9b": "Qwen3.5 9B: balanced, 16 GB",
        "model.qwen3.8-27b": "Qwen3.8 27B: newest and smartest, slower, 32 GB",
        "model.qwen3.6-35b-a3b": "Qwen3.6 35B-A3B: large but fast (MoE), 48 GB",
        "model.qwen3.6-35b-a3b-q8": "Qwen3.6 35B-A3B, 8-bit: best quality, 64 GB",
        "pick_engine": "Which engine should run the model?",
        "engine.gguf": "llama.cpp, GGUF models: works on every system, mature tool calling",
        "engine.mlx": "MLX, Apple's framework: often faster on Apple Silicon",
        "plan_mlx": "MLX runtime: uv {uv}, Python {py}, mlx-lm {ver}",
        "mlx_failed": "Installing the MLX runtime failed, see the messages above. Run RunMe again: "
                      "everything already downloaded is kept.",
        "file_n": "{name} ({i} of {n})",
        "chat_mlx": "The web chat comes with llama.cpp only. With MLX use OpenCode, or switch the engine.",
        "menu.bench": "Speed test (results go to benchmarks.csv)",
        "bench_title": "Speed test: {model} on {engine}",
        "bench_running": "Measuring: a long prompt, then a ~300-token answer. This takes a minute or two…",
        "bench_prefill": "Prompt reading: {tps:.0f} tokens/s ({n} tokens, first token after {ttft:.1f} s)",
        "bench_gen": "Answer generation: {tps:.1f} tokens/s ({n} tokens)",
        "bench_saved": "Saved to {file}",
        "bench_fail": "The speed test failed: {error}",
        "models_incomplete": "incomplete",
        "update_check_failed": "Could not check for updates, continuing.",
        "update_available": "Local AI Starter {new} is available (you have {old}).",
        "update_question": "Update now?",
        "update_now": "Update now",
        "update_later": "Not now",
        "update_skip": "Skip this version",
        "update_local_changes": "Could not update automatically: this folder has local changes or a different "
                                "history. Update by hand with git pull (release {tag}).",
        "update_failed": "The update failed: {error}. Continuing with the current version.",
        "update_bad_archive": "The release archive does not contain local_ai_starter.py.",
        "update_done": "Updated to {version}. Models and settings in local-ai/ are kept.",
        "update_restarting": "Restarting with the new version…",
        "status_bench": "Speed tests",
        "low_ram": "This model wants {need} GB of memory, you have {have:.0f} GB. It may be slow.",
        "continue_anyway": "Continue anyway?",
        "low_disk": "Not enough free space: about {need:.1f} GB is needed, {have:.1f} GB is free.",
        "plan": "Plan",
        "plan_engine": "llama.cpp engine {build}",
        "plan_model": "Model {file}",
        "plan_opencode": "OpenCode {ver}",
        "plan_total": "Total download: about {gb:.1f} GB, into {root}",
        "start": "Start?",
        "net_check": "Checking that the download servers are reachable…",
        "net_ok": "{host}: reachable",
        "net_fail_title": "{host} is not reachable from this network.",
        "net_reason.timeout": "It did not answer within {sec} seconds.",
        "net_reason.dns": "Its name could not be resolved (DNS).",
        "net_reason.refused": "The connection was refused or reset.",
        "net_reason.ssl": "The secure connection failed; a proxy or filter may be intercepting traffic.",
        "net_reason.http": "The server answered with an error: HTTP {code}.",
        "net_reason.other": "{detail}",
        "net_missing": "{host}: file not found (HTTP 404): {url}\nThe pinned version may have been removed. "
                       "Get a fresh copy of Local AI Starter.",
        "net_advice": "The resource is probably blocked or restricted on this network. Try another network "
                      "(for example a phone hotspot), a VPN, or a proxy (set HTTPS_PROXY), then run RunMe "
                      "again. Finished downloads are kept, interrupted ones resume.",
        "step": "[{i}/{n}] {what}",
        "downloading": "Downloading {name}",
        "download_retry": "Connection dropped ({reason}). Retrying in {sec} s, attempt {i} of {n}…",
        "verifying": "Checking the file…",
        "hash_ok": "File verified.",
        "hash_bad": "Checksum of {name} did not match; the file was deleted. Run RunMe again.",
        "extracting": "Unpacking…",
        "no_server_binary": "llama-server is missing from the archive; the build layout may have changed.",
        "no_opencode_binary": "opencode is missing from the archive; the release layout may have changed.",
        "unsupported_platform": "Platform {system} {machine} is not supported.",
        "no_free_port": "No free port found near 8080.",
        "starting_server": "Loading the model into memory…",
        "server_stopped": "The server stopped. Last log line: {line}\nFull log: {log}",
        "server_timeout": "The server did not start in {min} minutes. See the log: {log}",
        "server_test": "Server is up. Asking a test question…",
        "server_no_answer": "The server is running but does not answer. See the log: {log}",
        "server_ok": "The model answers. All set.",
        "server_running": "Server is already running.",
        "port_busy": "Port {busy} is busy, using {port}.",
        "stopping": "Stopping the server (PID {pid}).",
        "no_server": "No server is running.",
        "opencode_intro": "Opening OpenCode in {dir}",
        "opencode_tips": "Type a request and press Enter, for example: “{example}”.\n"
                         "OpenCode asks before it changes files. Quit with /exit or Ctrl+C.",
        "opencode_example": "Change the heading in index.html and add a dark theme toggle",
        "opencode_missing": "OpenCode is not installed.",
        "dry_run_would": "[dry-run] would {what}",
        "menu_title": "What next?",
        "menu.stop_exit": "Stop the server and exit",
        "menu.keep_exit": "Exit, keep the server running",
        "menu.opencode": "Back to OpenCode",
        "menu.chat": "Open the web chat in the browser",
        "menu.switch": "Switch model or engine",
        "menu.models": "Models on disk",
        "menu.status": "Status and log",
        "menu.uninstall": "Delete everything that was downloaded",
        "chat_url": "Chat: {url}",
        "models_title": "Models in {dir}",
        "models_none": "No models downloaded yet.",
        "models_total": "Total: {gb:.1f} GB",
        "models_pick": "Delete a model?",
        "models_back": "Back",
        "models_open": "Open the models folder",
        "models_deleted": "Deleted {file}.",
        "status_root": "Data folder", "status_engine": "Engine", "status_opencode": "OpenCode",
        "status_server": "Server", "status_model": "Model", "status_log": "Log", "status_last": "Last line",
        "installed": "installed", "not_installed": "not installed",
        "running_on": "running, port {port}", "not_running": "not running",
        "uninstall_warn": "The whole folder {root} will be deleted: engines, models, OpenCode, the workspace and speed tests.",
        "uninstall_confirm": "Delete everything?",
        "uninstall_done": "Done. Nothing else is left on the system.",
        "demo_title": "Practice page",
        "demo_heading": "Hello!",
        "demo_text": "Ask the assistant: “change the heading and add a dark theme toggle”.",
    },
    "ru": {
        "title": "Local AI Starter",
        "tagline": "Локальный ИИ-помощник на вашем компьютере. Без облака и ключей.",
        "hint_arrows": "↑/↓ — выбор, Enter — подтвердить",
        "hint_numbers": "Введите номер или просто нажмите Enter.",
        "bad_number": "Введите число от 1 до {n} или просто нажмите Enter.",
        "yes": "Да", "no": "Нет",
        "recommended": "рекомендую",
        "cancelled": "Отменено.",
        "gb": "ГБ", "mb": "МБ", "mbs": "МБ/с", "eta": "осталось",
        "error": "Ошибка: {error}",
        "system_check": "Проверка компьютера",
        "system": "Система", "memory": "Память", "disk_free": "Свободно на диске",
        "unknown": "не удалось определить",
        "pick_model": "Какую модель взять помощнику?",
        "model.qwen3.5-4b": "Qwen3.5 4B: быстрая, хватит 8 ГБ",
        "model.qwen3.5-9b": "Qwen3.5 9B: сбалансированная, 16 ГБ",
        "model.qwen3.8-27b": "Qwen3.8 27B: новейшая и самая умная, медленнее, 32 ГБ",
        "model.qwen3.6-35b-a3b": "Qwen3.6 35B-A3B: большая, но быстрая (MoE), 48 ГБ",
        "model.qwen3.6-35b-a3b-q8": "Qwen3.6 35B-A3B, 8 бит: лучшее качество, 64 ГБ",
        "pick_engine": "На каком движке запускать модель?",
        "engine.gguf": "llama.cpp, модели GGUF: работает на любой системе, отлаженный вызов инструментов",
        "engine.mlx": "MLX, фреймворк Apple: на Apple Silicon часто быстрее",
        "plan_mlx": "Среда MLX: uv {uv}, Python {py}, mlx-lm {ver}",
        "mlx_failed": "Не удалось установить среду MLX, подробности выше. Запустите RunMe ещё раз: "
                      "всё уже скачанное сохранится.",
        "file_n": "{name} ({i} из {n})",
        "chat_mlx": "Веб-чат есть только у llama.cpp. С MLX работайте в OpenCode или смените движок.",
        "menu.bench": "Замер скорости (результаты — в benchmarks.csv)",
        "bench_title": "Замер скорости: {model} на {engine}",
        "bench_running": "Замеряю: длинный запрос, затем ответ ~300 токенов. Займёт минуту-две…",
        "bench_prefill": "Чтение запроса: {tps:.0f} токенов/с ({n} токенов, первый токен через {ttft:.1f} с)",
        "bench_gen": "Генерация ответа: {tps:.1f} токенов/с ({n} токенов)",
        "bench_saved": "Записано в {file}",
        "bench_fail": "Замер не удался: {error}",
        "models_incomplete": "не докачано",
        "update_check_failed": "Не удалось проверить обновления, продолжаю.",
        "update_available": "Вышла версия Local AI Starter {new} (у вас {old}).",
        "update_question": "Обновить сейчас?",
        "update_now": "Обновить сейчас",
        "update_later": "Не сейчас",
        "update_skip": "Пропустить эту версию",
        "update_local_changes": "Не удалось обновить автоматически: в папке есть свои изменения или другая "
                                "история. Обновите вручную через git pull (релиз {tag}).",
        "update_failed": "Обновление не удалось: {error}. Продолжаю на текущей версии.",
        "update_bad_archive": "В архиве релиза нет local_ai_starter.py.",
        "update_done": "Обновлено до {version}. Модели и настройки в local-ai/ сохранены.",
        "update_restarting": "Перезапускаю новую версию…",
        "status_bench": "Замеры скорости",
        "low_ram": "Этой модели желательно {need} ГБ памяти, у вас {have:.0f} ГБ. Может работать медленно.",
        "continue_anyway": "Всё равно продолжить?",
        "low_disk": "Мало места: нужно около {need:.1f} ГБ, свободно {have:.1f} ГБ.",
        "plan": "План",
        "plan_engine": "Движок llama.cpp {build}",
        "plan_model": "Модель {file}",
        "plan_opencode": "OpenCode {ver}",
        "plan_total": "Всего скачать: около {gb:.1f} ГБ, в {root}",
        "start": "Начинаем?",
        "net_check": "Проверяю, доступны ли серверы для загрузки…",
        "net_ok": "{host}: доступен",
        "net_fail_title": "{host} недоступен из этой сети.",
        "net_reason.timeout": "Не ответил за {sec} секунд.",
        "net_reason.dns": "Не удалось найти адрес по имени (DNS).",
        "net_reason.refused": "Соединение отклонено или сброшено.",
        "net_reason.ssl": "Не удалось установить защищённое соединение; возможно, трафик перехватывает прокси или фильтр.",
        "net_reason.http": "Сервер ответил ошибкой: HTTP {code}.",
        "net_reason.other": "{detail}",
        "net_missing": "{host}: файл не найден (HTTP 404): {url}\nВозможно, закреплённую версию убрали с сервера. "
                       "Скачайте свежую версию Local AI Starter.",
        "net_advice": "Похоже, этот ресурс заблокирован или ограничен в вашей сети. Попробуйте другую сеть "
                      "(например, раздачу с телефона), VPN или прокси (переменная HTTPS_PROXY), затем снова "
                      "запустите RunMe. Скачанное сохранится, прерванное докачается.",
        "step": "[{i}/{n}] {what}",
        "downloading": "Скачиваю {name}",
        "download_retry": "Связь прервалась ({reason}). Повтор через {sec} с, попытка {i} из {n}…",
        "verifying": "Проверяю файл…",
        "hash_ok": "Файл проверен.",
        "hash_bad": "Контрольная сумма {name} не совпала, файл удалён. Запустите RunMe ещё раз.",
        "extracting": "Распаковываю…",
        "no_server_binary": "В архиве нет llama-server — возможно, сборка изменила состав.",
        "no_opencode_binary": "В архиве нет opencode — возможно, релиз изменил состав.",
        "unsupported_platform": "Платформа {system} {machine} не поддерживается.",
        "no_free_port": "Не нашёл свободный порт рядом с 8080.",
        "starting_server": "Загружаю модель в память…",
        "server_stopped": "Сервер остановился. Последняя строка журнала: {line}\nПолный журнал: {log}",
        "server_timeout": "Сервер не запустился за {min} минут. Смотрите журнал: {log}",
        "server_test": "Сервер запущен. Задаю пробный вопрос…",
        "server_no_answer": "Сервер запущен, но не отвечает. Смотрите журнал: {log}",
        "server_ok": "Модель отвечает. Всё готово.",
        "server_running": "Сервер уже работает.",
        "port_busy": "Порт {busy} занят, использую {port}.",
        "stopping": "Останавливаю сервер (PID {pid}).",
        "no_server": "Запущенного сервера нет.",
        "opencode_intro": "Открываю OpenCode в папке {dir}",
        "opencode_tips": "Напишите задачу и нажмите Enter, например: «{example}».\n"
                         "OpenCode спросит, прежде чем менять файлы. Выход — /exit или Ctrl+C.",
        "opencode_example": "Измени заголовок в index.html и добавь переключатель тёмной темы",
        "opencode_missing": "OpenCode не установлен.",
        "dry_run_would": "[dry-run] сделал бы: {what}",
        "menu_title": "Что дальше?",
        "menu.stop_exit": "Остановить сервер и выйти",
        "menu.keep_exit": "Выйти, сервер оставить работать",
        "menu.opencode": "Вернуться в OpenCode",
        "menu.chat": "Открыть веб-чат в браузере",
        "menu.switch": "Сменить модель или движок",
        "menu.models": "Модели на диске",
        "menu.status": "Состояние и журнал",
        "menu.uninstall": "Удалить всё, что скачано",
        "chat_url": "Чат: {url}",
        "models_title": "Модели в {dir}",
        "models_none": "Пока ни одной модели не скачано.",
        "models_total": "Всего: {gb:.1f} ГБ",
        "models_pick": "Удалить модель?",
        "models_back": "Назад",
        "models_open": "Открыть папку с моделями",
        "models_deleted": "Удалено: {file}.",
        "status_root": "Папка данных", "status_engine": "Движок", "status_opencode": "OpenCode",
        "status_server": "Сервер", "status_model": "Модель", "status_log": "Журнал", "status_last": "Последняя строка",
        "installed": "установлен", "not_installed": "не установлен",
        "running_on": "работает, порт {port}", "not_running": "не запущен",
        "uninstall_warn": "Будет удалена папка {root} целиком: движки, модели, OpenCode, рабочая папка и замеры.",
        "uninstall_confirm": "Удалить всё?",
        "uninstall_done": "Готово. В системе ничего больше не осталось.",
        "demo_title": "Учебная страница",
        "demo_heading": "Привет!",
        "demo_text": "Попросите помощника: «измени заголовок и добавь переключатель тёмной темы».",
    },
}


def detect_lang() -> str:
    """Russian for a Russian system locale, English otherwise. LOCAL_AI_STARTER_LANG overrides."""
    forced = os.environ.get("LOCAL_AI_STARTER_LANG", "").lower()
    if forced in STRINGS:
        return forced
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name, "")
        if value and value not in {"C", "POSIX"} and not value.startswith("C."):
            return "ru" if value.lower().startswith("ru") else "en"
    try:
        system = platform.system()
        if system == "Darwin":
            out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"],
                                 capture_output=True, text=True, timeout=3).stdout
            first = out.replace("(", "").replace('"', "").split(",")[0].strip().lower()
            return "ru" if first.startswith("ru") else "en"
        if system == "Windows":
            import ctypes
            return "ru" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x19 else "en"
    except Exception:
        pass
    return "en"


LANG = detect_lang()


def t(key: str, **kwargs) -> str:
    text = STRINGS[LANG].get(key) or STRINGS["en"][key]
    return text.format(**kwargs) if kwargs else text


def size_text(gigabytes: float) -> str:
    if gigabytes >= 1:
        return f"{gigabytes:.1f} {t('gb')}"
    return f"{gigabytes * 1024:.0f} {t('mb')}"


# ───────────────────────────── terminal ─────────────────────────────

class Cancelled(Exception):
    pass


class NetworkError(RuntimeError):
    pass


def _enable_ansi() -> bool:
    if not sys.stdout.isatty() or os.environ.get("TERM") == "dumb":
        return False
    if platform.system() != "Windows":
        return True
    try:
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel.SetConsoleMode(handle, mode.value | 0x0004))  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        return False


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ANSI = _enable_ansi()
COLOR = ANSI and "NO_COLOR" not in os.environ
INTERACTIVE = ANSI and sys.stdin.isatty()


def paint(text: str, code: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if COLOR else text


def bold(text: str) -> str:
    return paint(text, "1")


def dim(text: str) -> str:
    return paint(text, "2")


def ok(text: str) -> str:
    return paint("✓ ", "32") + text


def fail(text: str) -> str:
    return paint("✗ ", "31") + text


def say(text: str = "") -> None:
    print(text, flush=True)


def banner() -> None:
    title = f"  {t('title')} {VERSION}  "
    line = "─" * len(title)
    say(paint(f"╭{line}╮\n│{title}│\n╰{line}╯", "36"))
    say(t("tagline"))


def step(i: int, n: int, what: str) -> None:
    say("\n" + bold(t("step", i=i, n=n, what=what)))


def _read_key_posix(fd: int) -> str:
    import select
    data = os.read(fd, 1)
    if data == b"\x1b":
        if select.select([fd], [], [], 0.05)[0]:
            data += os.read(fd, 8)
        if data in (b"\x1b[A", b"\x1bOA"):
            return "up"
        if data in (b"\x1b[B", b"\x1bOB"):
            return "down"
        return "esc"
    if data in (b"\r", b"\n"):
        return "enter"
    if data == b"\x03":
        raise KeyboardInterrupt()
    return data.decode(errors="ignore")


def _read_key_windows() -> str:
    import msvcrt
    char = msvcrt.getwch()
    if char in ("\x00", "\xe0"):
        code = msvcrt.getwch()
        return {"H": "up", "P": "down"}.get(code, "")
    if char == "\r":
        return "enter"
    if char == "\x03":
        raise KeyboardInterrupt()
    if char == "\x1b":
        return "esc"
    return char


def _ask_arrows(options: list[str], default: int) -> int:
    selected = default - 1

    def draw(first: bool) -> None:
        if not first:
            sys.stdout.write(f"\x1b[{len(options) + 1}F")
        for index, option in enumerate(options):
            prefix = f"{index + 1}) "
            line = paint(f"› {prefix}{option}", "1;36") if index == selected else f"  {prefix}{option}"
            sys.stdout.write("\x1b[2K" + line + "\n")
        sys.stdout.write("\x1b[2K" + dim(t("hint_arrows")) + "\n")
        sys.stdout.flush()

    sys.stdout.write("\x1b[?25l")
    draw(True)
    windows = platform.system() == "Windows"
    if not windows:
        import termios
        import tty
        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    try:
        while True:
            key = _read_key_windows() if windows else _read_key_posix(fd)
            if key == "up":
                selected = (selected - 1) % len(options)
            elif key == "down":
                selected = (selected + 1) % len(options)
            elif key == "enter":
                return selected + 1
            elif key.isdigit() and 1 <= int(key) <= len(options):
                selected = int(key) - 1
                draw(False)
                return selected + 1
            else:
                continue
            draw(False)
    finally:
        if not windows:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        sys.stdout.write("\x1b[?25h")
        sys.stdout.flush()


def _ask_numbers(options: list[str], default: int) -> int:
    for number, option in enumerate(options, 1):
        mark = "  ← Enter" if number == default else ""
        say(f"  {number}) {option}{mark}")
    say(dim(t("hint_numbers")))
    while True:
        answer = input("> ").strip()
        if not answer:
            return default
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer)
        say(t("bad_number", n=len(options)))


def ask(question: str, options: list[str], default: int = 1) -> int:
    """Shows options; arrows or a digit pick one, Enter confirms. Returns a 1-based index."""
    say("\n" + bold(question))
    try:
        if INTERACTIVE:
            return _ask_arrows(options, default)
        return _ask_numbers(options, default)
    except (EOFError, KeyboardInterrupt):
        raise Cancelled()


def yes_no(question: str, default_yes: bool = True) -> bool:
    return ask(question, [t("yes"), t("no")], 1 if default_yes else 2) == 1


# ───────────────────────────── system ─────────────────────────────

def ram_gb() -> float | None:
    try:
        system = platform.system()
        if system == "Darwin":
            return int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip()) / 2**30
        if system == "Linux":
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / 2**20
        if system == "Windows":
            import ctypes

            class Status(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                            ("total", ctypes.c_ulonglong), ("avail", ctypes.c_ulonglong),
                            ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong),
                            ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong),
                            ("ext", ctypes.c_ulonglong)]

            status = Status()
            status.length = ctypes.sizeof(Status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return status.total / 2**30
    except Exception:
        pass
    return None


def free_gb() -> float:
    target = ROOT if ROOT.exists() else ROOT.parent
    return shutil.disk_usage(target).free / 2**30


def _arch() -> tuple[str, bool]:
    system, machine = platform.system(), platform.machine().lower()
    return system, machine in {"arm64", "aarch64"}


def llama_platform() -> str:
    system, arm = _arch()
    names = {"Darwin": "macos", "Linux": "ubuntu", "Windows": "win-cpu"}
    if system not in names:
        raise RuntimeError(t("unsupported_platform", system=system, machine=platform.machine()))
    return f"{names[system]}-{'arm64' if arm else 'x64'}"


def opencode_platform() -> str:
    system, arm = _arch()
    names = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}
    if system not in names:
        raise RuntimeError(t("unsupported_platform", system=system, machine=platform.machine()))
    return f"{names[system]}-{'arm64' if arm else 'x64'}"


def exe(name: str) -> str:
    return name + ".exe" if platform.system() == "Windows" else name


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def pick_port(preferred: int) -> int:
    for port in range(preferred, preferred + 50):
        if port_is_free(port):
            return port
    raise RuntimeError(t("no_free_port"))


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    if platform.system() == "Windows":
        # os.kill(pid, 0) on Windows terminates the process, so ask tasklist instead.
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", str(path)])
    elif system == "Windows":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", str(path)], stderr=subprocess.DEVNULL)


# ───────────────────────────── state ─────────────────────────────

def read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_state(state: dict) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def saved_profile() -> Profile | None:
    return PROFILES.get(read_state().get("profile", ""))


# ───────────────────────────── network ─────────────────────────────

def _net_reason(error: BaseException, sec: int = NET_CHECK_TIMEOUT) -> str:
    """Turns a network exception into a human sentence."""
    reason = getattr(error, "reason", error)
    if isinstance(error, urllib.error.HTTPError):
        return t("net_reason.http", code=error.code)
    if isinstance(reason, (socket.timeout, TimeoutError)) or "timed out" in str(reason):
        return t("net_reason.timeout", sec=sec)
    if isinstance(reason, socket.gaierror):
        return t("net_reason.dns")
    if isinstance(reason, ssl.SSLError):
        return t("net_reason.ssl")
    if isinstance(reason, (ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError)):
        return t("net_reason.refused")
    return t("net_reason.other", detail=str(reason))


def network_error(url: str, error: BaseException, sec: int = NET_CHECK_TIMEOUT) -> NetworkError:
    host = urllib.parse.urlparse(getattr(error, "url", None) or url).hostname or url
    if isinstance(error, urllib.error.HTTPError) and error.code in (404, 410):
        return NetworkError(t("net_missing", host=host, url=url))
    return NetworkError(f"{t('net_fail_title', host=host)}\n{_net_reason(error, sec)}\n{t('net_advice')}")


def _open(url: str, offset: int = 0, timeout: int = STALL_TIMEOUT):
    headers = {"User-Agent": "local-ai-starter"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)


def check_network(urls: list[str]) -> None:
    """Fetches the first byte of every pending download (redirects and CDNs included)."""
    if DRY_RUN or not urls:
        return
    say(dim(t("net_check")))
    for url in urls:
        host = urllib.parse.urlparse(url).hostname
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "local-ai-starter", "Range": "bytes=0-0"})
            with urllib.request.urlopen(request, timeout=NET_CHECK_TIMEOUT) as response:
                response.read(1)
        except (urllib.error.URLError, OSError) as error:
            raise network_error(url, error) from None
        say("  " + ok(t("net_ok", host=host)))


def _progress(done: int, total: int, started: float, base: int) -> None:
    elapsed = max(time.time() - started, 0.001)
    speed = (done - base) / elapsed
    if not total:
        print(f"\r  {done / 2**20:8.1f} {t('mb')}  {speed / 2**20:5.1f} {t('mbs')}", end="", flush=True)
        return
    share = done / total
    width = 24
    filled = int(width * share)
    bar = ("█" * filled + "░" * (width - filled)) if ANSI else ("#" * filled + "-" * (width - filled))
    left = (total - done) / speed if speed > 0 else 0
    eta = f"{int(left // 60)}:{int(left % 60):02d}" if speed > 0 else "--:--"
    if total > 2**30:
        size = f"{done / 2**30:.2f}/{total / 2**30:.2f} {t('gb')}"
    else:
        size = f"{done / 2**20:.0f}/{total / 2**20:.0f} {t('mb')}"
    print(f"\r  {bar} {share * 100:5.1f}%  {size}  {speed / 2**20:5.1f} {t('mbs')}  {t('eta')} {eta} ",
          end="", flush=True)


def download(url: str, target: Path, sha256: str | None, name: str) -> None:
    """Resumable download into target.part, verified (when a hash is known), then renamed to target."""
    say(t("downloading", name=name))
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    attempt = 0
    while True:
        offset = part.stat().st_size if part.exists() else 0
        try:
            with _open(url, offset) as response:
                if offset and response.status != 206:
                    offset = 0  # server ignored Range: start over
                length = int(response.headers.get("Content-Length") or 0)
                total = offset + length if length else 0
                done, started, drawn = offset, time.time(), 0.0
                with part.open("ab" if offset else "wb") as out:
                    while True:
                        chunk = response.read(1 << 20)
                        if not chunk:
                            break
                        out.write(chunk)
                        done += len(chunk)
                        attempt = 0  # progress resets the retry budget
                        if time.time() - drawn > 0.3 or done == total:
                            drawn = time.time()
                            _progress(done, total, started, offset)
            say("")
            if total and done < total:
                raise ConnectionResetError("incomplete")
            break
        except urllib.error.HTTPError as error:
            if error.code == 416 and offset:  # already complete
                break
            raise network_error(url, error) from None
        except (urllib.error.URLError, OSError) as error:
            say("")
            attempt += 1
            if attempt >= DOWNLOAD_ATTEMPTS:
                raise network_error(url, error, STALL_TIMEOUT) from None
            pause = min(5 * attempt, 20)
            say(dim(t("download_retry", reason=_net_reason(error, STALL_TIMEOUT), sec=pause, i=attempt + 1, n=DOWNLOAD_ATTEMPTS)))
            time.sleep(pause)
    if sha256:
        say(dim(t("verifying")))
        if sha256_of(part) != sha256:
            part.unlink(missing_ok=True)
            raise RuntimeError(t("hash_bad", name=name))
    part.replace(target)
    if sha256:
        say(ok(t("hash_ok")))


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def extract(archive: Path, target: Path) -> None:
    """Unpacks into target, dropping a shared top folder and refusing paths outside target.

    Symlinks matter: llama.cpp tarballs link libX.0.dylib -> libX.0.9.0.dylib, and the
    server does not start without them.
    """
    target.mkdir(parents=True, exist_ok=True)
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            files = [(m.filename, m) for m in zf.infolist() if not m.is_dir()]
            _write_members(files, [], lambda m: zf.open(m), target)
    else:
        with tarfile.open(archive) as tf:
            members = tf.getmembers()
            files = [(m.name, m) for m in members if m.isfile()]
            links = [(m.name, m.linkname) for m in members if m.issym()]
            _write_members(files, links, lambda m: tf.extractfile(m), target)


def _write_members(files, links, opener, target: Path) -> None:
    names = [name for name, _ in files] + [name for name, _ in links]
    firsts = {name.split("/")[0] for name in names}
    strip = len(firsts) == 1 and all("/" in name for name in names)
    root = target.resolve()

    def destination_of(name: str) -> Path:
        relative = Path(*name.split("/")[1:]) if strip else Path(name)
        destination = (target / relative).resolve()
        if root not in destination.parents:
            raise RuntimeError(f"Unsafe path in archive: {name}")
        return destination

    for name, member in files:
        destination = destination_of(name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with opener(member) as source, destination.open("wb") as out:
            shutil.copyfileobj(source, out)
        try:
            mode = getattr(member, "mode", None)
            if mode:
                destination.chmod(mode & 0o777)
        except OSError:
            pass
    for name, link in links:
        destination = destination_of(name)
        if root not in (destination.parent / link).resolve().parents:
            raise RuntimeError(f"Unsafe link in archive: {name} -> {link}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink() or destination.exists():
            destination.unlink()
        os.symlink(link, destination)


def make_executable(path: Path) -> None:
    if platform.system() != "Windows" and path.exists():
        path.chmod(path.stat().st_mode | 0o111)  # zip archives do not keep the exec bit


# ───────────────────────────── components ─────────────────────────────

def is_apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine().lower() == "arm64"


def server_binary() -> Path | None:
    path = LLAMA_DIR / exe("llama-server")
    return path if path.exists() else None


def opencode_binary() -> Path | None:
    path = OPENCODE_DIR / exe("opencode")
    return path if path.exists() else None


def mlx_python() -> Path:
    return MLX_DIR / "venv" / "bin" / "python"


def mlx_installed() -> bool:
    marker = MLX_DIR / ".installed"
    return marker.exists() and marker.read_text().strip() == MLX_LM_VERSION and mlx_python().exists()


def engine_installed(engine: str) -> bool:
    return mlx_installed() if engine == "mlx" else server_binary() is not None


def llama_asset() -> tuple[str, str]:
    plat = llama_platform()
    ext = "zip" if plat.startswith("win") else "tar.gz"
    return LLAMA_URL.format(build=LLAMA_BUILD, plat=plat, ext=ext), plat


def opencode_asset() -> tuple[str, str]:
    plat = opencode_platform()
    ext = "tar.gz" if plat.startswith("linux") else "zip"
    return OPENCODE_URL.format(ver=OPENCODE_VERSION, plat=plat, ext=ext), plat


def _install_archive(url: str, sha256: str, target: Path, name: str) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    archive = ROOT / ("download-" + url.rsplit("/", 1)[-1])
    download(url, archive, sha256, name)
    say(dim(t("extracting")))
    if target.exists():
        shutil.rmtree(target)
    extract(archive, target)
    archive.unlink(missing_ok=True)


def install_llama() -> None:
    url, plat = llama_asset()
    if DRY_RUN:
        say(t("dry_run_would", what=f"download {url} → {LLAMA_DIR}"))
        return
    _install_archive(url, LLAMA_SHA256[plat], LLAMA_DIR, f"llama.cpp {LLAMA_BUILD}")
    for path in LLAMA_DIR.iterdir():
        if path.is_file() and path.name.startswith("llama"):
            make_executable(path)
    if not server_binary():
        raise RuntimeError(t("no_server_binary"))


def uv_env() -> dict:
    """uv, its Python and its caches all stay inside engines/mlx/."""
    return dict(os.environ, UV_PYTHON_INSTALL_DIR=str(MLX_DIR / "python"), UV_CACHE_DIR=str(MLX_DIR / "cache"),
                UV_PYTHON_PREFERENCE="only-managed", UV_NO_CONFIG="1", UV_NO_PROGRESS="0")


def install_mlx() -> None:
    """uv (pinned) → Python 3.12 managed by uv → venv with mlx-lm (pinned version)."""
    if DRY_RUN:
        say(t("dry_run_would", what=f"install uv {UV_VERSION}, Python {MLX_PYTHON}, mlx-lm {MLX_LM_VERSION} → {MLX_DIR}"))
        return
    uv = MLX_DIR / "uv" / "uv"
    if not uv.exists():
        _install_archive(UV_URL, UV_SHA256, MLX_DIR / "uv", f"uv {UV_VERSION}")
        make_executable(uv)
    commands = [[str(uv), "venv", str(MLX_DIR / "venv"), "--python", MLX_PYTHON, "--clear"],
                [str(uv), "pip", "install", "--python", str(mlx_python()), f"mlx-lm=={MLX_LM_VERSION}"]]
    for command in commands:
        say(dim("$ " + " ".join(command)))
        try:
            subprocess.run(command, env=uv_env(), check=True)
        except (subprocess.CalledProcessError, OSError):
            raise RuntimeError(t("mlx_failed")) from None
    (MLX_DIR / ".installed").write_text(MLX_LM_VERSION + "\n")


def install_opencode() -> None:
    url, plat = opencode_asset()
    if DRY_RUN:
        say(t("dry_run_would", what=f"download {url} → {OPENCODE_DIR}"))
        return
    _install_archive(url, OPENCODE_SHA256[plat], OPENCODE_DIR, f"OpenCode {OPENCODE_VERSION}")
    make_executable(OPENCODE_DIR / exe("opencode"))
    if not opencode_binary():
        raise RuntimeError(t("no_opencode_binary"))


def mlx_files(profile: Profile) -> list[dict]:
    """File list of an MLX repo at the pinned commit (LFS files carry their SHA-256)."""
    try:
        _, files = http_json(profile.url, timeout=NET_CHECK_TIMEOUT)
    except (urllib.error.URLError, OSError) as error:
        raise network_error(profile.url, error) from None
    skip = {".gitattributes", "README.md"}
    return [f for f in files if f.get("type") == "file" and f["path"] not in skip]


def install_model(profile: Profile) -> None:
    if DRY_RUN:
        say(t("dry_run_would", what=f"download {profile.url} → {profile.path}"))
        return
    if profile.engine == "gguf":
        download(profile.url, profile.path, profile.sha256, profile.file)
        return
    files = mlx_files(profile)
    root = profile.path.resolve()
    for index, item in enumerate(files, 1):
        target = profile.path / item["path"]
        if root not in target.resolve().parents:
            raise RuntimeError(f"Unsafe path in repository: {item['path']}")
        if target.exists() and target.stat().st_size == item.get("size"):
            continue
        url = f"https://huggingface.co/{profile.repo}/resolve/{profile.file}/{item['path']}"
        sha256 = (item.get("lfs") or {}).get("oid")
        download(url, target, sha256, t("file_n", name=item["path"], i=index, n=len(files)))
    (profile.path / ".complete").write_text(profile.file + "\n")


# ───────────────────────────── server ─────────────────────────────

def http_json(url: str, payload: dict | None = None, timeout: int = 10, headers: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json",
                                                              "User-Agent": "local-ai-starter", **(headers or {})})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode() or "{}")


def is_healthy(port: int) -> bool:
    try:
        return http_json(f"http://127.0.0.1:{port}/health", timeout=3)[0] == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


def log_tail() -> str:
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        return lines[-1][:110] if lines else ""
    except OSError:
        return ""


def context_size() -> int:
    """OpenCode's system prompt and tools take ~10k tokens, so 32k is the comfortable minimum."""
    ram = ram_gb()
    if ram and ram < 12:
        return 16384
    if ram and ram >= 48:
        return 65536
    return 32768


def api_model(profile: Profile) -> str:
    # mlx_lm.server treats any other model name as a new model to load; its CLI model is "default_model".
    return "default_model" if profile.engine == "mlx" else profile.key


def server_command(profile: Profile, port: int, ctx: int) -> list[str]:
    if profile.engine == "mlx":
        return [str(mlx_python()), "-m", "mlx_lm.server", "--model", str(profile.path),
                "--host", "127.0.0.1", "--port", str(port), "--max-tokens", "8192"]
    binary = server_binary() or LLAMA_DIR / exe("llama-server")
    return [str(binary), "-m", str(profile.path), "--alias", profile.key, "-c", str(ctx),
            "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0", "--jinja",
            "--host", "127.0.0.1", "--port", str(port)]


def start_server(profile: Profile, port: int) -> dict:
    ctx = context_size()
    command = server_command(profile, port, ctx)
    state = read_state()
    fresh = {"port": port, "profile": profile.key, "engine": profile.engine, "model_id": api_model(profile),
             "ctx": ctx, "started_at": int(time.time())}
    if DRY_RUN:
        say(t("dry_run_would", what="run " + " ".join(command)))
        return dict(fresh, pid=0)
    options: dict = {}
    if platform.system() == "Windows":
        options["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    env = dict(os.environ)
    workdir = LLAMA_DIR
    if profile.engine == "mlx":
        workdir = MLX_DIR
        env.update(HF_HOME=str(MLX_DIR / "hf"), HF_HUB_OFFLINE="1")  # the model is local, never fetch
    with LOG_FILE.open("ab") as log:
        log.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(command)}\n".encode())
        log.flush()
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   cwd=str(workdir), env=env, **options)
    state.update(fresh, pid=process.pid)
    write_state(state)
    return state


def wait_ready(state: dict) -> None:
    if DRY_RUN:
        return
    say(dim(t("starting_server")))
    started, last_note, limit = time.time(), 0.0, 900
    while time.time() - started < limit:
        if is_healthy(state["port"]):
            break
        if not pid_alive(state["pid"]):
            raise RuntimeError(t("server_stopped", line=log_tail(), log=LOG_FILE))
        if time.time() - last_note > 10:
            last_note = time.time()
            say(dim(f"  [{int(time.time() - started)} s] {log_tail()}"))
        time.sleep(1)
    else:
        raise RuntimeError(t("server_timeout", min=limit // 60, log=LOG_FILE))
    say(dim(t("server_test")))
    status, body = http_json(
        f"http://127.0.0.1:{state['port']}/v1/chat/completions",
        {"model": state.get("model_id", state["profile"]), "messages": [{"role": "user", "content": "Say OK"}],
         "max_tokens": 16},
        timeout=300,
    )
    if status != 200 or not body.get("choices"):
        raise RuntimeError(t("server_no_answer", log=LOG_FILE))
    say(ok(t("server_ok")))


def running_state() -> dict | None:
    state = read_state()
    if state.get("pid") and pid_alive(state["pid"]):
        return state
    return None


def stop_server() -> None:
    state = read_state()
    pid = state.get("pid")
    if pid and pid_alive(pid):
        say(t("stopping", pid=pid))
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        else:
            try:
                os.killpg(pid, signal.SIGTERM)
            except OSError:
                os.kill(pid, signal.SIGTERM)
        for _ in range(20):
            if not pid_alive(pid):
                break
            time.sleep(0.5)
    else:
        say(t("no_server"))
    state.pop("pid", None)
    if STATE_FILE.exists():
        write_state(state)


def bring_up(profile: Profile) -> dict:
    existing = running_state()
    if existing and existing.get("profile") == profile.key and is_healthy(existing["port"]):
        say(ok(t("server_running")))
        return existing
    if existing:
        stop_server()
    port = pick_port(DEFAULT_PORT)
    if port != DEFAULT_PORT:
        say(t("port_busy", busy=DEFAULT_PORT, port=port))
    state = start_server(profile, port)
    wait_ready(state)
    return state


# ───────────────────────────── speed test ─────────────────────────────

def _stream_completion(port: int, model_id: str, prompt: str, max_tokens: int) -> dict:
    """Streams one answer; returns prompt/answer token counts, time to first token and generation time."""
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
               "temperature": 0, "stream": True, "stream_options": {"include_usage": True}}
    request = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
                                     data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    started, first, chunks, usage = time.time(), None, 0, {}
    with urllib.request.urlopen(request, timeout=900) as response:
        for raw in response:
            line = raw.decode(errors="ignore").strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            try:
                event = json.loads(line[5:])
            except ValueError:
                continue
            usage = event.get("usage") or usage
            for choice in event.get("choices") or []:
                delta = choice.get("delta") or {}
                if any(delta.get(k) for k in ("content", "reasoning_content", "reasoning")):
                    if first is None:
                        first = time.time()
                    chunks += 1
    finished = time.time()
    first = first or finished
    return {"prompt_tokens": usage.get("prompt_tokens") or 0,
            "answer_tokens": usage.get("completion_tokens") or chunks,
            "ttft": first - started, "gen_time": max(finished - first, 1e-6)}


def chip_name() -> str:
    try:
        if platform.system() == "Darwin":
            return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                                  text=True, timeout=3).stdout.strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()


def speed_test(profile: Profile) -> None:
    profile = ensure_installed(profile)
    state = bring_up(profile)
    say("\n" + bold(t("bench_title", model=profile.key, engine=ENGINE_NAMES[profile.engine])))
    say(dim(t("bench_running")))
    if DRY_RUN:
        return
    numbers = ", ".join(str(n) for n in range(1, 1500))
    long_prompt = f"Here is a list: {numbers}. How many items are in the list? Answer with one number."
    short_prompt = "Write a short story (about 200 words) about a robot that learns to paint."
    try:
        _stream_completion(state["port"], state["model_id"], "Say OK", 8)  # warm-up
        prefill = _stream_completion(state["port"], state["model_id"], long_prompt, 16)
        gen = _stream_completion(state["port"], state["model_id"], short_prompt, 300)
    except (urllib.error.URLError, OSError, ValueError) as error:
        say(fail(t("bench_fail", error=error)))
        return
    prefill_tps = prefill["prompt_tokens"] / prefill["ttft"] if prefill["ttft"] else 0
    gen_tps = (gen["answer_tokens"] - 1) / gen["gen_time"] if gen["answer_tokens"] > 1 else 0
    say(ok(t("bench_prefill", tps=prefill_tps, n=prefill["prompt_tokens"], ttft=prefill["ttft"])))
    say(ok(t("bench_gen", tps=gen_tps, n=gen["answer_tokens"])))
    new_file = not BENCH_FILE.exists()
    with BENCH_FILE.open("a", encoding="utf-8") as out:
        if new_file:
            out.write("date,engine,model,chip,ram_gb,context,prompt_tokens,first_token_s,prefill_tok_s,"
                      "answer_tokens,generation_tok_s\n")
        ram = ram_gb() or 0
        out.write(f"{time.strftime('%Y-%m-%d %H:%M')},{profile.engine},{profile.key},\"{chip_name()}\",{ram:.0f},"
                  f"{state.get('ctx', '')},{prefill['prompt_tokens']},{prefill['ttft']:.2f},{prefill_tps:.1f},"
                  f"{gen['answer_tokens']},{gen_tps:.1f}\n")
    say(dim(t("bench_saved", file=BENCH_FILE)))


# ───────────────────────────── OpenCode ─────────────────────────────

def write_opencode_config(profile: Profile, port: int, ctx: int) -> None:
    model_id = api_model(profile)
    config = {
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "share": "disabled",
        "provider": {"local-ai-starter": {
            "npm": "@ai-sdk/openai-compatible",
            "name": f"Local AI Starter ({ENGINE_NAMES[profile.engine]})",
            "options": {"baseURL": f"http://127.0.0.1:{port}/v1"},
            "models": {model_id: {"name": f"{profile.key} ({ENGINE_NAMES[profile.engine]}, local)",
                                  "tool_call": True, "limit": {"context": ctx, "output": 4096}}},
        }},
        "model": f"local-ai-starter/{model_id}",
        "small_model": f"local-ai-starter/{model_id}",
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    OPENCODE_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare_workspace() -> None:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    if any(WORKSPACE_DIR.iterdir()):
        return  # never overwrite the user's files
    html = (f'<!doctype html>\n<html lang="{LANG}"><head><meta charset="utf-8"><title>{t("demo_title")}</title></head>\n'
            f'<body><h1>{t("demo_heading")}</h1><p>{t("demo_text")}</p></body></html>\n')
    (WORKSPACE_DIR / "index.html").write_text(html, encoding="utf-8")


def opencode_env() -> dict:
    """Points OpenCode at our config and keeps its data, auth and caches inside local-ai/."""
    env = dict(os.environ, OPENCODE_CONFIG=str(OPENCODE_CONFIG), OPENCODE_DISABLE_AUTOUPDATE="1")
    for name, sub in (("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                      ("XDG_STATE_HOME", "state"), ("XDG_CACHE_HOME", "cache")):
        path = OPENCODE_HOME / sub
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    return env


def launch_opencode(profile: Profile, state: dict) -> None:
    write_opencode_config(profile, state["port"], state.get("ctx", context_size()))
    prepare_workspace()
    say("\n" + bold(t("opencode_intro", dir=WORKSPACE_DIR)))
    say(t("opencode_tips", example=t("opencode_example")))
    binary = opencode_binary()
    if DRY_RUN:
        say(t("dry_run_would", what=f"run {OPENCODE_DIR / exe('opencode')} in {WORKSPACE_DIR}"))
        return
    if not binary:
        raise RuntimeError(t("opencode_missing"))
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ctrl+C belongs to OpenCode now
    try:
        subprocess.run([str(binary)], cwd=str(WORKSPACE_DIR), env=opencode_env())
    finally:
        signal.signal(signal.SIGINT, previous)


# ───────────────────────────── updates ─────────────────────────────

def _version_tuple(text: str) -> tuple:
    """'v2.1.0' -> (2, 1, 0); anything unparsable -> () which never counts as newer."""
    try:
        return tuple(int(part) for part in text.strip().lstrip("vV").split("."))
    except ValueError:
        return ()


def check_for_update(argv: list[str]) -> None:
    """Asks GitHub for the latest release; offers it if it is newer. Never blocks the wizard."""
    if DRY_RUN or "--no-update" in argv or os.environ.get("LOCAL_AI_STARTER_NO_UPDATE") == "1":
        return
    try:
        _, release = http_json(UPDATE_API, timeout=UPDATE_TIMEOUT, headers={"Accept": "application/vnd.github+json"})
        tag = str(release.get("tag_name") or "")
    except (urllib.error.URLError, OSError, ValueError, AttributeError):
        say(dim(t("update_check_failed")))
        return
    latest = _version_tuple(tag)
    if not latest or latest <= _version_tuple(VERSION) or read_state().get("skipped_version") == tag:
        return
    say("\n" + bold(t("update_available", new=tag.lstrip("vV"), old=VERSION)))
    for line in str(release.get("body") or "").strip().splitlines()[:15]:
        say("  " + line.rstrip())
    choice = ask(t("update_question"), [t("update_now"), t("update_later"), t("update_skip")], 1)
    if choice == 2:
        return
    if choice == 3:
        state = read_state()
        state["skipped_version"] = tag
        write_state(state)
        return
    if apply_update(tag):
        restart(argv)


def apply_update(tag: str) -> bool:
    try:
        if (APP_DIR / ".git").exists() and shutil.which("git"):
            return _update_git(tag)
        return _update_zip(tag)
    except (urllib.error.URLError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        say(fail(t("update_failed", error=error)))
        return False


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(APP_DIR), *args], capture_output=True, text=True, timeout=180)


def _update_git(tag: str) -> bool:
    """Fast-forwards to the release tag (not to main), and only on a clean tree."""
    status = _git("status", "--porcelain")
    if status.returncode or status.stdout.strip():
        say(t("update_local_changes", tag=tag))
        return False
    for args in (("fetch", "--tags", "--force", "origin"), ("merge", "--ff-only", f"refs/tags/{tag}")):
        say(dim("$ git " + " ".join(args)))
        result = _git(*args)
        if result.returncode:
            say(dim((result.stderr or result.stdout).strip()[-400:]))
            say(t("update_local_changes", tag=tag))
            return False
    say(ok(t("update_done", version=tag.lstrip("vV"))))
    return True


def _update_zip(tag: str) -> bool:
    """Downloads the release archive and replaces changed wizard files; local-ai/ is never touched."""
    ROOT.mkdir(parents=True, exist_ok=True)
    archive, staging = ROOT / "download-update.zip", ROOT / "update-new"
    for leftover in (archive, archive.with_name(archive.name + ".part")):
        leftover.unlink(missing_ok=True)  # never resume a different release
    download(UPDATE_ZIP.format(tag=tag), archive, None, f"Local AI Starter {tag}")
    if staging.exists():
        shutil.rmtree(staging)
    extract(archive, staging)
    archive.unlink(missing_ok=True)
    if not (staging / "local_ai_starter.py").is_file():
        shutil.rmtree(staging, ignore_errors=True)
        raise RuntimeError(t("update_bad_archive"))
    for source in sorted(staging.rglob("*")):
        relative = source.relative_to(staging)
        if not source.is_file() or relative.parts[0] in ("local-ai", ".git"):
            continue
        target = APP_DIR / relative
        if target.is_file() and target.read_bytes() == source.read_bytes():
            continue  # unchanged: leave it alone (matters for a .bat that is running right now)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".update-tmp")
        shutil.copyfile(source, temporary)
        temporary.replace(target)
    for name in ("RunMe.command", "RunMe.sh"):
        make_executable(APP_DIR / name)
    shutil.rmtree(staging, ignore_errors=True)
    say(ok(t("update_done", version=tag.lstrip("vV"))))
    return True


def restart(argv: list[str]) -> None:
    """Runs the freshly installed wizard with the same arguments; --no-update prevents a loop."""
    say(dim(t("update_restarting")))
    command = [sys.executable, str(APP_DIR / "local_ai_starter.py")]
    command += [arg for arg in argv if arg != "--no-update"] + ["--no-update"]
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        code = subprocess.call(command)
    finally:
        signal.signal(signal.SIGINT, previous)
    raise SystemExit(code)


# ───────────────────────────── scenarios ─────────────────────────────

def migrate_layout() -> None:
    """Moves files from the v2 layout (bin/, models/<family>/) so nothing is downloaded twice."""
    if DRY_RUN or not ROOT.exists():
        return
    old_bin = ROOT / "bin"
    if old_bin.is_dir() and not LLAMA_DIR.exists():
        LLAMA_DIR.parent.mkdir(parents=True, exist_ok=True)
        old_bin.rename(LLAMA_DIR)
    if MODELS_DIR.is_dir():
        for folder in list(MODELS_DIR.iterdir()):
            if folder.is_dir() and folder.name not in ("gguf", "mlx"):
                target = MODELS_DIR / "gguf" / folder.name
                target.mkdir(parents=True, exist_ok=True)
                for item in folder.iterdir():
                    if not (target / item.name).exists():
                        item.rename(target / item.name)
                if not any(folder.iterdir()):
                    folder.rmdir()


def show_system() -> float | None:
    ram = ram_gb()
    say("\n" + bold(t("system_check")))
    say(f"  {t('system')}: {platform.system()} {platform.machine()}")
    memory = f"{ram:.0f} {t('gb')}" if ram else t("unknown")
    say(f"  {t('memory')}: {memory}")
    say(f"  {t('disk_free')}: {free_gb():.0f} {t('gb')}")
    return ram


def choose_engine() -> str:
    if not is_apple_silicon():
        return "gguf"
    engines = ["gguf", "mlx"]
    options = []
    for engine in engines:
        label = t("engine." + engine)
        if engine_installed(engine):
            label += " ✓"
        options.append(label)
    return engines[ask(t("pick_engine"), options, 1) - 1]


def choose_profile() -> Profile:
    ram = show_system()
    engine = choose_engine()
    candidates = [p for p in PROFILES.values() if p.engine == engine]
    fitting = [p for p in candidates if p.min_ram_gb <= (ram or 16)]
    recommended = fitting[-1] if fitting else candidates[0]
    ordered = [recommended] + [p for p in candidates if p is not recommended]
    options = []
    for profile in ordered:
        label = f"{t('model.' + profile.base)} · {profile.quant} · {size_text(profile.size / 2**30)}"
        if profile.installed:
            label += " ✓"
        if profile is recommended:
            label += f" ({t('recommended')})"
        options.append(label)
    profile = ordered[ask(t("pick_model"), options, 1) - 1]
    if ram and ram < profile.min_ram_gb:
        say(t("low_ram", need=profile.min_ram_gb, have=ram))
        if not yes_no(t("continue_anyway"), False):
            raise Cancelled()
    return profile


def engine_task(engine: str) -> tuple:
    if engine == "mlx":
        return (t("plan_mlx", uv=UV_VERSION, py=MLX_PYTHON, ver=MLX_LM_VERSION), MLX_SIZE_MB / 1024,
                [UV_URL, MLX_PYPI_URL], install_mlx)
    return (t("plan_engine", build=LLAMA_BUILD), LLAMA_SIZE_MB / 1024, [llama_asset()[0]], install_llama)


def ensure_installed(profile: Profile | None) -> Profile:
    """Asks only what is still unknown, installs only what is still missing."""
    if profile is None:
        profile = choose_profile()
    tasks = []
    if not engine_installed(profile.engine) or DRY_RUN:
        tasks.append(engine_task(profile.engine))
    if not profile.installed or DRY_RUN:
        tasks.append((t("plan_model", file=profile.label_path), profile.size / 2**30,
                      [profile.url], lambda: install_model(profile)))
    if not opencode_binary() or DRY_RUN:
        tasks.append((t("plan_opencode", ver=OPENCODE_VERSION), OPENCODE_SIZE_MB / 1024,
                      [opencode_asset()[0]], install_opencode))
    if tasks:
        total = sum(size for _, size, _, _ in tasks)
        say("\n" + bold(t("plan")))
        for index, (title, size, _, _) in enumerate(tasks, 1):
            say(f"  {index}. {title} · {size_text(size)}")
        say(dim("  " + t("plan_total", gb=total, root=ROOT)))
        if free_gb() < total + 1:
            say(fail(t("low_disk", need=total + 1, have=free_gb())))
            if not yes_no(t("continue_anyway"), False):
                raise Cancelled()
        if not yes_no(t("start"), True):
            raise Cancelled()
        check_network([url for _, _, urls, _ in tasks for url in urls])
        for index, (title, _, _, action) in enumerate(tasks, 1):
            step(index, len(tasks), title)
            action()
    state = read_state()
    state["profile"] = profile.key
    write_state(state)
    return profile


def open_chat(profile: Profile) -> None:
    if profile.engine == "mlx":
        say(t("chat_mlx"))
        return
    port = bring_up(profile)["port"]
    url = f"http://127.0.0.1:{port}"
    say(t("chat_url", url=url))
    if not DRY_RUN:
        webbrowser.open(url)


def show_status() -> None:
    alive = running_state()
    profile = saved_profile()
    installed = lambda flag: t("installed") if flag else t("not_installed")  # noqa: E731
    say(f"\n{t('status_root')}: {ROOT}")
    say(f"llama.cpp {LLAMA_BUILD}: {installed(server_binary())}")
    if is_apple_silicon():
        say(f"MLX (mlx-lm {MLX_LM_VERSION}): {installed(mlx_installed())}")
    say(f"OpenCode {OPENCODE_VERSION}: {installed(opencode_binary())}")
    say(f"{t('status_server')}: {t('running_on', port=alive['port']) if alive else t('not_running')}")
    say(f"{t('status_model')}: {f'{profile.key} → {profile.path}' if profile else '—'}")
    say(f"{t('status_log')}: {LOG_FILE}")
    if BENCH_FILE.exists():
        say(f"{t('status_bench')}: {BENCH_FILE}")
    if LOG_FILE.exists():
        say(f"{t('status_last')}: {log_tail()}")


def _size_of(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def model_entries() -> list[Path]:
    """GGUF files (and unfinished .part files) plus MLX model folders."""
    entries = []
    gguf = MODELS_DIR / "gguf"
    if gguf.is_dir():
        entries += sorted(p for p in gguf.glob("*/*") if p.name.endswith((".gguf", ".gguf.part")))
    mlx = MODELS_DIR / "mlx"
    if mlx.is_dir():
        entries += sorted(p for p in mlx.glob("*/*") if p.is_dir())
    return entries


def manage_models() -> None:
    while True:
        entries = model_entries()
        say("\n" + bold(t("models_title", dir=MODELS_DIR)))
        if not entries:
            say("  " + t("models_none"))
            return
        labels, total = [], 0
        for path in entries:
            size = _size_of(path)
            total += size
            label = str(path.relative_to(MODELS_DIR))
            unfinished = path.name.endswith(".part") or (path.is_dir() and not (path / ".complete").exists())
            if unfinished:
                label += f" ({t('models_incomplete')})"
            labels.append(label)
            say(f"  {label}  {size_text(size / 2**30)}")
        say(dim("  " + t("models_total", gb=total / 2**30)))
        choice = ask(t("models_pick"), [t("models_back"), t("models_open")] + labels, 1)
        if choice == 1:
            return
        if choice == 2:
            open_folder(MODELS_DIR)
            continue
        path = entries[choice - 3]
        current = saved_profile()
        if running_state() and current and path in (current.path, current.path.with_name(current.path.name + ".part")):
            stop_server()
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        if path.parent.exists() and not any(path.parent.iterdir()):
            path.parent.rmdir()
        say(ok(t("models_deleted", file=path.name)))


def uninstall() -> bool:
    say("\n" + t("uninstall_warn", root=ROOT))
    if not yes_no(t("uninstall_confirm"), False):
        return False
    stop_server()
    shutil.rmtree(ROOT, ignore_errors=True)
    say(ok(t("uninstall_done")))
    return True


def run_opencode(profile: Profile | None) -> Profile:
    profile = ensure_installed(profile)
    state = bring_up(profile)
    launch_opencode(profile, state)
    return profile


def menu(profile: Profile | None) -> None:
    actions = ["stop_exit", "keep_exit", "opencode", "switch", "bench", "chat", "models", "status", "uninstall"]
    while True:
        choice = actions[ask(t("menu_title"), [t("menu." + a) for a in actions], 1) - 1]
        if choice == "stop_exit":
            stop_server()
            return
        if choice == "keep_exit":
            return
        if choice == "opencode":
            profile = run_opencode(profile)
        elif choice == "switch":
            profile = run_opencode(choose_profile())
        elif choice == "bench":
            speed_test(profile or choose_profile())
            profile = saved_profile()
        elif choice == "chat":
            profile = ensure_installed(profile)
            open_chat(profile)
        elif choice == "models":
            manage_models()
        elif choice == "status":
            show_status()
        elif choice == "uninstall" and uninstall():
            return


def main(argv: list[str]) -> int:
    try:
        banner()
        check_for_update(argv)
        migrate_layout()
        profile = saved_profile()
        if "--menu" not in argv:
            profile = run_opencode(profile)
        menu(profile)
        return 0
    except (Cancelled, KeyboardInterrupt):
        say("\n" + t("cancelled"))
        return 0
    except NetworkError as error:
        say("\n" + fail(str(error)))
        return 1
    except (RuntimeError, subprocess.CalledProcessError, urllib.error.URLError, OSError) as error:
        say("\n" + fail(t("error", error=error)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
