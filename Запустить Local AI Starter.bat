@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul && (py -3 local_ai_starter.py & goto done)
where python >nul 2>nul && (python local_ai_starter.py & goto done)
echo Нужен Python 3: https://www.python.org/downloads/
:done
pause
