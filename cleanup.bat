@echo off
echo ========================================
echo   Attend-X Project Cleanup
echo ========================================
echo.
echo This will remove:
echo - Virtual environments
echo - Node modules
echo - Cache files
echo - Log files
echo - Temporary files
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Cleaning up...
echo.

REM Remove Python cache
echo Removing Python cache...
if exist backend\__pycache__ rmdir /s /q backend\__pycache__
if exist __pycache__ rmdir /s /q __pycache__

REM Remove virtual environments
echo Removing virtual environments...
if exist .venv rmdir /s /q .venv
if exist backend\venv rmdir /s /q backend\venv

REM Remove Node modules
echo Removing node_modules...
if exist frontend\node_modules rmdir /s /q frontend\node_modules
if exist node_modules rmdir /s /q node_modules

REM Remove log files
echo Removing log files...
if exist backend.log del /q backend.log
if exist backend\check_db.log del /q backend\check_db.log
if exist backend\*.log del /q backend\*.log

REM Remove package-lock.json
echo Removing package-lock.json...
if exist frontend\package-lock.json del /q frontend\package-lock.json
if exist package-lock.json del /q package-lock.json

REM Remove .pyc files
echo Removing .pyc files...
for /r %%i in (*.pyc) do del /q "%%i"

echo.
echo ========================================
echo   Cleanup Complete!
echo ========================================
echo.
echo To reinstall dependencies:
echo.
echo Backend:
echo   cd backend
echo   python -m venv venv
echo   venv\Scripts\activate
echo   pip install -r requirements.txt
echo.
echo Frontend:
echo   cd frontend
echo   npm install
echo.
pause
