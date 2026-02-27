"""
SmartAttendAI - Simplified Development Server
Web interface without heavy ML dependencies for development/testing
"""
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import json
import os
from datetime import datetime
from typing import Optional

# Initialize FastAPI app
app = FastAPI(
    title="SmartAttendAI - Development Server",
    description="Attendance System Development Interface",
    version="1.0.0-dev"
)

# Mount static files and templates  
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic models
class AttendanceRequest(BaseModel):
    image: str
    timestamp: str

class RegistrationRequest(BaseModel):
    name: str
    student_id: str
    image: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    """Serve the main project landing page"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Main page not found</h1><p><a href='/app'>Go to Attendance App</a></p>", status_code=404)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading page</h1><p>{str(e)}</p>", status_code=500)

@app.get("/app", response_class=HTMLResponse)
async def attendance_app(request: Request):
    """Serve the attendance application interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "SmartAttendAI Development Server is running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/attendance")
async def mark_attendance(request: AttendanceRequest):
    """Mock attendance endpoint for development"""
    # In development, simulate different responses
    import random
    
    responses = [
        {"success": True, "student_name": "John Doe", "confidence": 0.95},
        {"success": True, "student_name": "Jane Smith", "confidence": 0.87},
        {"success": False, "message": "Face not recognized"},
        {"success": False, "message": "Liveness check failed"},
    ]
    
    # Simulate processing delay
    import time
    time.sleep(0.5)
    
    result = random.choice(responses)
    
    # Log the attempt
    log_entry = {
        "timestamp": request.timestamp,
        "result": result,
        "type": "attendance"
    }
    
    print(f"Attendance attempt: {log_entry}")
    
    return result

@app.post("/api/register")
async def register_student(request: RegistrationRequest):
    """Mock registration endpoint for development"""
    # In development, simulate registration
    import time
    time.sleep(1.0)
    
    # Log the registration
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "student_name": request.name,
        "student_id": request.student_id,
        "type": "registration"
    }
    
    print(f"Student registration: {log_entry}")
    
    return {
        "success": True,
        "message": f"Student {request.name} registered successfully",
        "student_id": request.student_id
    }

@app.get("/api/students")
async def list_students():
    """List registered students (mock data)"""
    return {
        "students": [
            {"id": "STU001", "name": "John Doe", "registered": "2024-01-15"},
            {"id": "STU002", "name": "Jane Smith", "registered": "2024-01-16"},
            {"id": "STU003", "name": "Alice Johnson", "registered": "2024-01-17"}
        ]
    }

@app.get("/api/attendance-log")  
async def get_attendance_log():
    """Get attendance log (mock data)"""
    return {
        "records": [
            {
                "student_id": "STU001", 
                "student_name": "John Doe",
                "timestamp": "2024-02-26T09:00:00Z", 
                "status": "present"
            },
            {
                "student_id": "STU002", 
                "student_name": "Jane Smith",
                "timestamp": "2024-02-26T09:05:00Z", 
                "status": "present"
            }
        ]
    }

if __name__ == "__main__":
    print("Starting SmartAttendAI Development Server...")
    print("Access the web interface at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "dev_server:app",
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )