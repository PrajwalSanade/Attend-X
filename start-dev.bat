@echo off
echo ========================================
echo   AttendX Development Environment
echo ========================================
echo.

echo Starting Backend (Port 5000)...
start "AttendX Backend" cmd /k "cd backend && python start.py"

timeout /t 3 /nobreak > nul

echo Starting Frontend (Port 3000)...
start "AttendX Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   Both servers are starting...
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:5000/docs
echo ========================================
echo.
echo Press any key to stop all servers...
pause > nul

echo Stopping servers...
taskkill /FI "WindowTitle eq AttendX Backend*" /T /F
taskkill /FI "WindowTitle eq AttendX Frontend*" /T /F
