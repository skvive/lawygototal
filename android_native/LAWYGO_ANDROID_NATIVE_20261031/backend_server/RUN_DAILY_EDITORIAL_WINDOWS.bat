@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
if not defined LAWYGO_DB_PATH set "LAWYGO_DB_PATH=%LOCALAPPDATA%\LAWYGO\data\lawygo.db"
if not defined LAWYGO_UPLOAD_PATH set "LAWYGO_UPLOAD_PATH=%LOCALAPPDATA%\LAWYGO\data\uploads"
if not exist ".venv\Scripts\python.exe" (
 echo [LAWYGO] Run SETUP_WINDOWS.cmd before scheduled tasks.
 exit /b 2
)
".venv\Scripts\python.exe" run_daily_editorial.py
if errorlevel 1 exit /b 1
