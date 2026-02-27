# SmartAttendAI 🎓

## Robust Attendance System with Liveness Detection & Geo-Fencing

SmartAttendAI is an advanced, AI-powered attendance system that eliminates proxy attendance through multiple layers of security including liveness detection, face recognition, geofencing, and emotion analytics. It features a web-based dashboard for real-time attendance management and comprehensive fraud detection.

---

## 🌟 Key Features

### 1. **Advanced Liveness Detection (Anti-Spoofing)**

- **Eye Blink Detection**: Uses Eye Aspect Ratio (EAR) calculation to ensure natural blinking
- **Texture Analysis**: CNN-based detection of screen patterns and photo artifacts
- **Challenge-Response**: Random action prompts (smile, turn head) to defeat pre-recorded videos
- **Real-time spoofing detection** during attendance marking

### 2. **Robust Face Recognition**

- High-accuracy face matching against authorized database
- Confidence scoring for each recognition
- Support for multiple students per session
- Efficient encoding storage and retrieval
- Comprehensive face database management

### 3. **Geofencing Security**

- GPS-based location verification (100m radius default)
- Multiple classroom support
- GPS spoofing detection
- Location consistency verification

### 4. **Emotion & Engagement Analytics**

- Real-time emotion detection (7 emotion categories)
- Engagement scoring (0-100)
- Time-segmented analysis
- Teacher insights and recommendations
- Emotion analytics dashboard and visualizations

### 5. **Comprehensive Fraud Detection**

- Photo/screen attack detection
- Multiple face detection prevention
- Lighting anomaly analysis
- Motion pattern verification
- Automated evidence capture and logging
- Detailed fraud analytics and reporting

### 6. **Instant Notifications**

- Telegram bot integration
- SMS via Twilio
- Real-time attendance confirmations
- Fraud alerts and security notifications
- Daily summaries and reports

### 7. **Offline Mode & Sync**

- Local data storage during internet outage
- Automatic synchronization when online
- Queue management for pending records
- Reliable data persistence

### 8. **Web-Based Dashboard**

- User-friendly interface for student login and attendance marking
- Real-time attendance status
- Analytics and engagement tracking
- Fraud detection overview
- Admin dashboard for system management

---

## 🏗️ Project Structure

```
SmartAttendAI/
├── app.py                       # Flask web application
├── main.py                      # Main application entry point
├── setup.py                     # Package setup configuration
├── requirements.txt             # Project dependencies
├── DOCUMENTATION.md             # Detailed documentation
├── QUICKSTART.md                # Quick start guide
│
├── config/                      # Configuration module
│   ├── settings.py              # Main settings
│   ├── production_config.py     # Production settings
│   ├── dev_setup.py             # Development setup
│   └── data/                    # Config data directory
│       ├── faces/               # Face encoding cache
│       └── logs/                # System logs
│
├── src/                         # Application source code
│   ├── liveness/                # Liveness detection module
│   │   ├── detector.py          # Liveness detection logic
│   │   └── challenge.py         # Challenge-response system
│   │
│   ├── face_recognition/        # Face recognition module
│   │   └── recognizer.py        # Face recognition engine
│   │
│   ├── geofencing/              # Geofencing module
│   │   └── validator.py         # Location validation
│   │
│   ├── emotion_detection/       # Emotion detection module
│   │   └── analyzer.py          # Emotion analysis engine
│   │
│   ├── fraud_detection/         # Fraud detection module
│   │   └── detector2.py         # Fraud detection logic
│   │
│   └── utils/                   # Utility modules
│       ├── database.py          # Database operations
│       ├── notifications.py     # Notification service
│       ├── fraud_alert_service.py # Fraud alerts
│       ├── emotion_analytics.py # Emotion analytics
│       ├── offline_sync.py      # Offline synchronization
│       ├── sync_service.py      # Sync service
│       └── simple_emotion_detector.py # Simple emotion detection
│
├── models/                      # AI/ML models
│   ├── emotion_model.h5         # Emotion detection model
│   ├── spoof_detection_model.h5 # Spoofing detection model
│   └── [dlib predictor]         # Face landmarks predictor
│
├── data/                        # Data storage
│   ├── sample_students.csv      # Sample student data
│   ├── faces/                   # Student face images
│   │   └── metadata.json        # Face metadata
│   ├── fraud_attempts/          # Fraud incident logs
│   └── logs/                    # Application logs
│
├── templates/                   # HTML templates
│   ├── index.html               # Home page
│   ├── login.html               # Login page
│   ├── signup.html              # Student registration
│   ├── mark_attendance.html     # Attendance marking interface
│   ├── dashboard.html           # Admin dashboard
│   ├── emotion_analytics.html   # Emotion analytics page
│   └── fraud_details.html       # Fraud details page
│
├── static/                      # Static assets
│   ├── css/
│   │   └── style.css            # Application styles
│   └── js/
│       ├── app.js               # Main application script
│       ├── attendance.js        # Attendance module
│       └── attendance_automated.js # Automated attendance
│
└── tests/                       # Test modules
    ├── dev_server.py            # Development server
    ├── check_db.py              # Database checks
    ├── check_students.py        # Student data checks
    └── test_telegram.py         # Telegram integration tests
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Webcam/camera device
- Microphone (for notifications)
- pip package manager
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/SmartAttendAI.git
cd SmartAttendAI
```

