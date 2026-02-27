"""
Fraud Detection Module
Monitors and alerts on suspicious attendance attempts
"""
import cv2
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, Optional
import os
from pathlib import Path


class FraudDetector:
    """
    Comprehensive fraud detection system
    """
    
    def __init__(self, config: Dict, database):
        self.config = config
        self.database = database
        self.fraud_images_dir = Path("data/fraud_attempts")
        self.fraud_images_dir.mkdir(parents=True, exist_ok=True)
        
        self.texture_threshold = config["TEXTURE_THRESHOLD"]
        self.alert_email = config["ALERT_EMAIL"]
    
    def save_fraud_evidence(self, frame: np.ndarray, fraud_type: str,
                           student_id: str = None) -> str:
        """Save image evidence of fraud attempt"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{fraud_type}_{timestamp}"
        if student_id:
            filename += f"_{student_id}"
        filename += ".jpg"
        
        filepath = self.fraud_images_dir / filename
        cv2.imwrite(str(filepath), frame)
        
        return str(filepath)
    
    def detect_photo_attack(self, face_region: np.ndarray,
                           texture_analyzer) -> Tuple[bool, float, str]:
        """
        Detect if a photo/screen is being used instead of real face
        
        Returns:
            Tuple of (is_fraud, confidence, description)
        """
        is_real, confidence = texture_analyzer.analyze(face_region)
        
        if not is_real and confidence > self.texture_threshold:
            return True, confidence, "Photo/Screen detected"
        
        return False, confidence, "Appears to be real face"
    
    def detect_multiple_faces(self, face_locations: list) -> Tuple[bool, str]:
        """Detect if multiple faces are present (proxy attempt)"""
        if len(face_locations) > 1:
            return True, f"Multiple faces detected ({len(face_locations)})"
        return False, "Single face detected"
    
    def detect_face_too_small(self, face_location: Tuple, min_size: Tuple[int, int]) -> Tuple[bool, str]:
        """Detect if face is suspiciously small (distant photo)"""
        top, right, bottom, left = face_location
        width = right - left
        height = bottom - top
        
        min_width, min_height = min_size
        
        if width < min_width or height < min_height:
            return True, f"Face too small: {width}x{height}px (min: {min_width}x{min_height}px)"
        
        return False, "Face size acceptable"
    
    def detect_lighting_anomalies(self, frame: np.ndarray) -> Tuple[bool, str]:
        """Detect unnatural lighting (screen glow, flashlight, etc.)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate brightness statistics
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Check for extreme conditions
        if mean_brightness < 30:
            return True, "Extremely dark environment (possible occlusion)"
        
        if mean_brightness > 220:
            return True, "Extremely bright/washed out (possible screen glare)"
        
        # Check for unnatural uniformity (screens tend to be very uniform)
        if std_brightness < 15:
            return True, "Suspiciously uniform lighting (possible screen)"
        
        return False, "Lighting appears natural"
    
    def detect_motion_anomalies(self, frames_history: list) -> Tuple[bool, str]:
        """
        Detect unnatural motion patterns
        Real people have natural micro-movements; photos are static
        """
        if len(frames_history) < 10:
            return False, "Insufficient frames for motion analysis"
        
        # Calculate frame differences
        diffs = []
        for i in range(1, len(frames_history)):
            diff = cv2.absdiff(frames_history[i], frames_history[i-1])
            diffs.append(np.mean(diff))
        
        avg_motion = np.mean(diffs)
        std_motion = np.std(diffs)
        
        # Too little motion = likely a photo
        if avg_motion < 2.0:
            return True, f"Insufficient motion detected (avg: {avg_motion:.2f})"
        
        # Motion too consistent = likely video loop
        if std_motion < 0.5 and avg_motion > 5.0:
            return True, f"Unnaturally consistent motion (std: {std_motion:.2f})"
        
        return False, "Motion patterns appear natural"
    
    def comprehensive_fraud_check(self, frame: np.ndarray, face_location: Tuple,
                                 face_region: np.ndarray, texture_analyzer,
                                 liveness_verified: bool, blink_count: int,
                                 frames_history: list = None) -> Dict:
        """
        Perform comprehensive fraud detection
        
        Returns:
            Dictionary with fraud detection results
        """
        results = {
            "is_fraud": False,
            "fraud_type": None,
            "confidence": 0.0,
            "checks": {},
            "severity": "none"
        }
        
        # Check 1: Photo/Screen detection
        photo_fraud, photo_conf, photo_msg = self.detect_photo_attack(
            face_region, texture_analyzer
        )
        results["checks"]["photo_screen"] = {
            "is_fraud": photo_fraud,
            "confidence": photo_conf,
            "message": photo_msg
        }
        
        if photo_fraud:
            results["is_fraud"] = True
            results["fraud_type"] = "photo_attack"
            results["confidence"] = photo_conf
            results["severity"] = "high"
            return results
        
        # Check 2: Liveness verification
        if not liveness_verified:
            results["checks"]["liveness"] = {
                "is_fraud": True,
                "message": f"Liveness not verified (blinks: {blink_count})"
            }
            results["is_fraud"] = True
            results["fraud_type"] = "liveness_failed"
            results["severity"] = "high"
            return results
        else:
            results["checks"]["liveness"] = {
                "is_fraud": False,
                "message": f"Liveness verified (blinks: {blink_count})"
            }
        
        # Check 3: Lighting anomalies
        lighting_fraud, lighting_msg = self.detect_lighting_anomalies(frame)
        results["checks"]["lighting"] = {
            "is_fraud": lighting_fraud,
            "message": lighting_msg
        }
        
        if lighting_fraud:
            results["is_fraud"] = True
            results["fraud_type"] = "lighting_anomaly"
            results["severity"] = "medium"
        
        # Check 4: Face size
        size_fraud, size_msg = self.detect_face_too_small(
            face_location, (80, 80)
        )
        results["checks"]["face_size"] = {
            "is_fraud": size_fraud,
            "message": size_msg
        }
        
        if size_fraud:
            results["is_fraud"] = True
            results["fraud_type"] = "face_too_small"
            results["severity"] = "low"
        
        # Check 5: Motion analysis (if history available)
        if frames_history:
            motion_fraud, motion_msg = self.detect_motion_anomalies(frames_history)
            results["checks"]["motion"] = {
                "is_fraud": motion_fraud,
                "message": motion_msg
            }
            
            if motion_fraud:
                results["is_fraud"] = True
                results["fraud_type"] = "motion_anomaly"
                results["severity"] = "high"
        
        return results
    
    def handle_fraud_attempt(self, frame: np.ndarray, fraud_results: Dict,
                           student_id: str = None, location: Tuple = None):
        """
        Handle detected fraud attempt:
        1. Save evidence
        2. Log to database
        3. Send alert
        """
        if not fraud_results["is_fraud"]:
            return
        
        fraud_type = fraud_results["fraud_type"]
        severity = fraud_results["severity"]
        
        # Save evidence image
        image_path = self.save_fraud_evidence(frame, fraud_type, student_id)
        
        # Prepare details
        details = {
            "checks": fraud_results["checks"],
            "confidence": fraud_results["confidence"]
        }
        
        # Log to database
        self.database.log_fraud_attempt(
            fraud_type=fraud_type,
            student_id=student_id,
            details=str(details),
            image_path=image_path,
            latitude=location[0] if location else None,
            longitude=location[1] if location else None,
            severity=severity
        )
        
        # Send alert
        self._send_fraud_alert(
            fraud_type=fraud_type,
            student_id=student_id,
            severity=severity,
            image_path=image_path
        )
        
        print(f"[FRAUD ALERT] {fraud_type.upper()} detected!")
        if student_id:
            print(f"  Student ID: {student_id}")
        print(f"  Severity: {severity}")
        print(f"  Evidence saved: {image_path}")
    
    def _send_fraud_alert(self, fraud_type: str, student_id: str,
                         severity: str, image_path: str):
        """
        Send fraud alert notifications
        (Implement Telegram/Email/SMS notifications)
        """
        message = f"""
🚨 FRAUD ALERT 🚨

Type: {fraud_type}
Student ID: {student_id or 'Unknown'}
Severity: {severity.upper()}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Evidence: {image_path}

Please investigate immediately.
        """
        
        # TODO: Implement actual notification sending
        # - Telegram bot message
        # - Email alert
        # - SMS notification
        
        print(message)


