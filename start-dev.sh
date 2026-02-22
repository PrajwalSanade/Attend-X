#!/bin/bash

echo "========================================"
echo "  AttendX Development Environment"
echo "========================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

echo "Starting Backend (Port 5000)..."
cd backend && python start.py &
BACKEND_PID=$!

sleep 3

echo "Starting Frontend (Port 3000)..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  Both servers are running!"
echo "  Backend:  http://localhost:5000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:5000/docs"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all servers..."

wait