### Step 2: Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download Required Models

The project uses pre-trained models for face detection and emotion analysis. These are stored in the `models/` directory:

- `emotion_model.h5` - Emotion detection model
- `spoof_detection_model.h5` - Face spoofing detection model
- `shape_predictor_68_face_landmarks.dat` - dlib facial landmarks (download if missing)

To download dlib landmarks:

```bash
# Windows PowerShell
$url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
$output = "models/shape_predictor_68_face_landmarks.dat.bz2"
Invoke-WebRequest -Uri $url -OutFile $output

# Then extract the file (requires 7-Zip or similar)
```

### Step 5: Configure Application Settings

Edit `config/settings.py` with your configuration:

```python
# Database settings
DATABASE_PATH = "data/attendance.db"

# Geofencing
GEOFENCE_CONFIG = {
    "RADIUS_METERS": 100,
    "CLASSROOM_LOCATIONS": {
        "Room_101": {"lat": 18.5204, "lon": 73.8567},
        "Lab_A": {"lat": 18.5224, "lon": 73.8587},
    }
}

# Face Recognition
FACE_CONFIG = {
    "TOLERANCE": 0.6,
    "MODEL": "hog",  # 'hog' for CPU, 'cnn' for GPU
    "JITTERS": 1,
}

# Liveness Detection
LIVENESS_CONFIG = {
    "EAR_THRESHOLD": 0.25,
    "CONSECUTIVE_FRAMES": 3,
    "BLINK_TIME_WINDOW": 10,
    "MIN_BLINKS": 1,
    "MAX_BLINKS": 5,
}
```

### Step 6: Environment Variables

Create a `.env` file in the root directory:

```env
# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Twilio SMS (Optional)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Flask Settings
SECRET_KEY=your_secret_key_here
DEBUG=False
FLASK_ENV=production
```

### Step 7: Initialize Database

```bash
python setup_models.py
```

---

## 🎯 Quick Start

### Option 1: Web Interface (Recommended)

**Start the Flask application:**

```bash
python app.py
```

Access the application at `http://localhost:5000`

**User flows:**

1. **Student Registration** → Sign up page (`/signup`)
2. **Student Login** → Login page (`/login`)
3. **Mark Attendance** → Attendance marking interface (`/mark_attendance`)
4. **View Dashboard** → Attendance dashboard (`/dashboard`)
5. **View Analytics** → Emotion analytics (`/emotion_analytics`)

### Option 2: Command Line

**Run main application:**

```bash
python main.py
```

This starts the interactive attendance system with direct camera access.

### Option 3: Development/Testing

**Start development server:**

```bash
python tests/dev_server.py
```

