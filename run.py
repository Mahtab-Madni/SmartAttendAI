#!/usr/bin/env python
"""
Railway startup wrapper - handles PORT environment variable
"""
import os
import sys
import subprocess

# Get PORT from environment, default to 8000
port = os.getenv("PORT", "8000")

print(f"Starting SmartAttendAI on port {port}...")

# Run uvicorn with the PORT environment variable
cmd = [
    sys.executable,
    "-m",
    "uvicorn",
    "app:app",
    "--host",
    "0.0.0.0",
    "--port",
    port,
    "--log-level",
    "info"
]

print(f"Running: {' '.join(cmd)}")
subprocess.run(cmd)
