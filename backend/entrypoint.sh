#!/bin/bash

# Entrypoint script that handles different process types
# Usage: entrypoint.sh [process_type] [additional_args]

set -e

# Accept an explicit arg first, then PROCESS_TYPE from the environment, then default to web.
PROCESS_TYPE="${1:-${PROCESS_TYPE:-web}}"

# Default PORT to 8000 if not set
PORT="${PORT:-8000}"

case "$PROCESS_TYPE" in
  web)
    echo "Starting web server on port $PORT..."
    exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2 --log-level info
    ;;
  worker)
    echo "Starting Celery worker..."
    exec celery -A app.tasks worker --loglevel=info --pool=solo --concurrency=2
    ;;
  beat)
    echo "Starting Celery beat scheduler..."
    exec celery -A app.tasks beat --loglevel=info
    ;;
  events)
    echo "Starting event subscriber..."
    exec python -m app.events.subscriber
    ;;
  *)
    echo "Unknown process type: $PROCESS_TYPE"
    echo "Valid options: web, worker, beat, events"
    exit 1
    ;;
esac
