@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto :fail
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :fail
if not exist .env copy .env.example .env >nul
.venv\Scripts\python.exe setup_admin.py
start "LAWYGO Studio" http://127.0.0.1:8018
.venv\Scripts\python.exe app.py
exit /b 0
:fail
echo Python 3.11+ and internet for pip are required.
pause
exit /b 1
