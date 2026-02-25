#!/bin/bash

# Mnemosine Startup Script
# This script reliably starts both the backend (FastAPI) and frontend (React).

# Exit on error
set -e

# Base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

echo "========================================"
echo "    Starting Mnemosine Application      "
echo "========================================"

# 1. Check Python dependencies
echo "=> Checking backend..."
cd "$BASE_DIR/backend"
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "Warning: No virtual environment found in backend/. Make sure dependencies are installed."
fi

# Kill existing processes on ports 8000 and 5173 to avoid conflicts
echo "=> Cleaning up stale processes on ports 8000 and 5173..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true
sleep 1

# Start Backend
echo "=> Starting FastAPI Backend (Port 8000)..."
# We inject python-dotenv from the local env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend running with PID: $BACKEND_PID (logs in backend/backend.log)"

# Wait for backend to be ready
echo "   Waiting for backend to initialize..."
sleep 3
if curl -s http://localhost:8000/health | grep -q '"status":"ok"'; then
    echo "   Backend is UP."
else
    echo "   Backend might be slow to start or failed. Check backend.log."
fi

# Start Frontend
echo "=> Starting React Frontend (Port 5173)..."
cd "$BASE_DIR/frontend"
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend running with PID: $FRONTEND_PID (logs in frontend/frontend.log)"

echo "========================================"
echo " Mnemosine is running!"
echo " - Frontend UI: http://localhost:5173"
echo " - Backend API: http://localhost:8000"
echo " - API Docs:    http://localhost:8000/docs"
echo "========================================"
echo "Press Ctrl+C to stop both servers."

# Trap Ctrl+C to kill both background processes
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait indefinitely, keeping the script alive so the trap works
wait $BACKEND_PID $FRONTEND_PID
