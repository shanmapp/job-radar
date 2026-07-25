#!/usr/bin/env bash
# Convenience helpers for the job-radar EC2 host.
# Usage: ./remote.sh ssh|status|logs|crawl <f1|soccer|brands>
set -euo pipefail
HOST=job-radar
case "${1:-}" in
  ssh)     shift; exec ssh "$HOST" "$@" ;;
  status)  ssh "$HOST" "systemctl status job-radar --no-pager -n 10" ;;
  logs)    ssh "$HOST" "sudo journalctl -u job-radar --no-pager -n ${2:-60}" ;;
  crawl)   ssh "$HOST" "curl -s http://localhost:8000/${2:?f1|soccer|brands}" ; echo ;;
  *) echo "usage: $0 ssh|status|logs [N]|crawl <f1|soccer|brands>"; exit 1 ;;
esac
