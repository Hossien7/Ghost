@echo off
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --name OperationEclipse --add-data "frontend;frontend" --collect-all uvicorn --collect-all fastapi --collect-all qrcode backend\main.py
echo.
echo EXE created in dist\OperationEclipse.exe
pause
