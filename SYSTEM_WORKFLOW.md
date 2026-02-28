# SmartAttendAI System Workflow

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    SmartAttendAI System                       │
└──────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
            ┌───▼──┐      ┌───▼──┐     ┌───▼──┐
            │ Web  │      │ Mobile│    │ API  │
            │  UI  │      │  App  │    │Server│
            └──────┘      └───────┘    └──────┘
                              │
                         ┌────▼────┐
                         │ FastAPI │
                         │   App   │
                         └────┬────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌───▼────┐          ┌────▼────┐         ┌─────▼─────┐
    │  Auth  │          │ Session │         │ Real-time │
    │Handler │          │Management        │ Updates   │
    └────────┘          └────┬────┘         └───────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
    ┌───▼─────────┐   ┌──────▼──────┐    ┌─────────▼────┐
    │   Core      │   │  Analytics   │    │ Storage &    │
    │   Security  │   │   Engine     │    │ Sync         │
    │   Modules   │   └──────────────┘    └──────────────┘
    └─────────────┘
```

## Attendance Marking Workflow (Main Flow)

```
START (Student Opens App)
    │
    ├─→ [1] USER AUTHENTICATION
    │       ├─ Login/Signup
    │       └─ Session Creation
    │
    ├─→ [2] GEOFENCING CHECK ⚠️
    │       ├─ Get GPS Coordinates
    │       ├─ Calculate Distance (Haversine Formula)
    │       ├─ Verify Classroom Proximity (100m radius)
    │       └─ Detect GPS Spoofing
    │           └─ FAIL → Fraud Alert & Block
    │
    ├─→ [3] CAMERA & LIVENESS DETECTION ⚠️
    │       ├─ Start Video Capture
    │       ├─ EYE ASPECT RATIO (EAR) Detection
    │       │   └─ Calculate EAR from eye landmarks
    │       ├─ BLINK DETECTION
    │       │   ├─ Min blinks: 1, Max blinks: 5
    │       │   └─ Time window: 10 seconds
    │       ├─ TEXTURE ANALYSIS (CNN Model)
    │       │   └─ Detect screen/photo artifacts
    │       └─ Result: LIVE or SPOOF
    │           └─ FAIL → Block & Log Fraud
    │
    ├─→ [4] FACE RECOGNITION ⚠️
    │       ├─ Extract Face Encoding (Face128d)
    │       ├─ Match Against Database
    │       │   ├─ Load stored face encodings
    │       │   ├─ Calculate cosine similarity
    │       │   └─ Confidence threshold: 0.6
    │       └─ Verify Student Identity
    │           └─ FAIL → Rejection & Log Attempt
    │
    ├─→ [5] CHALLENGE-RESPONSE (Optional) ⚠️
    │       ├─ Generate Random Challenge
    │       │   ├─ Smile for 3 seconds
    │       │   ├─ Turn head left/right
    │       │   └─ Blink 5 times
    │       └─ Verify Response
    │           └─ FAIL → Suspicious Behavior Logged
    │
    ├─→ [6] MULTI-LAYER FRAUD DETECTION ⚠️
    │       ├─ Photo/Screen Attack Detection
    │       ├─ Multiple Face Detection
    │       ├─ Face Size Validation
    │       ├─ Lighting Anomaly Analysis
    │       ├─ Motion Pattern Verification
    │       └─ Severity: HIGH/MEDIUM/LOW
    │           └─ HIGH → Immediate Alert
    │
    ├─→ [7] EMOTION & ENGAGEMENT ANALYSIS 📊
    │       ├─ Detect Emotion
    │       │   ├─ Happy, Sad, Angry, Surprise
    │       │   ├─ Fear, Disgust, Neutral
    │       │   └─ Using CNN model
    │       ├─ Calculate Engagement Score (0-100)
    │       └─ Store Time-Segmented Data
    │
    ├─→ [8] DATABASE RECORDING 💾
    │       ├─ Store Attendance Record
    │       │   ├─ Student ID, Timestamp
    │       │   ├─ Classroom, Status
    │       │   ├─ Location (Lat/Long)
    │       │   └─ Confidence Scores
    │       ├─ Store Fraud Flags
    │       ├─ Store Emotion Data
    │       └─ Create Offline Queue (if no internet)
    │
    └─→ [9] NOTIFICATIONS & SYNC 📬
            ├─ Send Telegram Notification
            ├─ Optional SMS via Twilio
            ├─ Dashboard Update
            └─ Sync Data (if offline)
                └─ Queue stored, syncs when online

