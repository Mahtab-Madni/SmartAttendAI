"""
Development Configuration
Simplified settings for testing without all dependencies
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = DATA_DIR / "logs"
FACES_DIR = DATA_DIR / "faces"

# Environment Configuration
DEV_MODE = True
SKIP_DLIB = True  # Skip dlib-dependent features in development
SKIP_TENSORFLOW = True  # Skip TensorFlow features in development

# Create .env file if it doesn't exist
env_file = BASE_DIR / ".env"
if not env_file.exists():
    with open(env_file, 'w') as f:
        f.write("""# SmartAttendAI Environment Variables
DEBUG=True
SKIP_DLIB=True
SKIP_TENSORFLOW=True

# Database
DATABASE_URL=sqlite:///./data/attendance.db

# API Keys (Add your actual keys here)
TELEGRAM_BOT_TOKEN=your_telegram_token
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
""")

print("Development environment configured!")