---

## 📖 Usage Guide

### 1. Register Students

#### Method A: Web Interface

- Go to signup page: `http://localhost:5000/signup`
- Enter student details (name, ID, email, phone)
- Upload/capture student photo
- System automatically creates face encoding

#### Method B: CSV Bulk Import

```python
from src.face_recognition.recognizer import FaceRecognitionSystem

system = FaceRecognitionSystem()
system.register_bulk_students("data/sample_students.csv")
```

**CSV Format:**

```csv
name,student_id,roll_number,email,phone,image_path
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

**Via Web Interface:**

1. Teacher logs in with admin credentials
2. Selects classroom and subject
3. Clicks "Start Session"
4. Students mark attendance via `/mark_attendance`

**Via Python:**

```python
from main import SmartAttendAI
from src.geofencing.validator import Location

system = SmartAttendAI()
session = system.start_session(
    session_id="SESSION_001",
    classroom="Room_101",
    subject="Machine Learning",
    teacher_name="Dr. Smith"
)
```

### 4. Mark Attendance

**Student performs:**

1. **Face Recognition** - Camera captures and recognizes face
2. **Liveness Detection** - Performs eye blink and challenge-response
3. **Location Verification** - GPS coordinates validated against classroom
4. **Emotion Detection** - Analyzes student engagement (optional)

### 5. View Reports & Analytics

**Dashboard:**

- Real-time attendance status
- Student presence/absence records
- Engagement metrics

**Fraud Analytics Page:**

- Detected fraud attempts
- Security incident logs
- Suspicious activity patterns

**Emotion Analytics:**

- Class engagement average
- Per-student emotion tracking
- Engagement recommendations

---

## 📊 Module Reference

### Liveness Detection (`src/liveness/`)

- **detector.py** - Main liveness detection logic using eye aspect ratio and CNN
- **challenge.py** - Challenge-response system for additional verification

### Face Recognition (`src/face_recognition/`)

- **recognizer.py** - Face registration and matching using deep learning

### Geofencing (`src/geofencing/`)

- **validator.py** - GPS-based location verification and spoofing detection

### Emotion Detection (`src/emotion_detection/`)

- **analyzer.py** - Real-time emotion classification and engagement scoring

### Fraud Detection (`src/fraud_detection/`)

- **detector2.py** - Multi-layer fraud detection and prevention

### Utilities (`src/utils/`)

- **database.py** - SQLite database operations
- **notifications.py** - Telegram and SMS notifications
- **fraud_alert_service.py** - Fraud incident alerts
- **emotion_analytics.py** - Emotion data analysis
- **offline_sync.py** - Offline-online synchronization
- **sync_service.py** - Data synchronization service

---

## 🔧 Configuration Details

### Liveness Detection Configuration

```python
LIVENESS_CONFIG = {
    "EAR_THRESHOLD": 0.25,          # Eye aspect ratio threshold
    "CONSECUTIVE_FRAMES": 3,         # Frames to confirm blink
    "BLINK_TIME_WINDOW": 10,         # Seconds to verify liveness
    "MIN_BLINKS": 1,                 # Minimum required blinks
    "MAX_BLINKS": 5,                 # Maximum allowed blinks
    "CHALLENGE_TIMEOUT": 30,         # Seconds for challenge completion
}
```

### Face Recognition Configuration

```python
FACE_CONFIG = {
    "TOLERANCE": 0.6,                # Lower = stricter (0.4-0.7 recommended)
    "MODEL": "hog",                  # 'hog' (CPU) or 'cnn' (GPU)
    "JITTERS": 1,                    # Re-sampling count (higher = more accurate, slower)
    "MIN_FACE_SIZE": (80, 80),       # Minimum face dimensions
    "ENCODING_MODEL": "small",       # 'tiny', 'small', or 'large'
}
```

### Geofencing Configuration

```python
GEOFENCE_CONFIG = {
    "RADIUS_METERS": 100,            # Attendance radius
    "ALLOW_NETWORK_LOCATION": True,  # Use network-based location if GPS unavailable
    "CLASSROOM_LOCATIONS": {
        "Room_101": {
            "lat": 18.5204,
            "lon": 73.8567,
            "name": "Main Classroom"
        },
    }
}
```

### Emotion Detection Configuration

```python
EMOTION_CONFIG = {
    "EMOTIONS": ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"],
    "CONFIDENCE_THRESHOLD": 0.5,
    "UPDATE_FREQUENCY": 5,           # Update emotion every 5 seconds
    "ENGAGEMENT_THRESHOLD": 0.6,
}
```

### Database Configuration

```python
DATABASE_CONFIG = {
    "TYPE": "sqlite",
    "PATH": "data/attendance.db",
    "BACKUP_INTERVAL": 3600,         # Backup every hour
    "LOG_RETENTION_DAYS": 90,        # Keep logs for 90 days
}
```

---

## 🔐 Security Architecture

### Multi-Layer Security

| Layer               | Technology            | Details                                   |
| ------------------- | --------------------- | ----------------------------------------- |
| **Biometric**       | Face Recognition      | Deep learning-based unique identification |
| **Liveness**        | Eye Blink + Challenge | Prevents photo/video spoofing             |
| **Location**        | GPS Geofencing        | Verify attendance location                |
| **Behavior**        | Emotion Analysis      | Detects unusual patterns                  |
| **Fraud Detection** | ML Models             | Real-time anomaly detection               |

### Fraud Detection Mechanisms

- **Photo Attack Detection** - Identifies attempts to use student photos
- **Screen Display Detection** - Detects attendance via screen display
- **Multiple Face Detection** - Prevents proxy attendance
- **Lighting Anomaly** - Identifies unnatural lighting conditions
- **Motion Analysis** - Verifies natural head/eye movements
- **GPS Spoofing Detection** - Validates location authenticity

---

## 📊 Database Schema

The application uses SQLite for data persistence. Key tables include:

### Students Table

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    student_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    roll_number TEXT UNIQUE,
    email TEXT,
    phone TEXT,
    face_encoding BLOB,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Attendance Table

```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    student_id TEXT NOT NULL,
    classroom TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latitude REAL,
    longitude REAL,
    liveness_verified BOOLEAN,
    face_confidence REAL,
    emotion TEXT,
    engagement_score REAL,
    FOREIGN KEY(student_id) REFERENCES students(student_id)
);
```

### Fraud Attempts Table

```sql
CREATE TABLE fraud_attempts (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    student_id TEXT,
    fraud_type TEXT,
    confidence REAL,
    details TEXT,
    image_path TEXT,
    severity TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id)
);
```

### Session Logs Table

```sql
CREATE TABLE session_logs (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    classroom TEXT,
    teacher_name TEXT,
    subject TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_students INTEGER,
    present_students INTEGER
);
```

---

## 🌐 Web Interface Pages

### Public Pages

- **`/`** - Home page with system overview
- **`/login`** - Student/Staff login
- **`/signup`** - Student registration

### User Pages

- **`/mark_attendance`** - Real-time attendance marking with camera
- **`/dashboard`** - Attendance records and status

### Analytics Pages

- **`/emotion_analytics`** - Class engagement and emotion analytics
- **`/fraud_details`** - Fraud incidents and security overview

### Static Assets

- **`static/css/style.css`** - Application styling
- **`static/js/app.js`** - Main application logic
- **`static/js/attendance.js`** - Attendance form handling
- **`static/js/attendance_automated.js`** - Automated attendance processing

---

## 🧪 Testing

Run tests from the `tests/` directory:

```bash
# Check database integrity
python tests/check_db.py

