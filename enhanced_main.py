"""
Enhanced SmartAttendAI with Production Features
Includes error handling, fallbacks, and production configuration
"""
import cv2
import numpy as np
from datetime import datetime
import sys
import os
import asyncio
import logging
import traceback
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config.settings import *
    from config.production_config import get_production_config, print_config_status
except ImportError as e:
    print(f"Warning: Could not load production config: {e}")
    from config.settings import *

# Enhanced imports with error handling
try:
    from src.liveness.detector import LivenessDetector, TextureAnalyzer, ChallengeResponseVerifier
except ImportError as e:
    print(f"Warning: Liveness detection not available: {e}")
    LivenessDetector = None

try:
    from src.face_recognition.recognizer import FaceRecognitionSystem
except ImportError as e:
    print(f"Error: Face recognition system not available: {e}")
    sys.exit(1)

try:
    from src.geofencing.validator import GeofenceValidator, Location, GeofenceSecurity
except ImportError as e:
    print(f"Warning: Geofencing not available: {e}")
    GeofenceValidator = None
    Location = None

try:
    from src.emotion_detection.analyzer import EmotionAnalyzer, ClassroomAnalytics
except ImportError as e:
    print(f"Warning: Emotion detection not available: {e}")
    EmotionAnalyzer = None

try:
    from src.fraud_detection.detector2 import FraudDetector, FraudAnalytics
except ImportError as e:
    print(f"Warning: Fraud detection not available: {e}")
    FraudDetector = None

try:
    from src.utils.database import AttendanceDatabase
except ImportError as e:
    print(f"Error: Database system not available: {e}")
    sys.exit(1)

try:
    from src.utils.notifications import NotificationManager
except ImportError as e:
    print(f"Warning: Notifications not available: {e}")
    NotificationManager = None

# Setup logging
def setup_logging():
    """Setup production logging"""
    log_level = getattr(logging, LOG_LEVEL.upper() if 'LOG_LEVEL' in globals() else 'INFO')
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "smartattendai.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

