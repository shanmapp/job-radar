#!/bin/bash

PID_FILE="$(dirname "$0")/app.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "No PID file found — app may not be running"
  exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  rm "$PID_FILE"
  echo "Stopped (PID $PID)"
else
  echo "Process $PID not found — cleaning up PID file"
  rm "$PID_FILE"
fi
