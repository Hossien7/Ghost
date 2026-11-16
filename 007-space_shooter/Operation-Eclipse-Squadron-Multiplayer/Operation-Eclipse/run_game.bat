@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Creating Python environment...
  py -3 -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -r requirements.txt
python backend\main.py
pause
