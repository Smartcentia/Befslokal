#!/bin/bash

BACKEND_PORT=8000
FRONTEND_PORT=3000

check_port() {
  lsof -i :$1 > /dev/null
  return $?
}

start_backend() {
  echo "[$(date)] Starting Backend..."
  cd backend
  source .venv/bin/activate
  nohup uvicorn app.main:app --reload --port $BACKEND_PORT > ../backend.log 2>&1 &
  cd ..
}

start_frontend() {
  echo "[$(date)] Starting Frontend..."
  cd frontend
  nohup npm run dev > ../frontend.log 2>&1 &
  cd ..
}

echo "Starting watchdog..."

while true; do
  if ! check_port $BACKEND_PORT; then
    echo "[$(date)] Backend down detected!"
    start_backend
    sleep 5 # Wait for startup
  fi

  if ! check_port $FRONTEND_PORT; then
    echo "[$(date)] Frontend down detected!"
    start_frontend
    sleep 5 # Wait for startup
  fi

  sleep 10
done
