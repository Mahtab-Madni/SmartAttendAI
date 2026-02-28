#!/bin/bash
set -e

# Get port from environment or use default
PORT=${PORT:-8000}

# Start the application
python -m uvicorn app:app --host 0.0.0.0 --port $PORT
