"""
SmartAttendAI Main Application
Integrates all modules for robust attendance with liveness detection
"""
import cv2
import numpy as np
from datetime import datetime
import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import *
from src.liveness.detector import LivenessDetector, TextureAnalyzer, ChallengeResponseVerifier
from src.face_recognition.recognizer import FaceRecognitionSystem
from src.geofencing.validator import GeofenceValidator, Location, GeofenceSecurity
from src.emotion_detection.analyzer import EmotionAnalyzer, ClassroomAnalytics
from src.fraud_detection.detector2 import FraudDetector, FraudAnalytics
from src.utils.database import AttendanceDatabase
from src.utils.notifications import NotificationManager


class SmartAttendAI:
    """
    Main SmartAttendAI System
    """
    
    def __init__(self):
        print("Initializing SmartAttendAI...")
        
        # Initialize database
        self.database = AttendanceDatabase(DATABASE_CONFIG["SQLITE_PATH"])
        
        # Initialize core modules
        self.liveness_detector = LivenessDetector(LIVENESS_CONFIG)
        self.texture_analyzer = TextureAnalyzer(model_path="models/spoof_detection_model.h5")
        self.challenge_verifier = ChallengeResponseVerifier(FRAUD_CONFIG["CHALLENGES"])
        
        self.face_system = FaceRecognitionSystem(FACE_CONFIG)
        self.geofence_validator = GeofenceValidator(GEOFENCE_CONFIG)
        self.emotion_analyzer = EmotionAnalyzer(EMOTION_CONFIG)
        
        self.fraud_detector = FraudDetector(FRAUD_CONFIG, self.database)
        
        # Notification system
        config = {
            "API_KEYS": API_KEYS,
            "NOTIFICATION_CONFIG": NOTIFICATION_CONFIG
        }
        self.notifier = NotificationManager(config)
        
        # Session management
        self.current_session = None
        self.classroom_analytics = None
        
        # Frame history for motion analysis
        self.frames_history = []
        
        print("[OK] SmartAttendAI initialized successfully!")
    
    def start_session(self, session_id: str, classroom: str, 
                     subject: str = None, teacher_name: str = None):
        """Start a new attendance session"""
        self.current_session = {
            "session_id": session_id,
            "classroom": classroom,
            "subject": subject,
            "teacher_name": teacher_name
        }
        
        # Create session in database
        self.database.create_session(
            session_id=session_id,
            classroom=classroom,
            subject=subject,
            teacher_name=teacher_name
        )
        
        # Start emotion analytics
        self.classroom_analytics = ClassroomAnalytics()
        self.classroom_analytics.start_session(session_id)
        
        print(f"\n{'='*60}")
        print(f"SESSION STARTED")
        print(f"{'='*60}")
        print(f"Session ID: {session_id}")
        print(f"Classroom: {classroom}")
        if subject:
            print(f"Subject: {subject}")
        if teacher_name:
            print(f"Teacher: {teacher_name}")
        print(f"{'='*60}\n")
    
    async def mark_attendance(self, user_location: Location, 
                             use_challenge: bool = False) -> dict:
        """
        Complete attendance marking flow
        
        Returns:
            Dictionary with result status and details
        """
        if not self.current_session:
            return {
                "success": False,
                "message": "No active session. Please start a session first."
            }
        
        classroom = self.current_session["classroom"]
        result = {
            "success": False,
            "student": None,
            "message": "",
            "checks": {}
        }
        
        # Step 1: Geofence validation
        print("\n[1/5] Validating location...")
        is_valid_location, distance, geo_message = self.geofence_validator.is_within_geofence(
            user_location, classroom
        )
        result["checks"]["geofence"] = {
            "passed": is_valid_location,
            "distance": distance,
            "message": geo_message
        }
        
        if not is_valid_location:
            result["message"] = f"Location validation failed: {geo_message}"
            print(f"  [FAIL] {result['message']}")
            return result
        
        print(f"  [OK] {geo_message}")
        
        # Check for GPS spoofing
        security = GeofenceSecurity()
        is_suspicious, gps_reason = security.detect_gps_spoofing(user_location)
        if is_suspicious:
            result["message"] = f"GPS spoofing detected: {gps_reason}"
            print(f"  [FAIL] {result['message']}")
            self.fraud_detector.database.log_fraud_attempt(
                fraud_type="gps_spoofing",
                details=gps_reason,
                latitude=user_location.latitude,
                longitude=user_location.longitude,
                severity="high"
            )
            return result
        
        # Step 2: Liveness Detection
        print("\n[2/5] Verifying liveness...")
        cap = cv2.VideoCapture(0)
        
        liveness_verified = False
        blink_count = 0
        face_frame = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            is_live, message, annotated = self.liveness_detector.detect_blinks(frame)
            
            cv2.imshow("Liveness Detection", annotated)
            
            if is_live is not None:
                liveness_verified = is_live
                blink_count = self.liveness_detector.total_blinks
                face_frame = frame.copy()
                print(f"  {message}")
                break
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                result["message"] = "Liveness check cancelled"
                return result
        
        result["checks"]["liveness"] = {
            "passed": liveness_verified,
            "blinks": blink_count
        }
        
        if not liveness_verified:
            cap.release()
            cv2.destroyAllWindows()
            result["message"] = f"Liveness verification failed: {message}"
            print(f"  [FAIL] {result['message']}")
            return result
        
        print(f"  [OK] Liveness verified (blinks: {blink_count})")
        
        # Step 3: Challenge-Response (optional)
        if use_challenge:
            print("\n[3/5] Challenge-response verification...")
            challenge = self.challenge_verifier.generate_challenge()
            print(f"  Challenge: {challenge}")
            
            challenge_passed = False
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                passed, msg = self.challenge_verifier.verify_response(frame)
                
                cv2.putText(frame, msg, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Challenge", frame)
                
                if passed is not None:
                    challenge_passed = passed
                    print(f"  {msg}")
                    break
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            result["checks"]["challenge"] = {
                "passed": challenge_passed
            }
            
            if not challenge_passed:
                cap.release()
                cv2.destroyAllWindows()
                result["message"] = "Challenge-response failed"
                return result
        else:
            print("\n[3/5] Challenge-response skipped")
        
        # Step 4: Face Recognition
        print("\n[4/5] Recognizing face...")
        
        student_match = None
        face_confidence = 0.0
        face_location = None
        
        for _ in range(30):  # Try for 30 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            student, annotated, locations = self.face_system.recognize_face(frame)
            
            if student:
                student_match = student
                face_confidence = student["confidence"]
                if locations:
                    face_location = locations[0]
                break
            
            cv2.imshow("Face Recognition", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        result["checks"]["face_recognition"] = {
            "passed": student_match is not None,
            "confidence": face_confidence
        }
        
        if not student_match:
            result["message"] = "Face not recognized. Please register first."
            print(f"  [FAIL] {result['message']}")
            return result
        
        print(f"  [OK] Recognized: {student_match['name']} ({face_confidence:.2f})")
        result["student"] = student_match
        
        # Step 5: Fraud Detection
        print("\n[5/5] Running fraud detection...")
        
        # Extract face region for texture analysis
        if face_location and face_frame is not None:
            top, right, bottom, left = face_location
            top *= 4; right *= 4; bottom *= 4; left *= 4  # Scale back up
            face_region = face_frame[top:bottom, left:right]
            
            fraud_results = self.fraud_detector.comprehensive_fraud_check(
                frame=face_frame,
                face_location=(top, right, bottom, left),
                face_region=face_region,
                texture_analyzer=self.texture_analyzer,
                liveness_verified=liveness_verified,
                blink_count=blink_count,
                frames_history=self.frames_history
            )
            
            result["checks"]["fraud_detection"] = fraud_results
            
            if fraud_results["is_fraud"]:
                result["message"] = f"Fraud detected: {fraud_results['fraud_type']}"
                print(f"  [FAIL] {result['message']}")
                
                # Handle fraud attempt
                self.fraud_detector.handle_fraud_attempt(
                    frame=face_frame,
                    fraud_results=fraud_results,
                    student_id=student_match["id"],
                    location=(user_location.latitude, user_location.longitude)
                )
                
                # Notify student
                await self.notifier.notify_fraud_attempt(
                    student_data=student_match,
                    fraud_type=fraud_results["fraud_type"]
                )
                
                return result
        
        print("  [OK] No fraud detected")
        
        # All checks passed - Mark attendance
        print("\n" + "="*60)
        print("ALL CHECKS PASSED [OK]")
        print("="*60)
        
        success = self.database.mark_attendance(
            student_id=student_match["id"],
            classroom=classroom,
            latitude=user_location.latitude,
            longitude=user_location.longitude,
            gps_accuracy=user_location.accuracy,
            liveness_verified=liveness_verified,
            face_confidence=face_confidence
        )
        
        if success:
            result["success"] = True
            result["message"] = "Attendance marked successfully"
            
            timestamp = datetime.now()
            print(f"\n[OK] Attendance marked for {student_match['name']}")
            print(f"  Time: {timestamp.strftime('%I:%M:%S %p')}")
            print(f"  Location: {user_location}")
            print(f"  Classroom: {classroom}")
            
            # Send notification
            student_data = {
                **student_match,
                "student_name": student_match["name"],
                "classroom": classroom,
                "timestamp": timestamp
            }
            await self.notifier.notify_attendance_success(student_data)
        else:
            result["message"] = "Failed to save attendance"
        
        return result
    
    def end_session(self):
        """End current attendance session"""
        if not self.current_session or not self.classroom_analytics:
            print("No active session to end")
            return
        
        # Generate emotion report
        emotion_report = self.classroom_analytics.generate_report()
        
        # Get attendance count
        today = datetime.now().date()
        attendance_records = self.database.get_attendance_by_date(
            str(today),
            self.current_session["classroom"]
        )
        present_count = len(attendance_records)
        
        # Update session in database
        self.database.end_session(
            session_id=self.current_session["session_id"],
            total_students=len(self.face_system.known_encodings),
            present_students=present_count,
            engagement_score=emotion_report.get("engagement_score", 0),
            emotion_data=emotion_report
        )
        
        print(f"\n{'='*60}")
        print("SESSION ENDED")
        print(f"{'='*60}")
        print(f"Present: {present_count}/{len(self.face_system.known_encodings)}")
        print(f"Engagement Score: {emotion_report.get('engagement_score', 0):.1f}/100")
        print(f"{'='*60}\n")
        
        # Reset session
        self.current_session = None
        self.classroom_analytics = None


def main():
    """Main application entry point"""
    system = SmartAttendAI()
    
    # Start a session
    session_id = f"SESSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    system.start_session(
        session_id=session_id,
        classroom="Room_101",
        subject="Machine Learning",
        teacher_name="Dr. Smith"
    )
    
    # Simulate student location
    student_location = Location(
        latitude=18.5205,
        longitude=73.8568,
        accuracy=15.0
    )
    
    print("\n" + "="*60)
    print("MARK ATTENDANCE")
    print("="*60)
    print("Please follow the on-screen instructions...")
    print("Press 'q' to cancel at any time")
    print("="*60 + "\n")
    
    # Mark attendance
    result = asyncio.run(system.mark_attendance(
        user_location=student_location,
        use_challenge=False  # Set to True to enable challenge-response
    ))
    
    print("\n" + "="*60)
    print("RESULT")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    if result.get("student"):
        print(f"Student: {result['student']['name']}")
    print("="*60 + "\n")
    
    input("Press Enter to end session...")
    system.end_session()


if __name__ == "__main__":
    main()