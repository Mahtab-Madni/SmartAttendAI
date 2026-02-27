# SmartAttendAI - Quick Start Guide

## Getting Started (5 Minutes)

### 1. Install Dependencies

```bash
cd c:\Users\mahta\OneDrive\Desktop\SmartAttendAI
pip install dlib opencv-python scipy imutils face_recognition
```

### 2. Start the Server

```bash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

✅ Server running: `http://localhost:8000`

---

## Using the Attendance System

### Access the Attendance Page

```
http://localhost:8000/mark-attendance
```

### Complete Verification Flow (6 Steps)

#### **Step 1: Select Student & Get GPS**

1. Click "Get GPS Location"
2. Allow browser location access
3. Confirm location shows: Latitude, Longitude, Accuracy

#### **Step 2: Capture Face**

1. Click "Start Camera" (allow camera permissions)
2. Position face in center
3. Click "Capture Face"

#### **Step 3: Liveness Check** (5 seconds)

1. Click "Start Liveness Check"
2. Look naturally at camera for 5 seconds
3. Watch for real-time blink counting:
   - Total Blinks: 3
   - Blinks/5s: 3
4. System verifies: Blinks are natural (not a photo)

#### **Step 4: Challenge** (Optional, 3 seconds)

1. Click "Start Challenge"
2. Follow instruction: "Smile" or "Turn head left" etc.
3. System detects action
4. Confidence score shown

#### **Step 5: Submit**

1. Click "Submit & Mark Attendance"
2. All data verified automatically
3. See success/failure message

#### **Step 6: Database**

1. Check database:

```bash
sqlite3 data/smartattend.db
SELECT * FROM attendance ORDER BY timestamp DESC LIMIT 5;
```

---

## Test Student Setup (30 seconds)

### Register a Test Student

#### Option A: Via API

```bash
curl -X POST http://localhost:8000/api/students/register \
  -F "name=John Doe" \
  -F "student_id=STU001" \
  -F "roll_number=22001" \
  -F "email=john@example.com" \
  -F "photo=@/path/to/face.jpg"
```

#### Option B: Via Registration Page

1. Go to `http://localhost:8000/`
2. Click "Register Student"
3. Provide info + clear photo (frontfacing)
   email="john@example.com",
   phone="+1234567890"
   )

````

#### Option B: Bulk Import via CSV
```python
from src.face_recognition.recognizer import register_bulk_students

register_bulk_students(face_system, "students.csv")
````

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