# Verify student data
python tests/check_students.py

# Test Telegram integration
python tests/test_telegram.py

# Run development server with test data
python tests/dev_server.py
```

---

## 📦 Dependencies

Key dependencies include:

- **OpenCV** - Computer vision operations
- **TensorFlow/Keras** - Deep learning models
- **dlib** - Facial landmark detection
- **face_recognition** - Face encoding and matching
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Telegram Bot API** - Notifications
- **Twilio** - SMS notifications
- **NumPy/SciPy** - Numerical computing

See `requirements.txt` for complete dependency list.

---

## 🚀 Deployment

### Local Development

```bash
python app.py
# Application runs on http://localhost:5000
```

### Production Deployment (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run production server
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment (Optional)

```bash
# Build Docker image (Dockerfile required)
docker build -t smartattendai .

# Run container
docker run -p 5000:5000 smartattendai
```

---

## 📄 Documentation

Detailed documentation available in:

- [DOCUMENTATION.md](DOCUMENTATION.md) - Complete technical documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [CODE_STRUCTURE.md](CODE_STRUCTURE.md) - Module-by-module guide

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/YourFeature`
3. Make your changes and commit: `git commit -m 'Add YourFeature'`
4. Push to the branch: `git push origin feature/YourFeature`
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation with changes
- Ensure all tests pass before submitting PR

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Project Team

