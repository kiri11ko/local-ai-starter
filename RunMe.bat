@echo off
rem Windows double-click launcher.
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul && (py -3 local_ai_starter.py %* & goto done)
where python >nul 2>nul && (python local_ai_starter.py %* & goto done)
echo Python 3 is required: https://www.python.org/downloads/
:done
pause
