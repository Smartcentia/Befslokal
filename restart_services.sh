#!/bin/bash

# Kill existing processes
echo "Stopping existing services..."
pkill -f "uvicorn app.main:app"
pkill -f "next-server" 
pkill -f "next dev"

# Wait a moment
sleep 2

# Start Backend
echo "Starting Backend..."
cd KNOWME/backend
# source .venv/bin/activate # Commented out as it might vary by environment, let user handle venv if needed
nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../../backend.log 2>&1 &
cd ../..

# Start Frontend
echo "Starting Frontend..."
cd KNOWME/frontend
nohup npm run dev > ../../frontend.log 2>&1 &
cd ../..

echo "Services restarted! Check backend.log and frontend.log for output."
