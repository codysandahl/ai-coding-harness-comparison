@echo off
REM Start the Local AI Image Explorer backend
echo Starting Local AI Image Explorer...
cd /d "%~dp0src\backend"
call .venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
