# SmartAttendAI - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Installation (2 minutes)

```bash
# Clone the repository
git clone https://github.com/yourusername/SmartAttendAI.git
cd SmartAttendAI

# Run automated setup
python setup.py
```

The setup script will:
- ✅ Check Python version
- ✅ Create directory structure
- ✅ Install all dependencies
- ✅ Download required AI models
- ✅ Initialize database
- ✅ Create configuration templates

### Step 2: Configuration (1 minute)

Edit `.env` file with your credentials:

```env
# Optional: For notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
```

**Note**: Notifications are optional. The system works without them!

### Step 3: Register Students (2 minutes)

#### Option A: Single Student
```python
from src.face_recognition.recognizer import FaceRecognitionSystem
from config.settings import FACE_CONFIG

face_system = FaceRecognitionSystem(FACE_CONFIG)

face_system.register_face(
    image_path="path/to/photo.jpg",
    student_name="John Doe",
    student_id="STU001",
    roll_number="22001",
    email="john@example.com",
    phone="+1234567890"
)
```

#### Option B: Bulk Import via CSV
```python
from src.face_recognition.recognizer import register_bulk_students

register_bulk_students(face_system, "students.csv")
```

CSV Format:
```csv
name,id,roll_number,email,phone,image_path
John Doe,STU001,22001,john@example.com,+1234567890,data/faces/john.jpg
```

### Step 4: Run the System

#### Option A: Command Line Interface
```bash
python main.py
```

Follow the on-screen prompts to mark attendance.

#### Option B: Web Interface
```bash
python app.py
```

Then open: http://localhost:8000

---

## 🎯 Common Tasks

### Task 1: Mark Attendance
```bash
python main.py
# Follow prompts:
# 1. Position face in front of camera
# 2. Blink naturally
# 3. Wait for face recognition
# 4. Done!
```

### Task 2: View Today's Attendance
```python
from src.utils.database import AttendanceDatabase
from datetime import date

db = AttendanceDatabase()
records = db.get_attendance_by_date(str(date.today()))

for record in records:
    print(f"{record['name']} - {record['time']}")
```

### Task 3: Generate Daily Report
```python
report = db.generate_daily_report(str(date.today()))
print(f"Total Present: {report['total_present']}")
print(f"Avg Confidence: {report['avg_face_confidence']}")
```

### Task 4: Check Fraud Attempts
```python
from src.fraud_detection.detector import FraudAnalytics

analytics = FraudAnalytics(db)
report = analytics.generate_fraud_report()
print(f"Fraud Attempts (30 days): {report['last_30_days']['total_attempts']}")
```

---

## 📱 Using the Web Interface

1. **Home Page** (`/`)
   - Overview of system features
   - Live statistics
   - Quick access to all functions

2. **Mark Attendance** (`/mark-attendance`)
   - Camera-based attendance
   - Real-time liveness detection
   - Instant feedback

3. **Dashboard** (`/dashboard`)
   - Today's attendance summary
   - Student list
   - Recent activity
   - Reports and analytics

4. **Admin Panel** (Coming Soon)
   - Student management
   - Classroom configuration
   - Fraud attempt review
   - System settings

---

## ⚙️ Customization

### Adjust Geofence Radius

Edit `config/settings.py`:
```python
GEOFENCE_CONFIG = {
    "RADIUS_METERS": 150,  # Changed from 100 to 150 meters
}
```

### Add New Classroom

```python
GEOFENCE_CONFIG = {
    "CLASSROOM_LOCATIONS": {
        "Room_101": {"lat": 18.5204, "lon": 73.8567},
        "Lab_B": {"lat": 18.5244, "lon": 73.8607},  # New classroom
    }
}
```

### Adjust Face Recognition Strictness

```python
FACE_CONFIG = {
    "TOLERANCE": 0.5,  # Lower = stricter (default: 0.6)
}
```

### Change Liveness Detection Sensitivity

```python
LIVENESS_CONFIG = {
    "EAR_THRESHOLD": 0.23,  # Lower = more sensitive (default: 0.25)
    "MIN_BLINKS": 2,        # More blinks required (default: 1)
}
```

---

## 🐛 Troubleshooting

### Problem: Camera not working
**Solution**: 
```python
# Test camera
import cv2
cap = cv2.VideoCapture(0)  # Try 0, 1, or 2
ret, frame = cap.read()
print("Camera working!" if ret else "Camera failed!")
```

### Problem: Face not recognized
**Solution**:
1. Check photo quality (clear, well-lit, single face)
2. Re-register student with better photo
3. Lower tolerance: `TOLERANCE = 0.7` (less strict)

### Problem: Liveness detection fails
**Solution**:
1. Ensure good lighting
2. Look directly at camera
3. Blink naturally (not too fast)
4. Adjust `EAR_THRESHOLD` if needed

### Problem: GPS accuracy poor
**Solution**:
1. Enable high-accuracy GPS
2. Increase `RADIUS_METERS`
3. Wait for GPS to stabilize

---

## 📊 Sample Output

### Successful Attendance
```
============================================================
SESSION STARTED
============================================================
Session ID: SESSION_20240226_093000
Classroom: Room_101
Subject: Machine Learning
Teacher: Dr. Smith
============================================================

[1/5] Validating location...
  ✓ Within geofence (45.2m from classroom)

[2/5] Verifying liveness...
  EAR: 0.28
  Blinks: 2
  ✓ Liveness verified (blinks: 2)

[3/5] Challenge-response skipped

[4/5] Recognizing face...
  ✓ Recognized: John Doe (0.95)

[5/5] Running fraud detection...
  ✓ No fraud detected

============================================================
ALL CHECKS PASSED ✓
============================================================

✓ Attendance marked for John Doe
  Time: 09:35:42 AM
  Location: (18.5205, 73.8568)
  Classroom: Room_101
```

---

## 🎓 Next Steps

1. **Read Full Documentation**: `docs/DOCUMENTATION.md`
2. **Explore API**: `docs/API.md` (coming soon)
3. **Watch Tutorial Videos**: YouTube channel (coming soon)
4. **Join Community**: Discord server (link in README)
5. **Contribute**: Check `CONTRIBUTING.md` for guidelines

---

## 💡 Pro Tips

1. **Batch Registration**: Use CSV import for 50+ students
2. **Backup Database**: Regular backups of `data/smartattend.db`
3. **Monitor Fraud**: Check fraud reports weekly
4. **Update Models**: Keep AI models up-to-date
5. **Test Geofence**: Verify classroom coordinates before deployment

---

## 📞 Need Help?

- 📧 Email: support@smartattendai.com
- 💬 Discord: https://discord.gg/smartattendai
- 🐛 Report Bug: GitHub Issues
- 📖 Documentation: `docs/`

---

**Happy Attendance Tracking! 🎉**