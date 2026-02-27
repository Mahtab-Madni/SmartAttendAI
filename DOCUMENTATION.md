# SmartAttendAI Project Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Module Documentation](#module-documentation)
3. [API Reference](#api-reference)
4. [Configuration Guide](#configuration-guide)
5. [Deployment Guide](#deployment-guide)

## Architecture Overview

SmartAttendAI follows a modular architecture with clear separation of concerns:

```
User Interface (Web/Mobile)
        ↓
FastAPI REST API
        ↓
Core Modules (Liveness, Face Recognition, Geofencing, etc.)
        ↓
Database Layer (SQLite/Firebase)
```

### Data Flow for Attendance Marking

1. **User Authentication** → Student opens app/web interface
2. **Location Check** → GPS coordinates validated against geofence
3. **Liveness Detection** → Eye blink and texture analysis
4. **Face Recognition** → Match against registered database
5. **Fraud Detection** → Multi-layer security checks
6. **Database Storage** → Record attendance with all metadata
7. **Notification** → Send confirmation via Telegram/SMS

## Module Documentation

### 1. Liveness Detection (`src/liveness/detector.py`)

#### LivenessDetector Class

**Purpose**: Detect if the person is physically present (not a photo/video)

**Methods**:
- `calculate_ear(eye)`: Calculate Eye Aspect Ratio
- `detect_blinks(frame)`: Main detection loop
- `reset()`: Reset detection state

**Algorithm**:
```
EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
where p1-p6 are eye landmark coordinates
```

**Configuration**:
```python
LIVENESS_CONFIG = {
    "EAR_THRESHOLD": 0.25,
    "CONSECUTIVE_FRAMES": 3,
    "BLINK_TIME_WINDOW": 10,
    "MIN_BLINKS": 1,
    "MAX_BLINKS": 5
}
```

### 2. Face Recognition (`src/face_recognition/recognizer.py`)

#### FaceRecognitionSystem Class

**Purpose**: Register and recognize student faces

**Methods**:
- `register_face()`: Add new student to database
- `recognize_face()`: Identify person in frame
- `remove_face()`: Remove student from database
- `list_registered_students()`: Get all students

**Storage**:
- Face encodings: `data/faces/encodings.pkl`
- Metadata: `data/faces/metadata.json`

### 3. Geofencing (`src/geofencing/validator.py`)

#### GeofenceValidator Class

**Purpose**: Validate student location

**Methods**:
- `haversine_distance()`: Calculate distance between coordinates
- `is_within_geofence()`: Check if location is valid
- `get_nearest_classroom()`: Find closest classroom

**Formula (Haversine)**:
```
a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
c = 2 ⋅ atan2(√a, √(1−a))
d = R ⋅ c
where φ is latitude, λ is longitude, R is earth's radius (6371km)
```

### 4. Emotion Analysis (`src/emotion_analysis/analyzer.py`)

#### EmotionAnalyzer Class

**Purpose**: Detect student emotions and engagement

**Supported Emotions**:
- Happy
- Sad
- Angry
- Surprise
- Fear
- Disgust
- Neutral

**Methods**:
- `detect_emotion()`: Analyze single frame
- `record_emotion()`: Store for analytics
- `get_engagement_score()`: Calculate overall engagement (0-100)

### 5. Fraud Detection (`src/fraud_detection/detector.py`)

#### FraudDetector Class

**Purpose**: Detect and prevent attendance fraud

**Detection Methods**:
1. Photo/screen detection (texture analysis)
2. Multiple face detection
3. Face size validation
4. Lighting anomaly detection
5. Motion pattern analysis

**Severity Levels**:
- **High**: Photo attack, liveness failure, motion anomaly
- **Medium**: Lighting anomaly
- **Low**: Face too small

## API Reference

### REST Endpoints

#### Authentication & Students

```http
POST /api/students/register
Content-Type: multipart/form-data

{
  "name": "John Doe",
  "student_id": "STU001",
  "roll_number": "22001",
  "email": "john@example.com",
  "phone": "+1234567890",
  "photo": <file>
}
```

```http
GET /api/students
Response: {
  "students": [...]
}
```

#### Attendance

```http
POST /api/attendance/mark
Content-Type: application/json

{
  "student_id": "STU001",
  "classroom": "Room_101",
  "latitude": 18.5205,
  "longitude": 73.8568,
  "accuracy": 15.0
}
```

```http
GET /api/attendance/history/{student_id}?days=30
Response: {
  "student_id": "STU001",
  "history": [...],
  "statistics": {...}
}
```

```http
GET /api/attendance/today?classroom=Room_101
Response: {
  "date": "2024-02-26",
  "records": [...],
  "count": 45
}
```

#### Reports

```http
GET /api/reports/daily/2024-02-26
Response: {
  "date": "2024-02-26",
  "total_present": 45,
  "by_classroom": {...},
  "avg_face_confidence": 0.92,
  "fraud_attempts": 2
}
```

```http
GET /api/fraud/attempts?days=7
Response: {
  "attempts": [...],
  "count": 3,
  "period_days": 7
}
```

#### Sessions

```http
POST /api/session/start
{
  "session_id": "SESSION_001",
  "classroom": "Room_101",
  "subject": "Machine Learning",
  "teacher_name": "Dr. Smith"
}
```

```http
POST /api/session/end
Response: {
  "success": true,
  "message": "Session ended"
}
```

## Configuration Guide

### 1. Basic Settings (`config/settings.py`)

```python
# Liveness Detection
LIVENESS_CONFIG = {
    "EAR_THRESHOLD": 0.25,      # Adjust for sensitivity
    "MIN_BLINKS": 1,             # Minimum required blinks
    "BLINK_TIME_WINDOW": 10      # Detection window (seconds)
}

# Face Recognition
FACE_CONFIG = {
    "TOLERANCE": 0.6,            # Lower = stricter (0.4-0.7)
    "MODEL": "hog",              # 'hog' for CPU, 'cnn' for GPU
}

# Geofencing
GEOFENCE_CONFIG = {
    "RADIUS_METERS": 100,        # Attendance radius
    "CLASSROOM_LOCATIONS": {
        "Room_101": {"lat": 18.5204, "lon": 73.8567}
    }
}
```

### 2. Environment Variables (`.env`)

```env
TELEGRAM_BOT_TOKEN=your_token
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
```

## Deployment Guide

### Local Development

```bash
python setup.py
python main.py
```

### Web Server

```bash
python app.py
# Access at http://localhost:8000
```

### Production Deployment

#### Using Docker (Recommended)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

```bash
docker build -t smartattendai .
docker run -p 8000:8000 smartattendai
```

#### Using Systemd (Linux)

```ini
[Unit]
Description=SmartAttendAI Web Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/smartattendai
ExecStart=/opt/smartattendai/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Security Considerations

1. **HTTPS Required**: Always use HTTPS in production
2. **API Keys**: Never commit API keys to repository
3. **Database Encryption**: Enable encryption for sensitive data
4. **Rate Limiting**: Implement rate limiting on API endpoints
5. **CORS**: Configure CORS for web interface
6. **Authentication**: Add JWT authentication for API access

### Performance Optimization

1. **GPU Acceleration**: Use `MODEL="cnn"` for GPU-based face detection
2. **Caching**: Cache face encodings in memory
3. **Async Processing**: Use async/await for I/O operations
4. **Load Balancing**: Deploy multiple instances behind load balancer
5. **Database Indexing**: Ensure proper indexes on frequently queried fields

### Monitoring

- **Health Check**: `/health` endpoint for uptime monitoring
- **Logging**: Configure logging level in `LOGGING_CONFIG`
- **Metrics**: Track attendance rates, fraud attempts, system performance
- **Alerts**: Set up alerts for fraud attempts and system failures

---

For more information, visit: https://github.com/yourusername/SmartAttendAI