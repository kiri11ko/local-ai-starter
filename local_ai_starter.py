#!/usr/bin/env python3
"""Local AI Starter — мастер запуска локальной модели через llama.cpp.

Запуск без параметров:  python3 local_ai_starter.py  (или двойной клик по
«Запустить Local AI Starter.command» / «.bat»).

Всё, что скачивает и создаёт скрипт, лежит в папке ``local-ai`` рядом с ним:
движок, веса модели, журнал, учебный проект. Удалить папку = удалить всё.
Сервер слушает только 127.0.0.1. Глобальные настройки и PATH не меняются.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import webbrowser
import zipfile
from dataclasses import dataclass
from pathlib import Path

DRY_RUN = os.environ.get("LOCAL_AI_STARTER_DRY_RUN") == "1"
DEFAULT_PORT = 8080

ROOT = Path(os.environ.get("LOCAL_AI_STARTER_HOME") or (Path(__file__).resolve().parent / "local-ai"))
BIN_DIR = ROOT / "bin"
MODELS_DIR = ROOT / "models"
OPENCODE_HOME = ROOT / "opencode-home"
DEMO_DIR = ROOT / "demo-project"
STATE_FILE = ROOT / "state.json"
LOG_FILE = ROOT / "server.log"

# Закреплённая сборка llama.cpp: одна версия для всех, хеши с страницы релиза.
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
OPENCODE_INSTALL_URL = "https://opencode.ai/install"


@dataclass(frozen=True)
class Profile:
    key: str
    title: str
    purpose: str
    hf_model: str
    context: int
    download: str
    min_ram_gb: int


PROFILES = {
    "fast": Profile("fast", "Быстрый", "короткие ответы, черновики; идёт даже на скромном компьютере",
                    "Qwen/Qwen3-4B-GGUF:Q4_K_M", 8192, "около 2,5 ГБ", 8),
    "general": Profile("general", "Универсальный", "тексты, объяснения, повседневные задачи",
                       "Qwen/Qwen3-8B-GGUF:Q4_K_M", 8192, "около 5 ГБ", 16),
    "code": Profile("code", "Для программирования", "помощник в OpenCode, нужен запас памяти",
                    "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M", 32768, "около 4,7 ГБ", 16),
}


# ───────────────────────────── ввод-вывод ─────────────────────────────

class Cancelled(Exception):
    pass


def say(text: str = "") -> None:
    print(text, flush=True)


def ask(question: str, options: list[str], default: int = 1) -> int:
    """Показывает пронумерованные варианты; Enter выбирает вариант по умолчанию. Возвращает номер с 1."""
    say(f"\n{question}")
    for number, option in enumerate(options, 1):
        mark = "  ← Enter" if number == default else ""
        say(f"  {number}) {option}{mark}")
    while True:
        try:
            answer = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Cancelled()
        if not answer:
            return default
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer)
        say(f"Введите число от 1 до {len(options)} или просто Enter.")


def yes_no(question: str, default_yes: bool = True) -> bool:
    return ask(question, ["Да", "Нет"], 1 if default_yes else 2) == 1


def run_cmd(command: list[str], **kwargs) -> subprocess.CompletedProcess | None:
    say("$ " + " ".join(str(part) for part in command))
    if DRY_RUN:
        return None
    return subprocess.run(command, check=True, **kwargs)


# ───────────────────────────── система ─────────────────────────────

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


def llama_platform() -> str:
    system, machine = platform.system(), platform.machine().lower()
    arm = machine in {"arm64", "aarch64"}
    if system == "Darwin":
        return "macos-arm64" if arm else "macos-x64"
    if system == "Linux":
        return "ubuntu-arm64" if arm else "ubuntu-x64"
    if system == "Windows":
        return "win-cpu-arm64" if arm else "win-cpu-x64"
    raise RuntimeError(f"Платформа {system} не поддерживается.")


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
    raise RuntimeError("Не нашёл свободный порт рядом с 8080.")


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    if platform.system() == "Windows":
        # os.kill(pid, 0) на Windows убивает процесс, поэтому спрашиваем tasklist.
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# ───────────────────────────── состояние ─────────────────────────────

def read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def write_state(state: dict) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


# ───────────────────────────── llama.cpp ─────────────────────────────

def server_binary() -> Path | None:
    name = "llama-server.exe" if platform.system() == "Windows" else "llama-server"
    path = BIN_DIR / name
    return path if path.exists() else None


def download(url: str, target: Path) -> None:
    say(f"Скачиваю {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "local-ai-starter"})
    with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as out:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / 2**20:6.1f} / {total / 2**20:.1f} МБ ({done * 100 // total}%)", end="", flush=True)
    say("")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def extract(archive: Path, target: Path) -> None:
    """Распаковывает архив в target, убирая общую верхнюю папку, с защитой от выхода за пределы target."""
    target.mkdir(parents=True, exist_ok=True)
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            names = [(m.filename, m) for m in zf.infolist() if not m.is_dir()]
            opener = lambda m: zf.open(m)
            _write_members(names, opener, target)
    else:
        with tarfile.open(archive) as tf:
            names = [(m.name, m) for m in tf.getmembers() if m.isfile()]
            opener = lambda m: tf.extractfile(m)
            _write_members(names, opener, target)
    # tar хранит режим доступа, zip — нет; llama-server на POSIX обязан быть исполняемым
    if platform.system() != "Windows":
        for path in target.iterdir():
            if path.is_file() and path.name.startswith("llama"):
                path.chmod(path.stat().st_mode | 0o111)


def _write_members(items, opener, target: Path) -> None:
    firsts = {name.split("/")[0] for name, _ in items}
    strip = len(firsts) == 1 and all("/" in name for name, _ in items)
    for name, member in items:
        relative = Path(*name.split("/")[1:]) if strip else Path(name)
        destination = (target / relative).resolve()
        if target.resolve() not in destination.parents:
            raise RuntimeError(f"Небезопасный путь в архиве: {name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with opener(member) as source, destination.open("wb") as out:
            shutil.copyfileobj(source, out)
        try:
            mode = getattr(member, "mode", None)
            if mode:
                destination.chmod(mode & 0o777)
        except OSError:
            pass


def install_llama() -> None:
    if server_binary():
        return
    plat = llama_platform()
    ext = "zip" if plat.startswith("win") else "tar.gz"
    url = LLAMA_URL.format(build=LLAMA_BUILD, plat=plat, ext=ext)
    if DRY_RUN:
        say(f"[dry-run] скачал бы {url} в {BIN_DIR}")
        return
    ROOT.mkdir(parents=True, exist_ok=True)
    archive = ROOT / f"llama.{ext}"
    download(url, archive)
    if sha256_of(archive) != LLAMA_SHA256[plat]:
        archive.unlink(missing_ok=True)
        raise RuntimeError("Контрольная сумма архива llama.cpp не совпала — файл удалён. Повторите попытку.")
    say("Контрольная сумма совпала. Распаковываю…")
    if BIN_DIR.exists():
        shutil.rmtree(BIN_DIR)
    extract(archive, BIN_DIR)
    archive.unlink(missing_ok=True)
    if not server_binary():
        raise RuntimeError("В архиве нет llama-server — возможно, сборка изменила состав.")


# ───────────────────────────── сервер ─────────────────────────────

def http_json(url: str, payload: dict | None = None, timeout: int = 10):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
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


def start_server(profile: Profile, port: int) -> dict:
    binary = server_binary()
    if DRY_RUN:
        say(f"[dry-run] запустил бы llama-server -hf {profile.hf_model} -c {profile.context} --jinja --port {port}")
        return {"pid": 0, "port": port, "profile": profile.key}
    if not binary:
        raise RuntimeError("Движок не установлен.")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    command = [str(binary), "-hf", profile.hf_model, "--alias", profile.key, "-c", str(profile.context),
               "--jinja", "--host", "127.0.0.1", "--port", str(port)]
    env = dict(os.environ, LLAMA_CACHE=str(MODELS_DIR))
    options: dict = {}
    if platform.system() == "Windows":
        options["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    with LOG_FILE.open("ab") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env,
                                   cwd=str(BIN_DIR), **options)
    state = read_state()
    state.update({"pid": process.pid, "port": port, "profile": profile.key, "started_at": int(time.time())})
    write_state(state)
    return state


def wait_ready(state: dict) -> None:
    if DRY_RUN:
        return
    say("\nЗапускаю модель. При первом запуске она скачивается — это самый долгий шаг.")
    started = time.time()
    last_note = 0.0
    while time.time() - started < 3600:
        if is_healthy(state["port"]):
            break
        if not pid_alive(state["pid"]):
            raise RuntimeError(f"Сервер остановился. Последняя строка журнала: {log_tail()}\nПолный журнал: {LOG_FILE}")
        if time.time() - last_note > 10:
            last_note = time.time()
            say(f"  [{int(time.time() - started)} с] {log_tail()}")
        time.sleep(2)
    else:
        raise RuntimeError("Сервер не запустился за час. Смотрите журнал: " + str(LOG_FILE))
    say("Сервер отвечает. Проверяю пробным вопросом…")
    status, body = http_json(
        f"http://127.0.0.1:{state['port']}/v1/chat/completions",
        {"model": state["profile"], "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 16},
        timeout=300,
    )
    if status != 200 or not body.get("choices"):
        raise RuntimeError("Сервер запущен, но не отвечает на вопросы. Смотрите журнал: " + str(LOG_FILE))
    say("Модель отвечает. Всё работает.")


def running_state() -> dict | None:
    state = read_state()
    if state.get("pid") and pid_alive(state["pid"]):
        return state
    return None


def stop_server() -> None:
    state = read_state()
    pid = state.get("pid")
    if pid and pid_alive(pid):
        say(f"Останавливаю сервер (PID {pid}).")
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
        say("Запущенного сервера нет.")
    state.pop("pid", None)
    if STATE_FILE.exists():
        write_state(state)


# ───────────────────────────── OpenCode ─────────────────────────────

def find_opencode() -> Path | None:
    local = OPENCODE_HOME / ".opencode" / "bin" / "opencode"
    if local.exists():
        return local
    found = shutil.which("opencode")
    return Path(found) if found else None


def install_opencode() -> Path | None:
    existing = find_opencode()
    if existing:
        return existing
    if platform.system() == "Windows":
        say("OpenCode на Windows этот мастер не ставит. Установите его по инструкции https://opencode.ai/docs "
            "(рекомендуется WSL), затем запустите мастер снова — конфигурация проекта уже будет готова.")
        return None
    if DRY_RUN:
        say(f"[dry-run] установил бы OpenCode в {OPENCODE_HOME}")
        return None
    OPENCODE_HOME.mkdir(parents=True, exist_ok=True)
    script = ROOT / "install-opencode.sh"
    download(OPENCODE_INSTALL_URL, script)
    # Установщик пишет в $HOME/.opencode/bin; подменяем HOME, чтобы всё осталось в нашей папке.
    run_cmd(["bash", str(script), "--no-modify-path"], env=dict(os.environ, HOME=str(OPENCODE_HOME)))
    script.unlink(missing_ok=True)
    return find_opencode()


DEMO_HTML = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Учебная страница</title></head>
<body><h1>Привет!</h1><p>Попросите помощника: «измени заголовок и добавь переключатель темы».</p></body></html>
"""


