#!/usr/bin/env bash
# Deploy job-radar: push local main, then pull + restart on the EC2 host.
# Usage: ./deploy.sh            (push origin main, then remote pull+restart)
#        ./deploy.sh --no-push  (skip the push; just pull+restart on server)
set -euo pipefail

HOST=job-radar        # SSH alias defined in ~/.ssh/config
APP_DIR=/home/ubuntu/app
SERVICE=job-radar

if [[ "${1:-}" != "--no-push" ]]; then
  echo "==> Pushing local main to origin..."
  git -C "$(dirname "$0")" push origin main
fi

echo "==> Pulling and restarting on $HOST..."
ssh "$HOST" "cd $APP_DIR && git pull origin main && sudo systemctl restart $SERVICE && sleep 3 && systemctl is-active $SERVICE && git log --oneline -1"
echo "==> Done."
