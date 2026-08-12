@echo off
REM Self-check script for Local AI Image Explorer
cd /d "%~dp0src\backend"
call .venv\Scripts\activate
python demo.py