def setup_demo_project(profile: Profile, port: int) -> Path:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    (DEMO_DIR / "index.html").write_text(DEMO_HTML, encoding="utf-8")
    config = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {"local-ai-starter": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Local AI Starter (llama.cpp)",
            "options": {"baseURL": f"http://127.0.0.1:{port}/v1"},
            "models": {profile.key: {"name": f"{profile.title} (локально)",
                                     "limit": {"context": profile.context, "output": 4096}}},
        }},
        "model": f"local-ai-starter/{profile.key}",
    }
    path = DEMO_DIR / "opencode.json"
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


# ───────────────────────────── сценарии ─────────────────────────────

def choose_profile(purpose_code: bool) -> Profile:
    ram = ram_gb()
    free = free_gb()
    say("\nПроверка компьютера")
    say(f"  Система: {platform.system()} {platform.machine()}")
    say(f"  Память: {f'{ram:.0f} ГБ' if ram else 'не удалось определить'}")
    say(f"  Свободно на диске: {free:.0f} ГБ")
    if purpose_code:
        recommended = PROFILES["code"] if (ram or 16) >= 16 else PROFILES["fast"]
    else:
        recommended = PROFILES["general"] if (ram or 16) >= 12 else PROFILES["fast"]
    others = [p for p in PROFILES.values() if p is not recommended and (purpose_code or p.key != "code")]
    options = [f"{recommended.title} — {recommended.purpose} (загрузка {recommended.download}) — рекомендую"]
    options += [f"{p.title} — {p.purpose} (загрузка {p.download})" for p in others]
    choice = ask("Какую модель берём?", options, 1)
    profile = recommended if choice == 1 else others[choice - 2]
    if ram and ram < profile.min_ram_gb:
        say(f"\nВнимание: для этой модели желательно от {profile.min_ram_gb} ГБ памяти, у вас {ram:.0f} ГБ. "
            "Может работать медленно.")
        if not yes_no("Всё равно продолжить?", False):
            raise Cancelled()
    if free < 12:
        say(f"\nСвободного места мало ({free:.0f} ГБ). Нужно ещё несколько гигабайт для модели.")
        if not yes_no("Продолжить?", False):
            raise Cancelled()
    return profile