- **Lead Developer** - [Your Name]
- **Contributor** - [Team Members]

---

## 🙏 Acknowledgments

This project was built with:

- **OpenCV** - Computer vision library
- **TensorFlow/Keras** - Deep learning framework
- **dlib** - Machine learning library
- **Flask** - Web framework
- **face_recognition** - Simplified face recognition library
- **Telegram Bot API** - Notification service
- **Twilio** - SMS communication

---

## 🐛 Known Issues & Limitations

- GPU acceleration requires CUDA-compatible hardware
- CNN face detection model requires significant computational resources
- GPS accuracy depends on device and location
- Emotion detection accuracy varies with lighting conditions

---

## 📞 Support & Contact

- **Email** - support@smartattendai.local
- **Issues** - [GitHub Issues](https://github.com/yourusername/SmartAttendAI/issues)
- **Discussions** - [GitHub Discussions](https://github.com/yourusername/SmartAttendAI/discussions)

---

## 🗺️ Roadmap

### Current Version (v1.0)

- ✅ Face recognition attendance
- ✅ Liveness detection
- ✅ Geofencing validation
- ✅ Emotion analytics
- ✅ Fraud detection
- ✅ Web dashboard

### Planned Features (v2.0)

- [ ] Mobile app (iOS/Android)
- [ ] Multi-camera support
- [ ] Voice-based verification
- [ ] Advanced analytics dashboard
- [ ] REST API endpoints
- [ ] Cloud integration
- [ ] Parent portal
- [ ] LMS integration
- [ ] Blockchain-based record verification
- [ ] Advanced encryption for biometric data

---

## ⚖️ Legal & Privacy

### Privacy Notice

This system collects and processes biometric data (facial images, face encodings). Deployment must comply with:

- **GDPR** (EU)
- **CCPA** (California, USA)
- **BIPA** (Illinois, USA)
- **Local privacy regulations** in your jurisdiction

Ensure you have:

- ✓ Explicit user consent for biometric collection
- ✓ Clear privacy policy
- ✓ Data retention policies
- ✓ User rights for data access/deletion

### Educational Use

- Recommended for K-12 and higher education institutions
- Parent/guardian consent required for students under 18
- Transparent communication about system usage
- Regular security audits recommended

---

## 📊 System Requirements

### Minimum

- **CPU**: Dual-core processor (Intel i5 or equivalent)
- **RAM**: 4 GB
- **Storage**: 2 GB
- **Camera**: 720p minimum
- **Internet**: For notifications and sync

### Recommended

- **CPU**: Quad-core processor (Intel i7 or equivalent)
- **RAM**: 8 GB
- **GPU**: NVIDIA CUDA-capable (for CNN models)
- **Storage**: 10 GB SSD
- **Camera**: 1080p or higher
- **Internet**: High-speed connection

### Supported Platforms

- Windows 10/11
- macOS 10.14+
- Ubuntu 18.04+ (or other Linux distributions)

---

**Made with ❤️ for smarter, more secure education**
