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
from collections import defaultdict

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
                    telegram_id TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Add telegram_id column if it doesn't exist (migration)
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN telegram_id TEXT")
            except:
                pass  # Column already exists
            
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
            
            # Admin users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
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
                   email: str = "", phone: str = "", telegram_id: str = "") -> bool:
        """Add a new student to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO students (student_id, name, roll_number, email, phone, telegram_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, name, roll_number, email, phone, telegram_id))
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
    
    def delete_student(self, student_id: str) -> bool:
        """Soft delete a student by setting is_active to 0"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE students SET is_active = 0 WHERE student_id = ?
                """, (student_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting student: {e}")
            return False
    
    # Admin Operations
    
    def create_admin_user(self, username: str, email: str, full_name: str, password_hash: str) -> bool:
        """Create a new admin user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO admin_users (username, email, full_name, password_hash)
                    VALUES (?, ?, ?, ?)
                """, (username, email, full_name, password_hash))
                return True
        except Exception as e:
            print(f"Error creating admin user: {e}")
            return False
    
    def get_admin_user(self, username: str) -> Optional[Dict]:
        """Get admin user by username"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, full_name, password_hash, is_active
                    FROM admin_users WHERE username = ? AND is_active = 1
                """, (username,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error getting admin user: {e}")
            return None
    
    def check_admin_exists(self, username: str = None, email: str = None) -> bool:
        """Check if admin user exists"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if username:
                    cursor.execute("SELECT 1 FROM admin_users WHERE username = ?", (username,))
                elif email:
                    cursor.execute("SELECT 1 FROM admin_users WHERE email = ?", (email,))
                else:
                    return False
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking admin exists: {e}")
            return False
    
    def update_admin_last_login(self, username: str) -> bool:
        """Update last login time for admin"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE admin_users SET last_login = CURRENT_TIMESTAMP
                    WHERE username = ?
                """, (username,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating last login: {e}")
            return False
    
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
                    student_id, 
                    classroom, 
                    now.isoformat(),  # Convert datetime to ISO format string
                    now.date().isoformat(),  # Convert date to ISO format string
                    now.time().isoformat(),  # Convert time to ISO format string
                    latitude, 
                    longitude, 
                    gps_accuracy,
                    1 if liveness_verified else 0,  # Convert boolean to 0/1
                    face_confidence, 
                    emotion
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error marking attendance: {e}")
            import traceback
            traceback.print_exc()
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
    
    def check_attendance_today(self, student_id: str, classroom: str = None) -> Tuple[bool, Optional[Dict]]:
        """
        Check if a student has already marked attendance today
        Returns: (already_marked: bool, attendance_record: Optional[Dict])
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                today = datetime.now().date().isoformat()
                
                query = """
                    SELECT * FROM attendance
                    WHERE student_id = ?
                    AND date = ?
                """
                params = [student_id, today]
                
                if classroom:
                    query += " AND classroom = ?"
                    params.append(classroom)
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if row:
                    # Student has already marked attendance today
                    return (True, dict(row))
                else:
                    # No attendance record for today
                    return (False, None)
        except Exception as e:
            print(f"Error checking attendance today: {e}")
            return (False, None)
    
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
    
    def add_system_log(self, level: str, module: str, message: str, details: str = None) -> bool:
        """Add a system log entry (alternative method)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_logs (level, module, message, details)
                    VALUES (?, ?, ?, ?)
                """, (level, module, message, details))
                return True
        except Exception as e:
            print(f"Error writing system log: {e}")
            return False
    
    # Analytics and Reports
    
    def get_emotion_statistics(self, classroom: str, start_date: str, end_date: str) -> Dict:
        """
        Get emotion statistics for a classroom over a date range
        Returns: emotion distribution and engagement metrics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all emotions recorded in this period
                cursor.execute("""
                    SELECT emotion, COUNT(*) as count
                    FROM attendance
                    WHERE classroom = ? AND date BETWEEN ? AND ? AND emotion IS NOT NULL
                    GROUP BY emotion
                """, (classroom, start_date, end_date))
                
                emotion_counts = {row['emotion']: row['count'] for row in cursor.fetchall()}
                total_records = sum(emotion_counts.values())
                
                # Calculate percentages
                emotion_percentages = {}
                if total_records > 0:
                    emotion_percentages = {
                        emotion: round((count / total_records) * 100, 2)
                        for emotion, count in emotion_counts.items()
                    }
                
                # Get session engagement scores
                cursor.execute("""
                    SELECT engagement_score FROM sessions
                    WHERE classroom = ? AND DATE(start_time) BETWEEN ? AND ?
                """, (classroom, start_date, end_date))
                
                engagement_scores = [row['engagement_score'] for row in cursor.fetchall() 
                                   if row['engagement_score'] is not None]
                avg_engagement = round(sum(engagement_scores) / len(engagement_scores), 2) if engagement_scores else 0
                
                return {
                    "classroom": classroom,
                    "period": f"{start_date} to {end_date}",
                    "total_records": total_records,
                    "emotions": emotion_counts,
                    "emotion_percentages": emotion_percentages,
                    "average_engagement_score": avg_engagement,
                    "dominant_emotion": max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
                }
        except Exception as e:
            print(f"Error getting emotion statistics: {e}")
            return {}
    
    def get_student_emotion_trend(self, student_id: str, days: int = 7) -> List[Dict]:
        """
        Get emotion trend for a specific student over N days
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date, emotion, COUNT(*) as count
                    FROM attendance
                    WHERE student_id = ? AND date >= DATE('now', '-' || ? || ' days')
                    GROUP BY date, emotion
                    ORDER BY date DESC
                """, (student_id, days))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "date": row['date'],
                        "emotion": row['emotion'],
                        "count": row['count']
                    })
                
                return results
        except Exception as e:
            print(f"Error getting student emotion trend: {e}")
            return []
    
    def get_classroom_insights(self, classroom: str, session_date: str) -> Dict:
        """
        Generate classroom insights for a specific date
        Returns: emotion distribution, student engagement levels
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all attendance records for the date
                cursor.execute("""
                    SELECT a.student_id, s.name, a.emotion, a.face_confidence, a.timestamp
                    FROM attendance a
                    JOIN students s ON a.student_id = s.student_id
                    WHERE a.classroom = ? AND a.date = ?
                    ORDER BY a.timestamp
                """, (classroom, session_date))
                
                records = [dict(row) for row in cursor.fetchall()]
                
                # Calculate emotion distribution
                emotion_dist = defaultdict(int)
                for record in records:
                    if record['emotion']:
                        emotion_dist[record['emotion']] += 1
                
                total_students = len(records)
                emotion_percentages = {
                    emotion: round((count / total_students * 100), 1)
                    for emotion, count in emotion_dist.items()
                } if total_students > 0 else {}
                
                # Identify students needing attention (low confidence or negative emotions)
                students_needing_attention = []
                for record in records:
                    confidence = record['face_confidence'] or 0
                    emotion = record['emotion']
                    
                    if confidence < 0.7 or emotion in ['confused', 'bored', 'sad', 'angry']:
                        students_needing_attention.append({
                            "student_id": record['student_id'],
                            "name": record['name'],
                            "emotion": emotion,
                            "confidence": round(confidence, 2)
                        })
                
                return {
                    "classroom": classroom,
                    "date": session_date,
                    "total_students": total_students,
                    "emotions": dict(emotion_dist),
                    "emotion_percentages": emotion_percentages,
                    "students_needing_attention": students_needing_attention,
                    "engagement_level": round(sum(r.get('face_confidence', 0) for r in records) / total_students, 2) if total_students > 0 else 0
                }
        except Exception as e:
            print(f"Error generating classroom insights: {e}")
            return {}
    
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