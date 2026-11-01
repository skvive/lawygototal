@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo [LAWYGO] Install using SETUP_WINDOWS.cmd in the original release package first.
 exit /b 2
)
if not defined LAWYGO_DB_PATH set "LAWYGO_DB_PATH=%LOCALAPPDATA%\LAWYGO\data\lawygo.db"
if not defined LAWYGO_UPLOAD_PATH set "LAWYGO_UPLOAD_PATH=%LOCALAPPDATA%\LAWYGO\data\uploads"
".venv\Scripts\python.exe" setup_admin.py
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" launcher.py
