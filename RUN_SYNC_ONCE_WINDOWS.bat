@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (".venv\Scripts\python.exe" sync_worker.py --once) else (python sync_worker.py --once)
pause
