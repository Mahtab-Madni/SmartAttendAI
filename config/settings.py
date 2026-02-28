"""
SmartAttendAI Configuration
All system settings and constants
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = DATA_DIR / "logs"
FACES_DIR = DATA_DIR / "faces"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR, FACES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Liveness Detection Settings
LIVENESS_CONFIG = {
    "EAR_THRESHOLD": 0.25,  # Eye Aspect Ratio threshold for blink detection
    "CONSECUTIVE_FRAMES": 3,  # Frames to confirm blink
    "BLINK_TIME_WINDOW": 15,  # Seconds to detect natural blink (increased)
    "MIN_BLINKS": 2,  # Minimum blinks required (increased security)
    "MAX_BLINKS": 8,  # Maximum blinks allowed (anti-rapid-blink attack)
    "MOTION_THRESHOLD": 10,  # Minimum motion between frames
    "TEXTURE_ANALYSIS": True,  # Enable texture-based spoof detection
    "CHALLENGE_RESPONSE": True,  # Enable challenge-response verification
}

# Face Recognition Settings
FACE_CONFIG = {
    "TOLERANCE": 0.6,  # Face matching tolerance (lower = stricter)
    "MODEL": "hog",  # Options: 'hog' (CPU) or 'cnn' (GPU)
    "JITTERS": 1,  # Number of times to re-sample face for encoding
    "MIN_FACE_SIZE": (120, 120),  # Minimum face dimensions (increased for better accuracy)
    "CONFIDENCE_THRESHOLD": 70,  # Minimum confidence for face recognition (0-100)
    "MAX_FACES_PER_FRAME": 3,  # Maximum faces to process per frame
    "FACE_PADDING": 20,  # Pixels to add around detected face
}

# Geofencing Settings
GEOFENCE_CONFIG = {
    "RADIUS_METERS": 200,  # Attendance valid within this radius (200 meters)
    "CLASSROOM_LOCATIONS": {
        # Default locations - Update these for your institution
        "Reading_Room": {"lat": 28.558773, "lon": 77.277969},  
        "Room_331": {"lat": 26.1197, "lon": 85.3910}, 
        "Room_328": {"lat": 28.558773, "lon": 77.277969},
        "Home": {"lat": 28.555247, "lon": 77.289663},
    },
    "GPS_ACCURACY_THRESHOLD": 50,  # Minimum GPS accuracy in meters
    "MOCK_LOCATION_DETECTION": True,  # Enable developer options detection
}

# Emotion Analysis Settings
EMOTION_CONFIG = {
    "EMOTIONS": ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"],
    "ANALYSIS_INTERVAL": 30,  # Seconds between emotion captures
    "REPORT_THRESHOLD": 0.6,  # Confidence threshold for emotion
}

# Fraud Detection Settings
FRAUD_CONFIG = {
    "TEXTURE_THRESHOLD": 0.7,  # CNN model confidence for real vs fake
    "CHALLENGE_PROBABILITY": 0.3,  # 30% chance of challenge-response
    "CHALLENGES": [
        "Please smile",
        "Please turn your head left",
        "Please turn your head right",
        "Please nod your head",
    ],
}

# Voice Verification Settings
VOICE_CONFIG = {
    "REQUIRED": False,  # Set True to make voice MFA mandatory
    "TIMEOUT": 5,  # Seconds to record voice
    "SIMILARITY_THRESHOLD": 0.75,  # Voice match threshold
}

# Database Settings
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite").lower()  # Options: 'sqlite', 'postgresql'
DATABASE_URL = os.getenv("DATABASE_URL")  # Only needed for PostgreSQL

# Validate PostgreSQL configuration if using PostgreSQL
if DATABASE_TYPE == "postgresql" and not DATABASE_URL:
    print("[WARNING] DATABASE_TYPE=postgresql but DATABASE_URL not set. Falling back to SQLite.")
    DATABASE_TYPE = "sqlite"

DATABASE_CONFIG = {
    "TYPE": DATABASE_TYPE,
    "SQLITE_PATH": DATA_DIR / "smartattend.db",
    "DATABASE_URL": DATABASE_URL,  # PostgreSQL connection string
    "FIREBASE_CREDS": BASE_DIR / "config" / "firebase-credentials.json",
}

# API Keys (Load from environment)
API_KEYS = {
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
}

# Notification Settings
NOTIFICATION_CONFIG = {
    "TELEGRAM_ENABLED": os.getenv("TELEGRAM_ENABLED", "True").lower() == "true",
}

# Server Settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY")

# Validate SECRET_KEY in production
if ENVIRONMENT == "production" and (not SECRET_KEY or SECRET_KEY == "your-secret-key-change-this-in-production"):
    raise ValueError("SECRET_KEY must be set and unique in production environment!")

SERVER_CONFIG = {
    "HOST": os.getenv("SERVER_HOST", "0.0.0.0"),
    "PORT": int(os.getenv("SERVER_PORT", "8000")),
    "DEBUG": DEBUG,
    "RELOAD": False,  # Disabled to prevent multiprocessing conflicts with dlib/face_recognition
}

# Offline Mode Settings
OFFLINE_CONFIG = {
    "ENABLED": True,
    "SYNC_INTERVAL": 300,  # Seconds between sync attempts
    "MAX_QUEUE_SIZE": 1000,  # Maximum offline records to store
}

# Logging Settings
LOGGING_CONFIG = {
    "LEVEL": "INFO",
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "FILE": LOGS_DIR / "smartattend.log",
}