#!/bin/bash
set -e

# Load env vars
export $(grep -v '^#' "$(dirname "$0")/.env" | xargs)

cd "$(dirname "$0")/job_crawlers-main"

# Check if already running
if [ -f ../app.pid ] && kill -0 $(cat ../app.pid) 2>/dev/null; then
  echo "App is already running (PID $(cat ../app.pid))"
  exit 0
fi

echo "Starting job crawler..."
nohup gunicorn app:app --bind 0.0.0.0:8000 --workers 1 --timeout 120 \
  > ../app.log 2>&1 &
echo $! > ../app.pid

echo "Started (PID $!)"
echo "Logs: tail -f $(dirname "$0")/app.log"
echo ""
echo "Now trigger the crawlers:"
echo "  curl -X POST http://localhost:8000/main -H 'Content-Type: application/json' -d '{\"email\": \"your@email.com\"}'"
