# SmartAttendAI 🎓

## Robust Attendance System with Liveness Detection & Geo-Fencing

SmartAttendAI is an advanced, AI-powered attendance system that eliminates proxy attendance through multiple layers of security including liveness detection, face recognition, geofencing, and emotion analytics.

---

## 🌟 Key Features

### 1. **Advanced Liveness Detection (Anti-Spoofing)**
- **Eye Blink Detection**: Uses Eye Aspect Ratio (EAR) calculation to ensure natural blinking
- **Texture Analysis**: CNN-based detection of screen patterns and photo artifacts
- **Challenge-Response**: Random action prompts (smile, turn head) to defeat pre-recorded videos

### 2. **Robust Face Recognition**
- High-accuracy face matching against authorized database
- Confidence scoring for each recognition
- Support for multiple students per session
- Efficient encoding storage and retrieval

### 3. **Geofencing Security**
- GPS-based location verification (100m radius default)
- Multiple classroom support
- GPS spoofing detection
- Location consistency verification

### 4. **Emotion & Engagement Analytics**
- Real-time emotion detection (7 emotions)
- Engagement scoring (0-100)
- Time-segmented analysis
- Teacher insights and recommendations

### 5. **Comprehensive Fraud Detection**
- Photo/screen attack detection
- Multiple face detection
- Lighting anomaly analysis
- Motion pattern verification
- Automated evidence capture

### 6. **Instant Notifications**
- Telegram bot integration
- SMS via Twilio
- Real-time attendance confirmations
- Fraud alerts
- Daily summaries

### 7. **Offline Mode & Sync**
- Local data storage during internet outage
- Automatic synchronization when online
- Queue management for pending records

---

## 🏗️ Architecture

```
SmartAttendAI/
├── config/
│   └── settings.py              # Configuration
├── src/
│   ├── liveness/
│   │   └── detector.py          # Liveness detection
│   ├── face_recognition/
│   │   └── recognizer.py        # Face recognition
│   ├── geofencing/
│   │   └── validator.py         # Geofencing
│   ├── emotion_analysis/
│   │   └── analyzer.py          # Emotion detection
│   ├── fraud_detection/
│   │   └── detector.py          # Fraud detection
│   └── utils/
│       ├── database.py          # Database operations
│       └── notifications.py     # Notification system
├── models/                      # AI models
├── data/                        # Data storage
│   ├── faces/                   # Face database
│   ├── logs/                    # System logs
│   └── fraud_attempts/          # Fraud evidence
├── main.py                      # Main application
└── requirements.txt             # Dependencies
```

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Webcam
- pip package manager

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/SmartAttendAI.git
cd SmartAttendAI
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Download Required Models
```bash
# Download dlib face landmarks predictor
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat models/
```

### Step 5: Configure Environment
Create `.env` file in the root directory:
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Twilio (SMS)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 📖 Usage

### 1. Register Students

#### Using Python Script:
```python
from src.face_recognition.recognizer import FaceRecognitionSystem
from config.settings import FACE_CONFIG

face_system = FaceRecognitionSystem(FACE_CONFIG)

face_system.register_face(
    image_path="data/faces/student_photo.jpg",
    student_name="John Doe",
    student_id="STU001",
    roll_number="22001",
    email="john@example.com",
    phone="+1234567890"
)
```

#### Using CSV Bulk Import:
```python
from src.face_recognition.recognizer import FaceRecognitionSystem, register_bulk_students

face_system = FaceRecognitionSystem(FACE_CONFIG)
register_bulk_students(face_system, "students.csv")
```

CSV Format:
```csv
name,id,roll_number,email,phone,image_path
John Doe,STU001,22001,john@example.com,+1234567890,data/faces/john.jpg
Jane Smith,STU002,22002,jane@example.com,+1234567891,data/faces/jane.jpg
```

### 2. Configure Classrooms

Edit `config/settings.py`:
```python
GEOFENCE_CONFIG = {
    "RADIUS_METERS": 100,
    "CLASSROOM_LOCATIONS": {
        "Room_101": {"lat": 18.5204, "lon": 73.8567},
        "Lab_A": {"lat": 18.5224, "lon": 73.8587},
    }
}
```

### 3. Start Attendance Session

Run the main application:
```bash
python main.py
```

Or use programmatically:
```python
from main import SmartAttendAI
from src.geofencing.validator import Location

system = SmartAttendAI()

# Start session
system.start_session(
    session_id="SESSION_001",
    classroom="Room_101",
    subject="Machine Learning",
    teacher_name="Dr. Smith"
)

# Mark attendance
student_location = Location(latitude=18.5205, longitude=73.8568, accuracy=15.0)
result = await system.mark_attendance(user_location=student_location)

# End session
system.end_session()
```

