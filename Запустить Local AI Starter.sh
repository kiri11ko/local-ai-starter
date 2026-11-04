#!/bin/sh
# Linux: ./"Запустить Local AI Starter.sh" в терминале
# (двойной клик работает в файловых менеджерах, где включён запуск скриптов).
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Нужен Python 3. Установите его через пакетный менеджер, например: sudo apt install python3"
  printf "Нажмите Enter, чтобы закрыть окно…"; read -r _
  exit 1
fi
python3 local_ai_starter.py
status=$?
if [ $status -ne 0 ]; then
  printf "Нажмите Enter, чтобы закрыть окно…"; read -r _
fi
exit $status