def bring_up(profile: Profile) -> dict:
    existing = running_state()
    if existing and existing.get("profile") == profile.key and is_healthy(existing["port"]):
        say("Сервер уже работает.")
        return existing
    if existing:
        stop_server()
    port = pick_port(DEFAULT_PORT)
    if port != DEFAULT_PORT:
        say(f"Порт {DEFAULT_PORT} занят, использую {port}.")
    state = start_server(profile, port)
    wait_ready(state)
    return state


def open_chat(port: int) -> None:
    url = f"http://127.0.0.1:{port}"
    say(f"\nЧат: {url}")
    if not DRY_RUN:
        webbrowser.open(url)


def launch_opencode(profile: Profile, port: int, binary: Path | None) -> None:
    path = setup_demo_project(profile, port)
    say(f"\nУчебный проект готов: {DEMO_DIR}")
    if not binary:
        say("OpenCode не найден — после установки выполните в этой папке команду opencode.")
        return
    say("OpenCode спросит подтверждение перед изменением файлов — это нормально, не отключайте его.")
    say("Попробуйте задачу: «измени заголовок на index.html и добавь переключатель темы».")
    if DRY_RUN or not yes_no("Открыть OpenCode прямо сейчас в этом окне?", True):
        say(f'Позже: cd "{DEMO_DIR}" && "{binary}"')
        return
    subprocess.run([str(binary)], cwd=str(DEMO_DIR))