class FraudAnalytics:
    """
    Analyze fraud patterns and generate reports
    """
    
    def __init__(self, database):
        self.database = database
    
    def get_fraud_statistics(self, days: int = 30) -> Dict:
        """Get fraud attempt statistics"""
        attempts = self.database.get_fraud_attempts(days)
        
        if not attempts:
            return {
                "total_attempts": 0,
                "by_type": {},
                "by_severity": {},
                "trend": "No data"
            }
        
        # Count by type
        by_type = {}
        by_severity = {}
        
        for attempt in attempts:
            fraud_type = attempt['fraud_type']
            severity = attempt['severity']
            
            by_type[fraud_type] = by_type.get(fraud_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Most common fraud type
        most_common = max(by_type, key=by_type.get)
        
        return {
            "total_attempts": len(attempts),
            "by_type": by_type,
            "by_severity": by_severity,
            "most_common_type": most_common,
            "period_days": days
        }
    
    def identify_repeat_offenders(self, min_attempts: int = 3) -> list:
        """Identify students with multiple fraud attempts"""
        attempts = self.database.get_fraud_attempts(days=90)
        
        student_counts = {}
        for attempt in attempts:
            student_id = attempt.get('student_id')
            if student_id:
                student_counts[student_id] = student_counts.get(student_id, 0) + 1
        
        offenders = [
            {"student_id": sid, "attempts": count}
            for sid, count in student_counts.items()
            if count >= min_attempts
        ]
        
        # Sort by attempt count
        offenders.sort(key=lambda x: x["attempts"], reverse=True)
        
        return offenders
    
    def generate_fraud_report(self) -> Dict:
        """Generate comprehensive fraud report"""
        stats_7days = self.get_fraud_statistics(7)
        stats_30days = self.get_fraud_statistics(30)
        repeat_offenders = self.identify_repeat_offenders()
        
        report = {
            "report_date": datetime.now().isoformat(),
            "last_7_days": stats_7days,
            "last_30_days": stats_30days,
            "repeat_offenders": repeat_offenders,
            "recommendations": self._generate_recommendations(
                stats_30days, repeat_offenders
            )
        }
        
        return report
    
    def _generate_recommendations(self, stats: Dict, offenders: list) -> list:
        """Generate security recommendations based on fraud patterns"""
        recommendations = []
        
        total = stats["total_attempts"]
        
        if total == 0:
            recommendations.append("No fraud attempts detected. System security is effective.")
            return recommendations
        
        # Check for high fraud rate
        if total > 20:
            recommendations.append(
                f"High fraud attempt rate ({total} in 30 days). Consider increasing security measures."
            )
        
        # Check for specific fraud types
        by_type = stats.get("by_type", {})
        
        if by_type.get("photo_attack", 0) > 5:
            recommendations.append(
                "Multiple photo attacks detected. Consider implementing stricter texture analysis."
            )
        
        if by_type.get("liveness_failed", 0) > 10:
            recommendations.append(
                "Many liveness failures. Consider adjusting blink detection parameters."
            )
        
        # Check for repeat offenders
        if len(offenders) > 0:
            recommendations.append(
                f"{len(offenders)} repeat offenders identified. Consider additional verification for these students."
            )
        
        # Severity distribution
        by_severity = stats.get("by_severity", {})
        high_severity = by_severity.get("high", 0)
        
        if high_severity > total * 0.3:
            recommendations.append(
                "High proportion of severe fraud attempts. Immediate security review recommended."
            )
        
        return recommendations


if __name__ == "__main__":
    from src.utils.database import AttendanceDatabase
    from config.settings import FRAUD_CONFIG
    
    # Initialize
    db = AttendanceDatabase()
    fraud_detector = FraudDetector(FRAUD_CONFIG, db)
    analytics = FraudAnalytics(db)
    
    # Test fraud detection
    cap = cv2.VideoCapture(0)
    frames_history = []
    
    print("Fraud detection test... Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Store frame history
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frames_history.append(gray)
        if len(frames_history) > 30:
            frames_history.pop(0)
        
        cv2.imshow("Fraud Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Generate fraud report
    print("\n" + "="*50)
    print("FRAUD DETECTION REPORT")
    print("="*50)
    report = analytics.generate_fraud_report()
    
    import json
    print(json.dumps(report, indent=2))