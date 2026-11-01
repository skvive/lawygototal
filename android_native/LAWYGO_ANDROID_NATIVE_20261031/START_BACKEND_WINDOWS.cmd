@echo off
setlocal
cd /d "%~dp0backend_server"
if not exist .venv (py -3.11 -m venv .venv || exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt || exit /b 2
if not exist .env (echo LAWYGO_SECURE_COOKIES=false> .env)
python -m uvicorn app:app --host 127.0.0.1 --port 8018