def first_run() -> None:
    say("Local AI Starter — локальный ИИ на вашем компьютере.")
    say("Всё скачивается в папку рядом со скриптом, наружу ничего не открывается.")
    purpose = ask("Для чего вам помощник?", ["Чат и тексты", "Программирование в OpenCode"], 1)
    code = purpose == 2
    profile = choose_profile(code)
    plat = llama_platform()
    say(f"\nПлан:\n  1. Скачать движок llama.cpp {LLAMA_BUILD} ({plat}) в {BIN_DIR}\n"
        f"  2. Скачать модель «{profile.title}» ({profile.download}) в {MODELS_DIR}\n"
        + ("  3. Поставить OpenCode и создать учебный проект\n" if code else ""))
    if not yes_no("Начинаем?", True):
        raise Cancelled()
    install_llama()
    binary = install_opencode() if code else None
    state = bring_up(profile)
    if code:
        launch_opencode(profile, state["port"], binary)
    else:
        open_chat(state["port"])


def show_status() -> None:
    state = read_state()
    say(f"\nПапка данных: {ROOT}")
    say(f"Движок: {'установлен' if server_binary() else 'не установлен'}")
    alive = running_state()
    say(f"Сервер: {'работает, порт ' + str(alive['port']) if alive else 'не запущен'}")
    say(f"Профиль: {state.get('profile', '—')}")
    say(f"Журнал: {LOG_FILE}")
    if LOG_FILE.exists():
        say("Последняя строка: " + log_tail())


def uninstall() -> None:
    say(f"\nБудет удалена папка {ROOT} целиком: движок, модели и учебный проект.")
    if not yes_no("Удалить всё?", False):
        return
    stop_server()
    shutil.rmtree(ROOT, ignore_errors=True)
    say("Готово. В системе ничего больше не осталось.")


def menu() -> None:
    state = read_state()
    profile = PROFILES.get(state.get("profile", ""), PROFILES["general"])
    while True:
        choice = ask("Local AI Starter", [
            "Запустить и открыть чат",
            "Остановить сервер",
            "Выбрать другую модель",
            "Учебный проект в OpenCode",
            "Состояние и журнал",
            "Удалить всё, что скачано",
            "Выход",
        ], 1)
        if choice == 1:
            state = bring_up(profile)
            open_chat(state["port"])
        elif choice == 2:
            stop_server()
        elif choice == 3:
            profile = choose_profile(False)
            state = bring_up(profile)
            open_chat(state["port"])
        elif choice == 4:
            code = PROFILES["code"]
            binary = install_opencode()
            state = bring_up(code)
            launch_opencode(code, state["port"], binary)
            profile = code
        elif choice == 5:
            show_status()
        elif choice == 6:
            uninstall()
            if not ROOT.exists():
                return
        else:
            return


def main() -> int:
    try:
        if server_binary() or DRY_RUN and STATE_FILE.exists():
            menu()
        else:
            first_run()
            if yes_no("Открыть меню управления (остановка, смена модели)?", False):
                menu()
        return 0
    except Cancelled:
        say("\nОтменено.")
        return 0
    except KeyboardInterrupt:
        say("\nОтменено.")
        return 0
    except (RuntimeError, subprocess.CalledProcessError, urllib.error.URLError, OSError) as error:
        say(f"\nОшибка: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
