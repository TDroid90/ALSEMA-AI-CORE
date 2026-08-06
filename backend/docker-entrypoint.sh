#!/bin/sh
set -eu
case "$1" in
  api) alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ;;
  worker) exec python -m arq app.workers.arq.WorkerSettings ;;
  *) exit 64 ;;
esac
