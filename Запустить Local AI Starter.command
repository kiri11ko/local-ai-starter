#!/bin/bash
# Двойной клик на macOS. Первый раз: правый клик -> Открыть (Gatekeeper).
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Нужен Python 3. Установите его с https://www.python.org/downloads/ и запустите файл снова."
  read -r -p "Нажмите Enter, чтобы закрыть окно…" _
  exit 1
fi
python3 local_ai_starter.py
status=$?
if [ $status -ne 0 ]; then
  read -r -p "Нажмите Enter, чтобы закрыть окно…" _
fi
exit $status