END (Attendance Marked Successfully)
```

## Core Security Modules

| Module                   | Purpose                       | Key Functions                                       |
| ------------------------ | ----------------------------- | --------------------------------------------------- |
| **Liveness Detector**    | Prevent photo/video attacks   | Eye blink detection, texture analysis               |
| **Face Recognition**     | Student identity verification | Face encoding matching, confidence scoring          |
| **Geofencing**           | Location validation           | GPS validation, spoofing detection                  |
| **Fraud Detector**       | Multi-layer threat detection  | Photo detection, lighting analysis, motion patterns |
| **Emotion Analyzer**     | Student engagement tracking   | 7-emotion classification, engagement scoring        |
| **Notification Manager** | Real-time alerts              | Telegram, SMS, dashboard updates                    |
| **Offline Sync**         | Data persistence              | Queue management, auto-sync when online             |

## Key API Endpoints

**Authentication:**

- `POST /api/admin/login` - Admin login
- `POST /api/admin/signup` - Admin registration
- `POST /api/students/register` - Register student faces

**Attendance:**

- `POST /api/attendance/mark` - Mark attendance (basic)
- `POST /api/attendance/mark-comprehensive` - Full verification flow
- `GET /api/attendance/history/{student_id}` - View attendance history

**Security:**

- `POST /api/geofence/validate` - Validate location
- `POST /api/challenge/request` - Request challenge action
- `POST /api/challenge/validate` - Validate challenge response
- `POST /api/recognize-face` - Face recognition check

**Data:**

- `GET /api/students` - List all registered students
- `GET /emotion-analytics` - Emotion analytics dashboard

## Data Flow Diagram

```
User Input (Face/Location)
        │
        ▼
┌─────────────────────────────────────┐
│   Security & Validation Layer       │
│  ┌─ Geofencing                      │
│  ├─ Liveness Detection              │
│  ├─ Face Recognition                │
│  └─ Fraud Detection                 │
└──────────────┬──────────────────────┘
               │
        ✓(PASS) │ ✗(FAIL)
           │         │
           ▼         ▼
      ┌─────────┬──────────┐
      │ Accept  │  Reject  │
      └────┬────┴─────┬────┘
           │          │
           ▼          ▼
    ┌────────────┐ ┌──────────┐
    │ Attendance │ │ Fraud    │
    │ Database   │ │ Database │
    └────┬───────┘ └────┬─────┘
         │               │
         ├───────┬───────┘
         │       │
         ▼       ▼
    ┌─────────────────────┐
    │  Emotion Analytics  │
    │  & Notifications    │
    └─────────────────────┘
         │
         ▼
    ┌──────────────┐
    │  Dashboard   │
    │  & Reports   │
    └──────────────┘
```

## Session Management Flow

1. **Session Start** → Teacher/Admin creates attendance session
2. **Classroom Setup** → Geofence coordinates defined
3. **Student Attendance** → Each student goes through full workflow
4. **Emotion Collection** → Real-time emotion tracking throughout session
5. **Session End** → Compile analytics and generate reports
6. **Notifications** → Send summary to teacher via Telegram

## Offline Mode Flow

```
No Internet Connection Detected
    │
    ├─→ Continue normal workflow
    ├─→ Store data in LOCAL QUEUE
    ├─→ Show "Offline Mode" indicator
    │
Internet Restored
    │
    └─→ SYNC SERVICE ACTIVATED
        ├─ Process queued records
        ├─ Upload to main database
        ├─ Update analytics
        └─ Clear offline queue
```

## Component Interaction Flow

### 1. Geofencing Module (`src/geofencing/validator.py`)

```
Student Location Input
    │
    ├─→ Haversine Distance Calculation
    │   └─ Compares GPS coords with classroom location
    │
    ├─→ Classroom Validation
    │   └─ Check against registered geofence boundaries
    │
    └─→ Spoofing Detection
        └─ Analyzes location patterns for anomalies
```

### 2. Liveness Detection Module (`src/liveness/detector.py`)

```
Video Frame Input
    │
    ├─→ Face Landmark Detection
    │   └─ Identifies eye positions
    │
    ├─→ EAR Calculation
    │   └─ (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    │
    ├─→ Blink Counter
    │   └─ Tracks consecutive blinks (threshold: 1-5)
    │
    ├─→ Texture Analysis (CNN Model)
    │   └─ Detects screen/photo patterns
    │
    └─→ Final Verdict: LIVE or SPOOF
```

### 3. Face Recognition Module (`src/face_recognition/recognizer.py`)

```
Face Frame Input
    │
    ├─→ Face Encoding Extraction
    │   └─ Creates 128-dimensional vector
    │
    ├─→ Database Lookup
    │   └─ Loads registered student encodings
    │
    ├─→ Cosine Similarity Matching
    │   └─ Calculates match confidence
    │
    └─→ Identity Verification
        ├─ MATCHED (confidence > 0.6)
        └─ NOT MATCHED (confidence < 0.6)
```

### 4. Fraud Detection Module (`src/fraud_detection/detector2.py`)

```
Multiple Signals Input
    │
    ├─→ Photo Attack Detection
    ├─→ Multiple Face Detection
    ├─→ Face Size Validation
    ├─→ Lighting Analysis
    ├─→ Motion Pattern Verification
    │
    └─→ Risk Assessment
        ├─ HIGH Severity → Immediate Block & Alert
        ├─ MEDIUM Severity → Log & Monitor
        └─ LOW Severity → Record & Monitor
```

### 5. Emotion Analytics Module (`src/emotion_detection/analyzer.py`)

```
Video Frames Input
    │
    ├─→ Emotion Classification (CNN Model)
    │   ├─ Happy
    │   ├─ Sad
    │   ├─ Angry
    │   ├─ Surprise
    │   ├─ Fear
    │   ├─ Disgust
    │   └─ Neutral
    │
    ├─→ Engagement Scoring
    │   └─ Calculates 0-100 engagement level
    │
    ├─→ Time-Segmented Analysis
    │   └─ Tracks emotion changes over session
    │
    └─→ Analytics Storage
        └─ Classroom-level insights & recommendations
```

## Database Schema Overview

**Students Table:**

- `student_id` (PK)
- `name`
- `email`
- `enrollment_date`
- Face encodings (pickled)

**Attendance Table:**

- `attendance_id` (PK)
- `student_id` (FK)
- `session_id` (FK)
- `timestamp`
- `status` (present/absent/fraud)
- `confidence_score`
- `location` (lat/long)

**Fraud Table:**

- `fraud_id` (PK)
- `student_id` (FK)
- `fraud_type`
- `severity` (high/medium/low)
- `details`
- `timestamp`

**Sessions Table:**

- `session_id` (PK)
- `classroom`
- `subject`
- `teacher_name`
- `start_time`
- `end_time`

**Emotions Table:**

- `emotion_id` (PK)
- `session_id` (FK)
- `student_id` (FK)
- `emotion_type`
- `confidence`
- `timestamp`
- `engagement_score`

## Security Hierarchy

```
Level 1: AUTHENTICATION
├─ Student ID verification
├─ Password-based login
└─ Session token validation

Level 2: LOCATION VERIFICATION (Geofencing)
├─ GPS coordinate validation
├─ Distance calculation (100m radius)
└─ Spoofing pattern detection

Level 3: LIVENESS VERIFICATION
├─ Eye blink detection (EAR analysis)
├─ Texture analysis (CNN)
└─ Challenge-response (optional)

Level 4: IDENTITY VERIFICATION (Face Recognition)
├─ Face encoding extraction
├─ Database matching (cosine similarity)
└─ Confidence threshold check (0.6)

Level 5: BEHAVIORAL ANALYSIS
├─ Motion pattern verification
├─ Lighting consistency check
├─ Multiple face detection
└─ Face size validation

Level 6: ENGAGEMENT VERIFICATION
├─ Emotion detection
├─ Engagement scoring
└─ Anomaly detection

Level 7: FORENSICS & LOGGING
├─ Complete event logging
├─ Fraud attempt documentation
├─ Alert generation
└─ Evidence capture
```

## Notification Flow

```
Attendance Recorded
    │
    ├─→ Telegram Bot Notification
    │   └─ Sends attendance confirmation with details
    │
    ├─→ SMS Alert (Optional)
    │   └─ Via Twilio integration
    │
    ├─→ Dashboard Update
    │   └─ Real-time UI refresh with new record
    │
    └─→ Fraud Alert (if triggered)
        └─ Immediate notification to admin/teacher
```

## Offline & Sync Flow

```
Attendance Attempt While Offline
    │
    ├─→ Process normally (all validations work locally)
    ├─→ Store in OFFLINE_QUEUE table
    ├─→ Display "Offline Mode" badge
    │
Internet Connection Detected
    │
    ├─→ Activate Sync Service
    ├─→ Process queue in batches
    ├─→ Validate records before upload
    ├─→ Upload to main database
    ├─→ Update analytics engine
    ├─→ Send buffered notifications
    └─→ Clear queue & restart normal mode
```

## Error Handling & Fallback Flow

```
Attendance Marking Failure
    │
    ├─→ Geofence Check FAIL
    │   └─ Return: "Location Outside Classroom"
    │
    ├─→ Liveness Check FAIL
    │   └─ Return: "Not a Live Person Detected"
    │
    ├─→ Face Recognition FAIL
    │   └─ Return: "Identity Not Verified"
    │
    ├─→ Fraud Detection HIGH
    │   └─ Return: "Suspicious Activity Detected"
    │
    ├─→ Database Connection FAIL
    │   └─ Store in Offline Queue (if offline mode enabled)
    │
    └─→ General Error
        └─ Log to system and notify admin
```

This comprehensive workflow ensures secure, multi-layered attendance verification with real-time fraud detection and analytics.
