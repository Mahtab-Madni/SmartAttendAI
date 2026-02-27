"""
SmartAttendAI Web Application
FastAPI-based web interface for attendance management
"""
from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import cv2
import numpy as np
import base64
from datetime import datetime, date
import asyncio
import json

from config.settings import *
from src.utils.database import AttendanceDatabase
from src.face_recognition.recognizer import FaceRecognitionSystem
from src.geofencing.validator import GeofenceValidator, Location
from main import SmartAttendAI

# Initialize FastAPI app
app = FastAPI(
    title="SmartAttendAI",
    description="Robust Attendance System with Liveness Detection",
    version="1.0.0"
)

# Initialize system
db = AttendanceDatabase()
face_system = FaceRecognitionSystem(FACE_CONFIG)
geofence_validator = GeofenceValidator(GEOFENCE_CONFIG)
smart_attend = SmartAttendAI()

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class StudentRegistration(BaseModel):
    name: str
    student_id: str
    roll_number: str
    email: Optional[str] = ""
    phone: Optional[str] = ""

class AttendanceRequest(BaseModel):
    student_id: str
    classroom: str
    latitude: float
    longitude: float
    accuracy: float

class SessionCreate(BaseModel):
    session_id: str
    classroom: str
    subject: Optional[str] = None
    teacher_name: Optional[str] = None


# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Admin dashboard"""
    # Get today's statistics
    today = str(date.today())
    report = db.generate_daily_report(today)
    students = db.list_students()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "report": report,
        "total_students": len(students),
        "date": today
    })

@app.get("/mark-attendance", response_class=HTMLResponse)
async def mark_attendance_page(request: Request):
    """Attendance marking page"""
    classrooms = list(GEOFENCE_CONFIG["CLASSROOM_LOCATIONS"].keys())
    return templates.TemplateResponse("mark_attendance.html", {
        "request": request,
        "classrooms": classrooms
    })


# API Endpoints

@app.get("/api/students")
async def get_students():
    """Get list of all registered students"""
    students = db.list_students()
    return {"students": students}

@app.post("/api/students/register")
async def register_student(
    name: str = Form(...),
    student_id: str = Form(...),
    roll_number: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    photo: UploadFile = File(...)
):
    """Register a new student"""
    try:
        # Save uploaded photo
        photo_path = f"data/faces/{student_id}.jpg"
        contents = await photo.read()
        
        # Convert to image
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imwrite(photo_path, img)
        
        # Register face
        success = face_system.register_face(
            image_path=photo_path,
            student_name=name,
            student_id=student_id,
            roll_number=roll_number,
            email=email,
            phone=phone
        )
        
        if success:
            # Add to database
            db.add_student(student_id, name, roll_number, email, phone)
            
            return {
                "success": True,
                "message": f"Student {name} registered successfully"
            }
        else:
            return {
                "success": False,
                "message": "Face registration failed. Please use a clear photo with only one face."
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/attendance/mark")
async def mark_attendance(request: AttendanceRequest):
    """Mark attendance for a student"""
    try:
        # Validate location
        user_location = Location(
            latitude=request.latitude,
            longitude=request.longitude,
            accuracy=request.accuracy
        )
        
        is_valid, distance, message = geofence_validator.is_within_geofence(
            user_location,
            request.classroom
        )
        
        if not is_valid:
            return {
                "success": False,
                "message": message,
                "distance": distance
            }
        
        # Get student info
        student = db.get_student(request.student_id)
        if not student:
            return {
                "success": False,
                "message": "Student not found"
            }
        
        # Mark attendance (simplified version without live video)
        success = db.mark_attendance(
            student_id=request.student_id,
            classroom=request.classroom,
            latitude=request.latitude,
            longitude=request.longitude,
            gps_accuracy=request.accuracy,
            liveness_verified=False,  # Would be True with video verification
            face_confidence=0.0
        )
        
        if success:
            return {
                "success": True,
                "message": f"Attendance marked for {student['name']}",
                "student": student,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Failed to mark attendance"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attendance/history/{student_id}")
async def get_attendance_history(student_id: str, days: int = 30):
    """Get attendance history for a student"""
    history = db.get_student_attendance_history(student_id, days)
    stats = db.get_attendance_statistics(student_id)
    
    return {
        "student_id": student_id,
        "history": history,
        "statistics": stats
    }

@app.get("/api/attendance/today")
async def get_todays_attendance(classroom: Optional[str] = None):
    """Get today's attendance records"""
    today = str(date.today())
    records = db.get_attendance_by_date(today, classroom)
    
    return {
        "date": today,
        "classroom": classroom,
        "records": records,
        "count": len(records)
    }

@app.post("/api/session/start")
async def start_session(session: SessionCreate):
    """Start a new attendance session"""
    try:
        smart_attend.start_session(
            session_id=session.session_id,
            classroom=session.classroom,
            subject=session.subject,
            teacher_name=session.teacher_name
        )
        
        return {
            "success": True,
            "message": "Session started",
            "session": session.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/end")
async def end_session():
    """End current attendance session"""
    try:
        smart_attend.end_session()
        
        return {
            "success": True,
            "message": "Session ended"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/daily/{date}")
async def get_daily_report(date: str):
    """Get daily attendance report"""
    report = db.generate_daily_report(date)
    return report

@app.get("/api/fraud/attempts")
async def get_fraud_attempts(days: int = 7):
    """Get recent fraud attempts"""
    attempts = db.get_fraud_attempts(days)
    return {
        "attempts": attempts,
        "count": len(attempts),
        "period_days": days
    }

@app.get("/api/classrooms")
async def get_classrooms():
    """Get list of configured classrooms"""
    classrooms = geofence_validator.list_classrooms()
    return {"classrooms": classrooms}


# WebSocket for live video streaming (for liveness detection)
@app.websocket("/ws/video")
async def video_websocket(websocket: WebSocket):
    """WebSocket endpoint for live video processing"""
    await websocket.accept()
    
    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_text()
            frame_data = json.loads(data)
            
            # Decode base64 image
            img_data = base64.b64decode(frame_data['image'])
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Process frame (face recognition, liveness, etc.)
            student, annotated, locations = face_system.recognize_face(frame)
            
            # Encode response
            _, buffer = cv2.imencode('.jpg', annotated)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            response = {
                "image": img_base64,
                "student": student,
                "faces_detected": len(locations)
            }
            
            await websocket.send_json(response)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    print("Starting SmartAttendAI Web Server...")
    print(f"Access at: http://{SERVER_CONFIG['HOST']}:{SERVER_CONFIG['PORT']}")
    
    uvicorn.run(
        "app:app",
        host=SERVER_CONFIG["HOST"],
        port=SERVER_CONFIG["PORT"],
        reload=SERVER_CONFIG["RELOAD"]
    )