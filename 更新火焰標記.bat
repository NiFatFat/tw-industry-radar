@echo off
chcp 65001 >nul
cd /d "%~dp0"
"E:\Downloads\學員包\.venv\Scripts\python.exe" local_push_flags.py
echo.
pause