class EnhancedSmartAttendAI:
    """
    Enhanced SmartAttendAI System with Error Handling and Fallbacks
    """
    
    def __init__(self):
        self.logger = setup_logging()
        self.logger.info("Initializing Enhanced SmartAttendAI...")
        
        # Load production configuration
        try:
            self.config = get_production_config()
            print_config_status()
        except Exception as e:
            self.logger.warning(f"Could not load production config: {e}")
            self.config = None
        
        # Initialize core components with error handling
        self.database = None
        self.face_system = None
        self.liveness_detector = None
        self.geofence_validator = None
        self.emotion_analyzer = None
        self.fraud_detector = None
        self.notification_manager = None
        
        # System status
        self.system_ready = False
        self.available_modules = []
        self.failed_modules = []
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize system components with error handling"""
        
        # Initialize database (required)
        try:
            db_path = DATABASE_CONFIG["SQLITE_PATH"]
            self.database = AttendanceDatabase(db_path)
            self.available_modules.append("Database")
            self.logger.info("✓ Database initialized successfully")
        except Exception as e:
            self.logger.error(f"✗ Database initialization failed: {e}")
            self.failed_modules.append("Database")
            raise RuntimeError("Database is required for operation")
        
        # Initialize face recognition (required)
        try:
            self.face_system = FaceRecognitionSystem(FACE_CONFIG)
            self.available_modules.append("Face Recognition")
            self.logger.info("✓ Face recognition initialized successfully")
        except Exception as e:
            self.logger.error(f"✗ Face recognition initialization failed: {e}")
            self.failed_modules.append("Face Recognition")
            raise RuntimeError("Face recognition is required for operation")
        
        # Initialize optional components
        self._init_optional_component("Liveness Detection", self._init_liveness)
        self._init_optional_component("Geofencing", self._init_geofencing)
        self._init_optional_component("Emotion Analysis", self._init_emotion)
        self._init_optional_component("Fraud Detection", self._init_fraud)
        self._init_optional_component("Notifications", self._init_notifications)
        
        # System ready if core components are available
        self.system_ready = "Database" in self.available_modules and "Face Recognition" in self.available_modules
        
        if self.system_ready:
            self.logger.info("✓ SmartAttendAI initialized successfully!")
        else:
            self.logger.error("✗ System initialization failed - core components missing")
    
    def _init_optional_component(self, name, init_func):
        """Initialize an optional component with error handling"""
        try:
            if init_func():
                self.available_modules.append(name)
                self.logger.info(f"✓ {name} initialized successfully")
            else:
                self.failed_modules.append(name)
                self.logger.warning(f"- {name} not available (module missing)")
        except Exception as e:
            self.failed_modules.append(name)
            self.logger.warning(f"- {name} initialization failed: {e}")
    
    def _init_liveness(self):
        """Initialize liveness detection"""
        if LivenessDetector is None:
            return False
        
        self.liveness_detector = LivenessDetector(LIVENESS_CONFIG)
        return True
    
    def _init_geofencing(self):
        """Initialize geofencing"""
        if GeofenceValidator is None:
            return False
        
        self.geofence_validator = GeofenceValidator(GEOFENCE_CONFIG)
        return True
    
    def _init_emotion(self):
        """Initialize emotion analysis"""
        if EmotionAnalyzer is None:
            return False
        
        self.emotion_analyzer = EmotionAnalyzer(EMOTION_CONFIG)
        return True
    
    def _init_fraud(self):
        """Initialize fraud detection"""
        if FraudDetector is None:
            return False
        
        self.fraud_detector = FraudDetector(FRAUD_CONFIG, self.database)
        return True
    
    def _init_notifications(self):
        """Initialize notification system"""
        if NotificationManager is None:
            return False
        
        api_keys = API_KEYS
        notification_config = {'API_KEYS': api_keys, 'NOTIFICATION_CONFIG': NOTIFICATION_CONFIG}
        self.notification_manager = NotificationManager(notification_config)
        return True
    
    def get_system_status(self):
        """Get comprehensive system status"""
        return {
            'ready': self.system_ready,
            'available_modules': self.available_modules,
            'failed_modules': self.failed_modules,
            'total_modules': len(self.available_modules) + len(self.failed_modules)
        }
    
    def safe_camera_test(self, camera_id=0):
        """Test camera with error handling"""
        try:
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                return False, "Could not open camera"
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, "Could not read from camera"
            
            return True, f"Camera {camera_id} working ({frame.shape[1]}x{frame.shape[0]})"
            
        except Exception as e:
            return False, f"Camera error: {str(e)}"

def main():
    """Main application entry point"""
    print("=" * 60)
    print("Enhanced SmartAttendAI System")
    print("=" * 60)
    
    try:
        # Initialize system
        system = EnhancedSmartAttendAI()
        
        # Display system status
        status = system.get_system_status()
        print(f"\nSystem Status: {'READY' if status['ready'] else 'NOT READY'}")
        print(f"Available modules: {', '.join(status['available_modules'])}")
        
        if status['failed_modules']:
            print(f"Failed modules: {', '.join(status['failed_modules'])}")
        
        if not status['ready']:
            print("\nSystem not ready. Please check the logs for errors.")
            return
        
        # Test camera
        camera_ok, camera_msg = system.safe_camera_test()
        print(f"\nCamera test: {camera_msg}")
        
        if not camera_ok:
            print("Warning: Camera not available. System will work in offline mode.")
        
        # Interactive mode
        print("\n" + "=" * 60)
        print("SYSTEM READY - Interactive Mode")
        print("=" * 60)
        print("Commands:")
        print("  'test' - Test face recognition")
        print("  'report' - Generate daily report")
        print("  'status' - Show system status")
        print("  'quit' - Exit system")
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'test':
                    print("Testing face recognition system...")
                    
                    # Test with existing student data
                    students = system.face_system.list_registered_students()
                    if students:
                        print(f"Found {len(students)} registered students:")
                        for student in students:
                            print(f"  - {student['name']} (ID: {student['id']})")
                    else:
                        print("No students registered. Please register students first.")
                
                elif command == 'report':
                    try:
                        report = system.database.generate_daily_report(str(datetime.now().date()))
                        print("\nDaily Attendance Report:")
                        print(json.dumps(report, indent=2))
                    except Exception as e:
                        print(f"Error generating report: {e}")
                
                elif command == 'status':
                    status = system.get_system_status()
                    print(f"\nSystem Status: {status}")
                    
                    # Test all cameras
                    print("\nCamera Status:")
                    for cam_id in range(3):
                        ok, msg = system.safe_camera_test(cam_id)
                        print(f"  Camera {cam_id}: {msg}")
                
                else:
                    print("Unknown command. Try: test, report, status, quit")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\nSmartAttendAI system shutdown complete.")
        
    except Exception as e:
        print(f"System initialization failed: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()