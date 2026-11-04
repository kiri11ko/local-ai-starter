#!/bin/sh
# Linux launcher: ./RunMe.sh in a terminal
# (double-click works in file managers that allow running scripts).
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it with your package manager, e.g.: sudo apt install python3"
  printf "Press Enter to close this window..."; read -r _
  exit 1
fi
python3 local_ai_starter.py "$@"
status=$?
if [ $status -ne 0 ]; then
  printf "Press Enter to close this window..."; read -r _
fi
exit $status
