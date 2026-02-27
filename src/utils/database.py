"""
Database Module
Handles attendance records, student data, and system logs
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from contextlib import contextmanager

class AttendanceDatabase:
    """
    SQLite database for attendance management
    """
    
    def __init__(self, db_path: str = "data/smartattend.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    roll_number TEXT UNIQUE NOT NULL,
                    email TEXT,
                    phone TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Attendance records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    classroom TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    gps_accuracy REAL,
                    liveness_verified BOOLEAN DEFAULT 0,
                    face_confidence REAL,
                    emotion TEXT,
                    status TEXT DEFAULT 'present',
                    FOREIGN KEY (student_id) REFERENCES students(student_id)
                )
            """)
            
            # Fraud attempts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fraud_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    student_id TEXT,
                    fraud_type TEXT NOT NULL,
                    details TEXT,
                    image_path TEXT,
                    ip_address TEXT,
                    latitude REAL,
                    longitude REAL,
                    severity TEXT DEFAULT 'medium',
                    FOREIGN KEY (student_id) REFERENCES students(student_id)
                )
            """)
            
            # Sessions table (for lecture sessions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    classroom TEXT NOT NULL,
                    subject TEXT,
                    teacher_name TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    total_students INTEGER DEFAULT 0,
                    present_students INTEGER DEFAULT 0,
                    engagement_score REAL,
                    emotion_data TEXT
                )
            """)
            
            # System logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    module TEXT,
                    message TEXT NOT NULL,
                    details TEXT
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_attendance_student 
                ON attendance(student_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_attendance_date 
                ON attendance(date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fraud_timestamp 
                ON fraud_attempts(timestamp)
            """)
            
            conn.commit()
            print("Database initialized successfully")
    
    # Student Operations
    
    def add_student(self, student_id: str, name: str, roll_number: str,
                   email: str = "", phone: str = "") -> bool:
        """Add a new student to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO students (student_id, name, roll_number, email, phone)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_id, name, roll_number, email, phone))
                return True
        except sqlite3.IntegrityError as e:
            print(f"Student already exists: {e}")
            return False
        except Exception as e:
            print(f"Error adding student: {e}")
            return False
    
    def get_student(self, student_id: str) -> Optional[Dict]:
        """Get student information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM students WHERE student_id = ?
            """, (student_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_students(self, active_only: bool = True) -> List[Dict]:
        """Get list of all students"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM students"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY name"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    # Attendance Operations
    
    def mark_attendance(self, student_id: str, classroom: str,
                       latitude: float = None, longitude: float = None,
                       gps_accuracy: float = None, liveness_verified: bool = False,
                       face_confidence: float = 0.0, emotion: str = None) -> bool:
        """Mark attendance for a student"""
        try:
            now = datetime.now()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO attendance (
                        student_id, classroom, timestamp, date, time,
                        latitude, longitude, gps_accuracy,
                        liveness_verified, face_confidence, emotion
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_id, classroom, now, now.date(), now.time(),
                    latitude, longitude, gps_accuracy,
                    liveness_verified, face_confidence, emotion
                ))
                return True
        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False
    
    def get_attendance_by_date(self, date: str, classroom: str = None) -> List[Dict]:
        """Get attendance records for a specific date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT a.*, s.name, s.roll_number
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE a.date = ?
            """
            params = [date]
            
            if classroom:
                query += " AND a.classroom = ?"
                params.append(classroom)
            
            query += " ORDER BY a.time"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_student_attendance_history(self, student_id: str, 
                                      days: int = 30) -> List[Dict]:
        """Get attendance history for a student"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM attendance
                WHERE student_id = ?
                AND date >= date('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            """, (student_id, days))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_attendance_statistics(self, student_id: str) -> Dict:
        """Get attendance statistics for a student"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total attendance
            cursor.execute("""
                SELECT COUNT(*) as total_present
                FROM attendance
                WHERE student_id = ?
            """, (student_id,))
            total_present = cursor.fetchone()['total_present']
            
            # Last 30 days
            cursor.execute("""
                SELECT COUNT(*) as present_30days
                FROM attendance
                WHERE student_id = ?
                AND date >= date('now', '-30 days')
            """, (student_id,))
            present_30days = cursor.fetchone()['present_30days']
            
            # By classroom
            cursor.execute("""
                SELECT classroom, COUNT(*) as count
                FROM attendance
                WHERE student_id = ?
                GROUP BY classroom
            """, (student_id,))
            by_classroom = {row['classroom']: row['count'] 
                          for row in cursor.fetchall()}
            
            return {
                "total_present": total_present,
                "present_last_30_days": present_30days,
                "by_classroom": by_classroom
            }
    
    # Fraud Detection Operations
    
    def log_fraud_attempt(self, fraud_type: str, student_id: str = None,
                         details: str = None, image_path: str = None,
                         ip_address: str = None, latitude: float = None,
                         longitude: float = None, severity: str = "medium") -> bool:
        """Log a fraud attempt"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO fraud_attempts (
                        student_id, fraud_type, details, image_path,
                        ip_address, latitude, longitude, severity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_id, fraud_type, details, image_path,
                    ip_address, latitude, longitude, severity
                ))
                return True
        except Exception as e:
            print(f"Error logging fraud attempt: {e}")
            return False
    
    def get_fraud_attempts(self, days: int = 7) -> List[Dict]:
        """Get recent fraud attempts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.*, s.name as student_name
                FROM fraud_attempts f
                LEFT JOIN students s ON f.student_id = s.student_id
                WHERE f.timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY f.timestamp DESC
            """, (days,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Session Management
    
    def create_session(self, session_id: str, classroom: str,
                      subject: str = None, teacher_name: str = None) -> bool:
        """Create a new lecture session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (
                        session_id, classroom, subject, teacher_name, start_time
                    ) VALUES (?, ?, ?, ?, ?)
                """, (session_id, classroom, subject, teacher_name, datetime.now()))
                return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def end_session(self, session_id: str, total_students: int = 0,
                   present_students: int = 0, engagement_score: float = 0.0,
                   emotion_data: Dict = None) -> bool:
        """End a lecture session and update statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions
                    SET end_time = ?, total_students = ?, present_students = ?,
                        engagement_score = ?, emotion_data = ?
                    WHERE session_id = ?
                """, (
                    datetime.now(), total_students, present_students,
                    engagement_score, json.dumps(emotion_data) if emotion_data else None,
                    session_id
                ))
                return True
        except Exception as e:
            print(f"Error ending session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                if data.get('emotion_data'):
                    data['emotion_data'] = json.loads(data['emotion_data'])
                return data
            return None
    
    # System Logging
    
    def log(self, level: str, module: str, message: str, details: Dict = None):
        """Add system log entry"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_logs (level, module, message, details)
                    VALUES (?, ?, ?, ?)
                """, (level, module, message, json.dumps(details) if details else None))
        except Exception as e:
            print(f"Error writing log: {e}")
    
    # Analytics and Reports
    
    def generate_daily_report(self, date: str) -> Dict:
        """Generate comprehensive daily report"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total attendance count
            cursor.execute("""
                SELECT COUNT(DISTINCT student_id) as total_present
                FROM attendance
                WHERE date = ?
            """, (date,))
            total_present = cursor.fetchone()['total_present']
            
            # By classroom
            cursor.execute("""
                SELECT classroom, COUNT(*) as count
                FROM attendance
                WHERE date = ?
                GROUP BY classroom
            """, (date,))
            by_classroom = {row['classroom']: row['count'] 
                          for row in cursor.fetchall()}
            
            # Average face confidence
            cursor.execute("""
                SELECT AVG(face_confidence) as avg_confidence
                FROM attendance
                WHERE date = ?
            """, (date,))
            avg_confidence = cursor.fetchone()['avg_confidence'] or 0.0
            
            # Fraud attempts
            cursor.execute("""
                SELECT COUNT(*) as fraud_count
                FROM fraud_attempts
                WHERE date(timestamp) = ?
            """, (date,))
            fraud_count = cursor.fetchone()['fraud_count']
            
            return {
                "date": date,
                "total_present": total_present,
                "by_classroom": by_classroom,
                "avg_face_confidence": round(avg_confidence, 2),
                "fraud_attempts": fraud_count
            }


if __name__ == "__main__":
    # Test the database
    db = AttendanceDatabase()
    
    # Add test students
    db.add_student("STU001", "Alice Johnson", "22001", "alice@example.com", "+1234567890")
    db.add_student("STU002", "Bob Smith", "22002", "bob@example.com", "+1234567891")
    
    # Mark attendance
    db.mark_attendance(
        student_id="STU001",
        classroom="Room_101",
        latitude=18.5205,
        longitude=73.8568,
        liveness_verified=True,
        face_confidence=0.95,
        emotion="happy"
    )
    
    # Get today's attendance
    from datetime import date
    today = str(date.today())
    attendance = db.get_attendance_by_date(today)
    print(f"\nToday's Attendance ({today}):")
    for record in attendance:
        print(f"  {record['name']} - {record['time']} - {record['classroom']}")
    
    # Generate report
    report = db.generate_daily_report(today)
    print(f"\nDaily Report:")
    print(json.dumps(report, indent=2))