### 4. View Reports

#### Daily Attendance Report:
```python
from src.utils.database import AttendanceDatabase
from datetime import date

db = AttendanceDatabase()
report = db.generate_daily_report(str(date.today()))
print(report)
```

#### Fraud Analytics:
```python
from src.fraud_detection.detector import FraudAnalytics

analytics = FraudAnalytics(db)
report = analytics.generate_fraud_report()
print(report)
```

#### Engagement Report:
```python
from src.emotion_analysis.analyzer import ClassroomAnalytics

analytics = ClassroomAnalytics()
# ... after session ...
report = analytics.generate_report()
print(report)
```

---

## 🔧 Configuration

### Liveness Detection
```python
LIVENESS_CONFIG = {
    "EAR_THRESHOLD": 0.25,        # Eye aspect ratio threshold
    "CONSECUTIVE_FRAMES": 3,       # Frames to confirm blink
    "BLINK_TIME_WINDOW": 10,       # Seconds to verify liveness
    "MIN_BLINKS": 1,               # Minimum required blinks
    "MAX_BLINKS": 5,               # Maximum allowed blinks
}
```

### Face Recognition
```python
FACE_CONFIG = {
    "TOLERANCE": 0.6,              # Lower = stricter (0.4-0.7 recommended)
    "MODEL": "hog",                # 'hog' (CPU) or 'cnn' (GPU)
    "JITTERS": 1,                  # Re-sampling count (higher = more accurate, slower)
    "MIN_FACE_SIZE": (80, 80),     # Minimum face dimensions
}
```

### Geofencing
```python
GEOFENCE_CONFIG = {
    "RADIUS_METERS": 100,          # Attendance radius
    "CLASSROOM_LOCATIONS": {
        "Room_101": {"lat": 18.5204, "lon": 73.8567},
    }
}
```

---

## 🔐 Security Features

| Feature | Description | Protection Level |
|---------|-------------|------------------|
| Eye Blink Detection | Detects natural eye blinks | High |
| Texture Analysis | Identifies screen patterns | High |
| Challenge-Response | Random action verification | Very High |
| Geofencing | Location-based verification | High |
| GPS Spoofing Detection | Detects fake GPS | Medium |
| Multiple Face Detection | Prevents proxy attempts | High |
| Lighting Analysis | Detects unnatural lighting | Medium |
| Motion Analysis | Verifies natural movement | High |

---

## 📊 Database Schema

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    student_id TEXT UNIQUE,
    name TEXT,
    roll_number TEXT UNIQUE,
    email TEXT,
    phone TEXT,
    registered_at TIMESTAMP
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    student_id TEXT,
    classroom TEXT,
    timestamp TIMESTAMP,
    latitude REAL,
    longitude REAL,
    liveness_verified BOOLEAN,
    face_confidence REAL,
    emotion TEXT
);
```

### Fraud Attempts Table
```sql
CREATE TABLE fraud_attempts (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP,
    student_id TEXT,
    fraud_type TEXT,
    details TEXT,
    image_path TEXT,
    severity TEXT
);
```

---

## 📱 API Integration (Future)

### REST API Endpoints (Planned)
```
POST /api/attendance/mark
GET  /api/attendance/history/{student_id}
GET  /api/reports/daily/{date}
GET  /api/fraud/attempts
POST /api/students/register
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- OpenCV for computer vision capabilities
- dlib for facial landmark detection
- face_recognition library for face encoding
- TensorFlow/Keras for deep learning models
- Telegram Bot API for notifications
- Twilio for SMS notifications

---

## 📞 Support

For support, email support@smartattendai.com or join our [Discord server](https://discord.gg/smartattendai).

---

## 🗺️ Roadmap

- [ ] Web-based admin dashboard
- [ ] Mobile app (iOS/Android)
- [ ] Voice verification integration
- [ ] Multi-camera support
- [ ] Cloud deployment guide
- [ ] Docker containerization
- [ ] Advanced analytics dashboard
- [ ] Parent portal
- [ ] Integration with LMS platforms

---

## ⚠️ Disclaimer

This system is designed for educational and professional attendance tracking. Ensure compliance with local privacy laws and obtain necessary consents before deployment. The system stores biometric data (face encodings) which may be subject to GDPR, CCPA, or other privacy regulations.

---

## 🔗 Useful Links

- [Documentation](https://docs.smartattendai.com)
- [Tutorial Videos](https://youtube.com/smartattendai)
- [Community Forum](https://community.smartattendai.com)
- [Bug Reports](https://github.com/yourusername/SmartAttendAI/issues)

---

**Made with ❤️ for better education**