#!/bin/bash
set -e

# Get port from environment or use default
PORT=${PORT:-8000}

echo "Starting SmartAttendAI on port $PORT..."
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

# Start the application with verbose logging
python -m uvicorn app:app --host 0.0.0.0 --port $PORT --log-level info
