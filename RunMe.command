#!/bin/bash
# macOS double-click launcher. First time: right-click -> Open (Gatekeeper).
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it from https://www.python.org/downloads/ and run this file again."
  read -r -p "Press Enter to close this window..." _
  exit 1
fi
python3 local_ai_starter.py "$@"
status=$?
if [ $status -ne 0 ]; then
  read -r -p "Press Enter to close this window..." _
fi
exit $status
