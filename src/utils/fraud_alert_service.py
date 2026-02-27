"""
Fraud Alert Service
Handles detection, capture, logging, and notification of fraud attempts (spoofing, photo attacks, etc)
"""
import cv2
import numpy as np
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict
import json
from src.utils.notifications import NotificationManager
from config.settings import API_KEYS, NOTIFICATION_CONFIG


class FraudAlertService:
    """
    Handle fraud detection alerts and red-handed snapshots
    """
    
    def __init__(self, database):
        """
        Initialize fraud alert service
        
        Args:
            database: AttendanceDatabase instance
        """
        self.db = database
        self.fraud_images_dir = Path("data/fraud_attempts")
        self.fraud_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize notification manager
        try:
            self.notification_manager = NotificationManager(
                config={
                    "API_KEYS": API_KEYS,
                    "NOTIFICATION_CONFIG": NOTIFICATION_CONFIG
                }
            )
        except Exception as e:
            print(f"[FRAUD] Notification manager initialization warning: {e}")
            self.notification_manager = None
    
    def capture_fraud_snapshot(self, face_image_b64: str, student_id: str, 
                               fraud_type: str) -> Optional[str]:
        """
        Capture and save red-handed fraud snapshot
        
        Args:
            face_image_b64: Base64 encoded face image
            student_id: ID of student attempting fraud
            fraud_type: Type of fraud (spoofing, photo_attack, screen_attack, etc)
        
        Returns:
            Path to saved image or None if failed
        """
        try:
            # Decode image
            img_data = base64.b64decode(face_image_b64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                print(f"[FRAUD] Failed to decode image")
                return None
            
            # Generate filename with timestamp and fraud type
            timestamp = datetime.now()
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{fraud_type}_{student_id}.jpg"
            filepath = self.fraud_images_dir / filename
            
            # Save image with enhanced visibility
            # Add red border to indicate fraud
            h, w = frame.shape[:2]
            border_thickness = 15
            frame_with_border = cv2.copyMakeBorder(
                frame, 
                border_thickness, border_thickness, 
                border_thickness, border_thickness,
                cv2.BORDER_CONSTANT,
                value=(0, 0, 255)  # Red border
            )
            
            # Add timestamp and fraud type text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.2
            font_thickness = 3
            color = (0, 0, 255)  # Red text
            
            cv2.putText(
                frame_with_border,
                f"FRAUD DETECTED: {fraud_type.upper()}",
                (30, 40),
                font, font_scale, color, font_thickness
            )
            
            cv2.putText(
                frame_with_border,
                f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                (30, 90),
                font, font_scale, color, font_thickness
            )
            
            if student_id:
                cv2.putText(
                    frame_with_border,
                    f"Student: {student_id}",
                    (30, 140),
                    font, font_scale, color, font_thickness
                )
            
            # Save the annotated image
            cv2.imwrite(str(filepath), frame_with_border)
            print(f"[FRAUD] Snapshot saved: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            print(f"[FRAUD] Error capturing snapshot: {e}")
            return None
    
    async def log_and_alert_fraud(self, 
                                  fraud_type: str,
                                  student_id: Optional[str] = None,
                                  image_path: Optional[str] = None,
                                  ip_address: Optional[str] = None,
                                  latitude: Optional[float] = None,
                                  longitude: Optional[float] = None,
                                  severity: str = "high",
                                  classroom: Optional[str] = None,
                                  admin_contact: Optional[Dict] = None) -> bool:
        """
        Log fraud attempt and send alert notifications via Telegram
        
        Args:
            fraud_type: Type of fraud (spoofing, photo_attack, screen_attack, gps_spoofing, etc)
            student_id: ID of student attempting fraud
            image_path: Path to captured fraud snapshot
            ip_address: IP address of the attempt
            latitude: GPS latitude (for location-based frauds)
            longitude: GPS longitude (for location-based frauds)
            severity: Severity level (low, medium, high, critical)
            classroom: Classroom where fraud occurred
            admin_contact: Dict with admin contact info (telegram_id)
        
        Returns:
            True if logging and alerts successful, False otherwise
        """
        try:
            timestamp = datetime.now()
            
            # Prepare fraud details
            details = {
                "fraud_type": fraud_type,
                "student_id": student_id,
                "classroom": classroom,
                "timestamp": timestamp.isoformat(),
                "severity": severity,
                "ip_address": ip_address,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                } if latitude and longitude else None
            }
            
            # Log to database
            db_success = self.db.log_fraud_attempt(
                fraud_type=fraud_type,
                student_id=student_id,
                details=json.dumps(details),
                image_path=image_path,
                ip_address=ip_address,
                latitude=latitude,
                longitude=longitude,
                severity=severity
            )
            
            if db_success:
                print(f"[FRAUD] Logged to database: {fraud_type}")
            
            # Send admin/teacher alerts
            await self._send_admin_alerts(
                fraud_type=fraud_type,
                student_id=student_id,
                image_path=image_path,
                timestamp=timestamp,
                severity=severity,
                classroom=classroom,
                admin_contact=admin_contact,
                latitude=latitude,
                longitude=longitude
            )
            
            return True
            
        except Exception as e:
            print(f"[FRAUD] Error in log_and_alert_fraud: {e}")
            return False
    
    async def _send_admin_alerts(self,
                                fraud_type: str,
                                student_id: Optional[str],
                                image_path: Optional[str],
                                timestamp: datetime,
                                severity: str,
                                classroom: Optional[str],
                                admin_contact: Optional[Dict],
                                latitude: Optional[float] = None,
                                longitude: Optional[float] = None):
        """Send alerts to admin/teacher via multiple channels"""
        
        if not admin_contact:
            print("[FRAUD] No admin contact provided")
            return
        
        # Prepare alert message
        alert_message = f"""
🚨 🚨 🚨 FRAUD ALERT - CRITICAL 🚨 🚨 🚨

Spoofing/Fraud Attempt Detected!

Type: {fraud_type.upper()}
Severity: {severity.upper()}
Student ID: {student_id or 'Unknown'}
Classroom: {classroom or 'Unknown'}
Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{f'Location: Lat {latitude:.4f}, Lon {longitude:.4f}' if latitude and longitude else ''}
{f'Snapshot: {image_path}' if image_path else ''}

FRAUDULENT ATTENDANCE ATTEMPT BLOCKED

Immediate Actions:
✓ Image captured and stored
✓ Attempt logged to database
✓ Admin notified automatically

Next Steps:
1. Review the red-handed snapshot immediately
2. Contact the student for explanation
3. Verify student identity through alternative means
4. Update security protocols if needed
        """
        
        # Send via Telegram to teacher/admin if available
        if self.notification_manager:
            try:
                if admin_contact.get("telegram_id"):
                    await self.notification_manager.notify_admin(
                        message=alert_message,
                        admin_contacts=admin_contact
                    )
                    print(f"[FRAUD] Alert sent via Telegram to admin")
            except Exception as e:
                print(f"[FRAUD] Error sending admin alert: {e}")
    
    def get_fraud_statistics(self, days: int = 7, classroom: Optional[str] = None) -> Dict:
        """
        Get fraud statistics
        
        Args:
            days: Number of days to look back
            classroom: Filter by classroom (optional)
        
        Returns:
            Dict with fraud statistics
        """
        try:
            attempts = self.db.get_fraud_attempts(days)
            
            # Filter by classroom if specified
            if classroom:
                attempts = [a for a in attempts if a.get('classroom') == classroom]
            
            # Aggregate statistics
            fraud_types = {}
            total_attempts = len(attempts)
            unique_students = set()
            severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            
            for attempt in attempts:
                # Count by fraud type
                ftype = attempt.get('fraud_type', 'unknown')
                fraud_types[ftype] = fraud_types.get(ftype, 0) + 1
                
                # Unique students
                if attempt.get('student_id'):
                    unique_students.add(attempt['student_id'])
                
                # Severity distribution
                severity = attempt.get('severity', 'medium').lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            return {
                "total_attempts": total_attempts,
                "unique_students": len(unique_students),
                "fraud_types": fraud_types,
                "severity_distribution": severity_counts,
                "recent_attempts": attempts[:10]  # Last 10 attempts
            }
            
        except Exception as e:
            print(f"[FRAUD] Error getting statistics: {e}")
            return {
                "error": str(e),
                "total_attempts": 0,
                "unique_students": 0
            }
