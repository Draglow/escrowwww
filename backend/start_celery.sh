#!/bin/bash
# Script to start Celery worker and beat scheduler

set -e

echo "=== Starting Celery Services ==="

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A config worker --loglevel=info --concurrency=4 &
WORKER_PID=$!

# Start Celery beat scheduler in background
echo "Starting Celery beat scheduler..."
celery -A config beat --loglevel=info &
BEAT_PID=$!

echo "Celery worker PID: $WORKER_PID"
echo "Celery beat PID: $BEAT_PID"

# Wait for both processes
wait $WORKER_PID $BEAT_PID
