"""
Database Module - PostgreSQL & SQLite Support
Handles attendance records, student data, and system logs
Supports both PostgreSQL (production) and SQLite (development)
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from contextlib import contextmanager

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False


class DatabaseBase:
    """Base class with all database operations"""
    
    def get_connection(self):
        """Context manager for database connections - override in subclasses"""
        raise NotImplementedError
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        raise NotImplementedError
    
    # Helper to execute in separate transactions (for PostgreSQL)
    def _execute_safe(self, sql: str, description: str = ""):
        """Execute SQL in a separate transaction, catching duplicate errors"""
        raise NotImplementedError
    
    # Student Operations
    
    def add_student(self, student_id: str, name: str, roll_number: str,
                   email: str = "", phone: str = "", telegram_id: str = "") -> bool:
        """Add a new student"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param_placeholder = "?" if self.db_type == "sqlite" else "%s"
                cursor.execute(f"""
                    INSERT INTO students (student_id, name, roll_number, email, phone, telegram_id)
                    VALUES ({param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder})
                """, (student_id, name, roll_number, email, phone, telegram_id))
                return True
        except (sqlite3.IntegrityError, Exception) as e:
            if "already exists" in str(e) or "UNIQUE" in str(e):
                print(f"Student already exists: {e}")
            else:
                print(f"Error adding student: {e}")
            return False
    
    def get_student(self, student_id: str) -> Optional[Dict]:
        """Get student by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            param_placeholder = "?" if self.db_type == "sqlite" else "%s"
            cursor.execute(f"SELECT * FROM students WHERE student_id = {param_placeholder}", (student_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            if self.db_type == "sqlite":
                return dict(row)
            else:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
    
    def list_students(self, active_only: bool = True) -> List[Dict]:
        """Get all students"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM students"
            if active_only:
                query += " WHERE is_active = " + ("TRUE" if self.db_type == "postgresql" else "1")
            query += " ORDER BY name"
            
            cursor.execute(query)
            
            if self.db_type == "sqlite":
                return [dict(row) for row in cursor.fetchall()]
            else:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def delete_student(self, student_id: str) -> bool:
        """Soft delete a student"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                val = "0" if self.db_type == "sqlite" else "FALSE"
                cursor.execute(f"UPDATE students SET is_active = {val} WHERE student_id = {param}", (student_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting student: {e}")
            return False
    
    # Face Encoding Operations
    
    def save_face_encodings(self, student_id: str, encodings_json: str) -> bool:
        """Save face encodings for a student as JSON string"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                
                # Try UPDATE first
                cursor.execute(f"""
                    UPDATE students SET face_encodings = {param} WHERE student_id = {param}
                """, (encodings_json, student_id))
                
                # If no rows were updated, the student might not have been added yet
                # Log this but don't fail - the encoding will be saved when student is added
                if cursor.rowcount == 0:
                    print(f"[DB] Warning: Could not update face encodings for student {student_id} - student may not exist yet")
                    # Try to log for debugging
                    try:
                        # Check if student exists
                        cursor.execute(f"SELECT student_id FROM students WHERE student_id = {param}", (student_id,))
                        if cursor.fetchone() is None:
                            print(f"[DB] Confirmed: Student {student_id} does not exist in database yet")
                        else:
                            print(f"[DB] Student {student_id} exists but UPDATE affected 0 rows")
                    except:
                        pass
                else:
                    print(f"[DB] Successfully saved face encodings for student {student_id}")
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error saving face encodings: {e}")
            return False
    
    def get_face_encodings(self, student_id: str) -> Optional[str]:
        """Get face encodings for a student"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                cursor.execute(f"SELECT face_encodings FROM students WHERE student_id = {param}", (student_id,))
                row = cursor.fetchone()
                
                if row:
                    if self.db_type == "sqlite":
                        return row['face_encodings']
                    else:
                        return row[0]
                return None
        except Exception as e:
            print(f"Error getting face encodings: {e}")
            return None
    
    def get_all_face_encodings(self) -> Dict[str, str]:
        """Get all face encodings for active students"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                active = "1" if self.db_type == "sqlite" else "TRUE"
                cursor.execute(f"""
                    SELECT student_id, face_encodings FROM students 
                    WHERE is_active = {active} AND face_encodings IS NOT NULL
                """)
                
                encodings_dict = {}
                for row in cursor.fetchall():
                    if self.db_type == "sqlite":
                        encodings_dict[row['student_id']] = row['face_encodings']
                    else:
                        encodings_dict[row[0]] = row[1]
                
                return encodings_dict
        except Exception as e:
            print(f"Error getting all face encodings: {e}")
            return {}
    
    # Admin Operations
    
    def create_admin_user(self, username: str, email: str, full_name: str, password_hash: str) -> bool:
        """Create admin user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                cursor.execute(f"""
                    INSERT INTO admin_users (username, email, full_name, password_hash)
                    VALUES ({param}, {param}, {param}, {param})
                """, (username, email, full_name, password_hash))
                return True
        except (sqlite3.IntegrityError, Exception) as e:
            print(f"Admin already exists: {e}")
            return False
    
    def get_admin_user(self, username: str) -> Optional[Dict]:
        """Get admin user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                active = "1" if self.db_type == "sqlite" else "TRUE"
                cursor.execute(f"""
                    SELECT id, username, email, full_name, password_hash, is_active
                    FROM admin_users WHERE username = {param} AND is_active = {active}
                """, (username,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                if self.db_type == "sqlite":
                    return dict(row)
                else:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            print(f"Error getting admin: {e}")
            return None
    
    def check_admin_exists(self, username: str = None, email: str = None) -> bool:
        """Check if admin exists"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                
                if username:
                    cursor.execute(f"SELECT 1 FROM admin_users WHERE username = {param}", (username,))
                elif email:
                    cursor.execute(f"SELECT 1 FROM admin_users WHERE email = {param}", (email,))
                else:
                    return False
                
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking admin: {e}")
            return False
    
    def update_admin_last_login(self, username: str) -> bool:
        """Update admin last login"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                cursor.execute(f"""
                    UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE username = {param}
                """, (username,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating login: {e}")
            return False
    
    # Attendance Operations
    
    def add_attendance_record(self, student_id: str, classroom: str, date: str, time: str,
                             latitude: float, longitude: float, gps_accuracy: float,
                             liveness_verified: bool = False, face_confidence: float = 0.0,
                             emotion: str = "") -> bool:
        """Add attendance record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                
                # Convert boolean for database compatibility
                if self.db_type == "sqlite":
                    liveness_bool = 1 if liveness_verified else 0
                else:  # PostgreSQL - use 'true'/'false' with ::boolean cast
                    liveness_bool = 'true' if liveness_verified else 'false'
                
                if self.db_type == "sqlite":
                    query = f"""
                        INSERT INTO attendance 
                        (student_id, classroom, date, time, latitude, longitude, gps_accuracy, 
                         liveness_verified, face_confidence, emotion)
                        VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param})
                    """
                    params = (student_id, classroom, date, time, latitude, longitude, gps_accuracy,
                              liveness_bool, face_confidence, emotion)
                else:  # PostgreSQL - use ::boolean cast for safe conversion
                    query = f"""
                        INSERT INTO attendance 
                        (student_id, classroom, date, time, latitude, longitude, gps_accuracy, 
                         liveness_verified, face_confidence, emotion)
                        VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}::boolean, {param}, {param})
                    """
                    params = (student_id, classroom, date, time, latitude, longitude, gps_accuracy,
                              liveness_bool, face_confidence, emotion)
                
                cursor.execute(query, params)
                return True
        except Exception as e:
            print(f"Error adding attendance: {e}")
            return False
    
    def get_attendance_for_student(self, student_id: str, days: int = 7) -> List[Dict]:
        """Get student attendance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            param = "?" if self.db_type == "sqlite" else "%s"
            
            if self.db_type == "sqlite":
                cursor.execute(f"""
                    SELECT * FROM attendance 
                    WHERE student_id = {param} AND date >= date('now', '-' || {param} || ' days')
                    ORDER BY timestamp DESC
                """, (student_id, days))
                return [dict(row) for row in cursor.fetchall()]
            else:
                cursor.execute(f"""
                    SELECT * FROM attendance 
                    WHERE student_id = {param} AND date >= CURRENT_DATE - INTERVAL '{days} days'
                    ORDER BY timestamp DESC
                """, (student_id,))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_attendance_by_date(self, date: str, classroom: Optional[str] = None) -> List[Dict]:
        """Get attendance by date, optionally filtered by classroom"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            param = "?" if self.db_type == "sqlite" else "%s"
            
            if classroom:
                if self.db_type == "sqlite":
                    cursor.execute(f"""
                        SELECT * FROM attendance 
                        WHERE date = {param} AND classroom = {param}
                        ORDER BY timestamp DESC
                    """, (date, classroom))
                else:
                    cursor.execute(f"""
                        SELECT * FROM attendance 
                        WHERE date = {param} AND classroom = {param}
                        ORDER BY timestamp DESC
                    """, (date, classroom))
            else:
                cursor.execute(f"""
                    SELECT * FROM attendance WHERE date = {param} ORDER BY timestamp DESC
                """, (date,))
            
            if self.db_type == "sqlite":
                return [dict(row) for row in cursor.fetchall()]
            else:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_recent_attendance(self, limit: int = 50) -> List[Dict]:
        """Get recent attendance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Use limit directly - PostgreSQL doesn't support parameterized LIMIT
            cursor.execute(f"""
                SELECT * FROM attendance ORDER BY timestamp DESC LIMIT {limit}
            """)
            
            if self.db_type == "sqlite":
                return [dict(row) for row in cursor.fetchall()]
            else:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Fraud Operations
    
    def add_fraud_attempt(self, student_id: str, fraud_type: str, details: str = "",
                         image_path: str = "", ip_address: str = "",
                         latitude: float = None, longitude: float = None,
                         severity: str = "medium") -> bool:
        """Log fraud attempt"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                params = (param,) * 8
                cursor.execute(f"""
                    INSERT INTO fraud_attempts 
                    (student_id, fraud_type, details, image_path, ip_address, latitude, longitude, severity)
                    VALUES ({', '.join(params)})
                """, (student_id, fraud_type, details, image_path, ip_address, latitude, longitude, severity))
                return True
        except Exception as e:
            print(f"Error adding fraud: {e}")
            return False
    
    def get_fraud_attempts(self, days: int = 7) -> List[Dict]:
        """Get fraud attempts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            param = "?" if self.db_type == "sqlite" else "%s"
            
            if self.db_type == "sqlite":
                cursor.execute(f"""
                    SELECT * FROM fraud_attempts 
                    WHERE timestamp >= datetime('now', '-' || {param} || ' days')
                    ORDER BY timestamp DESC
                """, (days,))
                return [dict(row) for row in cursor.fetchall()]
            else:
                cursor.execute(f"""
                    SELECT * FROM fraud_attempts 
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
                    ORDER BY timestamp DESC
                """)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # System Logs
    
    def log_system_event(self, level: str, module: str, message: str, details: str = "") -> bool:
        """Log system event"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                cursor.execute(f"""
                    INSERT INTO system_logs (level, module, message, details)
                    VALUES ({param}, {param}, {param}, {param})
                """, (level, module, message, details))
                return True
        except Exception as e:
            print(f"Error logging: {e}")
            return False
    
    # Sessions
    
    def create_session(self, session_id: str, classroom: str, subject: str = "",
                      teacher_name: str = "", start_time: datetime = None) -> bool:
        """Create session"""
        try:
            if start_time is None:
                start_time = datetime.now()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                cursor.execute(f"""
                    INSERT INTO sessions (session_id, classroom, subject, teacher_name, start_time)
                    VALUES ({param}, {param}, {param}, {param}, {param})
                """, (session_id, classroom, subject, teacher_name, start_time))
                return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            param = "?" if self.db_type == "sqlite" else "%s"
            cursor.execute(f"""
                SELECT * FROM sessions WHERE session_id = {param}
            """, (session_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            if self.db_type == "sqlite":
                return dict(row)
            else:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
    
    def end_session(self, session_id: str) -> bool:
        """End session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                cursor.execute(f"""
                    UPDATE sessions SET end_time = CURRENT_TIMESTAMP WHERE session_id = {param}
                """, (session_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error ending session: {e}")
            return False
    
    # Additional Attendance Operations
    
    def mark_attendance(self, student_id: str, classroom: str,
                       latitude: float = None, longitude: float = None,
                       gps_accuracy: float = None, liveness_verified: bool = False,
                       face_confidence: float = 0.0, emotion: str = None) -> bool:
        """Mark attendance for a student"""
        try:
            now = datetime.now()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                param = "?" if self.db_type == "sqlite" else "%s"
                
                # Convert boolean to appropriate type for database
                if self.db_type == "sqlite":
                    liveness_bool = 1 if liveness_verified else 0
                else:  # PostgreSQL - convert to SQL boolean literal
                    liveness_bool = 'true' if liveness_verified else 'false'
                
                # Build INSERT query with proper boolean handling
                if self.db_type == "sqlite":
                    query = f"""
                        INSERT INTO attendance (
                            student_id, classroom, timestamp, date, time,
                            latitude, longitude, gps_accuracy,
                            liveness_verified, face_confidence, emotion
                        ) VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param})
                    """
                    params = (
                        student_id, 
                        classroom, 
                        now.isoformat(),
                        now.date().isoformat(),
                        now.time().isoformat(),
                        latitude, 
                        longitude, 
                        gps_accuracy,
                        liveness_bool,
                        face_confidence, 
                        emotion
                    )
                else:  # PostgreSQL - use ::boolean cast for safe conversion
                    query = f"""
                        INSERT INTO attendance (
                            student_id, classroom, timestamp, date, time,
                            latitude, longitude, gps_accuracy,
                            liveness_verified, face_confidence, emotion
                        ) VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}::boolean, {param}, {param})
                    """
                    params = (
                        student_id, 
                        classroom, 
                        now.isoformat(),
                        now.date().isoformat(),
                        now.time().isoformat(),
                        latitude, 
                        longitude, 
                        gps_accuracy,
                        liveness_bool,
                        face_confidence, 
                        emotion
                    )
                
                cursor.execute(query, params)
                return True
        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False
    
    def check_attendance_today(self, student_id: str, classroom: str = None) -> tuple:
        """Check if student marked attendance today - returns (bool, record_dict)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                today = datetime.now().date().isoformat()
                param = "?" if self.db_type == "sqlite" else "%s"
                
                if classroom:
                    cursor.execute(f"""
                        SELECT * FROM attendance
                        WHERE student_id = {param}
                        AND date = {param}
                        AND classroom = {param}
                    """, (student_id, today, classroom))
                else:
                    cursor.execute(f"""
                        SELECT * FROM attendance
                        WHERE student_id = {param}
                        AND date = {param}
                    """, (student_id, today))
                
                row = cursor.fetchone()
                
                if row:
                    if self.db_type == "sqlite":
                        return (True, dict(row))
                    else:
                        columns = [desc[0] for desc in cursor.description]
                        return (True, dict(zip(columns, row)))
                else:
                    return (False, None)
        except Exception as e:
            print(f"Error checking attendance today: {e}")
            return (False, None)
    
    def log_fraud_attempt(self, fraud_type: str, student_id: str = None,
                         details: str = None, image_path: str = None,
                         ip_address: str = None, latitude: float = None,
                         longitude: float = None, severity: str = "medium") -> bool:
        """Log a fraud attempt"""
        return self.add_fraud_attempt(student_id, fraud_type, details, image_path, 
                                      ip_address, latitude, longitude, severity)
    
    def generate_daily_report(self, date: str) -> Dict:
        """Generate comprehensive daily report"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            param = "?" if self.db_type == "sqlite" else "%s"
            
            # Total attendance count
            cursor.execute(f"""
                SELECT COUNT(DISTINCT student_id) as total_present
                FROM attendance
                WHERE date = {param}
            """, (date,))
            row = cursor.fetchone()
            if self.db_type == "sqlite":
                total_present = row['total_present']
            else:
                total_present = row[0] if row else 0
            
            # By classroom
            cursor.execute(f"""
                SELECT classroom, COUNT(*) as count
                FROM attendance
                WHERE date = {param}
                GROUP BY classroom
            """, (date,))
            
            if self.db_type == "sqlite":
                by_classroom = {row['classroom']: row['count'] for row in cursor.fetchall()}
            else:
                by_classroom = {}
                for row in cursor.fetchall():
                    by_classroom[row[0]] = row[1]
            
            # Average face confidence
            cursor.execute(f"""
                SELECT AVG(face_confidence) as avg_confidence
                FROM attendance
                WHERE date = {param}
            """, (date,))
            row = cursor.fetchone()
            if self.db_type == "sqlite":
                avg_confidence = row['avg_confidence'] or 0.0
            else:
                avg_confidence = row[0] if row and row[0] else 0.0
            
            # Fraud attempts
            if self.db_type == "sqlite":
                date_func = "date(timestamp)"
            else:
                date_func = "DATE(timestamp)"
            
            cursor.execute(f"""
                SELECT COUNT(*) as fraud_count
                FROM fraud_attempts
                WHERE {date_func} = {param}
            """, (date,))
            row = cursor.fetchone()
            if self.db_type == "sqlite":
                fraud_count = row['fraud_count']
            else:
                fraud_count = row[0] if row else 0
            
            return {
                "date": date,
                "total_present": total_present,
                "by_classroom": by_classroom,
                "avg_face_confidence": round(avg_confidence, 2),
                "fraud_attempts": fraud_count
            }



class SQLiteDatabase(DatabaseBase):
    """SQLite database implementation"""
    
    def __init__(self, db_path: str = "data/smartattend.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_type = "sqlite"
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for SQLite connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create SQLite tables"""
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
                    face_encodings TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Attendance table
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
            
            # Sessions table
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
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fraud_timestamp ON fraud_attempts(timestamp)")
            
            conn.commit()
            print("[DB] SQLite database initialized")


class PostgreSQLDatabase(DatabaseBase):
    """PostgreSQL database implementation"""
    
    def __init__(self, database_url: str):
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("psycopg2 not installed: pip install psycopg2-binary")
        
        self.database_url = database_url
        self.db_type = "postgresql"
        
        # Test connection
        try:
            conn = psycopg2.connect(database_url)
            conn.close()
            print("[DB] PostgreSQL connection established")
        except Exception as e:
            print(f"[DB] PostgreSQL connection error: {e}")
            raise
        
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for PostgreSQL connections"""
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _execute_safe(self, sql: str):
        """Execute DDL statement in separate transaction"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
        except (psycopg2.errors.DuplicateTable, psycopg2.errors.DuplicateColumn, 
                psycopg2.errors.DuplicateObject):
            pass  # Table/column/index already exists
        except Exception as e:
            print(f"[DB] Warning: {e}")
    
    def _initialize_database(self):
        """Create PostgreSQL tables"""
        
        # Create each table in separate transaction
        self._execute_safe("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                roll_number VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(20),
                telegram_id VARCHAR(255),
                face_encodings TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Add face_encodings column if it doesn't exist (migration for existing databases)
        self._execute_safe("""
            ALTER TABLE students ADD COLUMN IF NOT EXISTS face_encodings TEXT
        """)
        
        self._execute_safe("""
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR(255) NOT NULL,
                classroom VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date DATE NOT NULL,
                time TIME NOT NULL,
                latitude FLOAT,
                longitude FLOAT,
                gps_accuracy FLOAT,
                liveness_verified BOOLEAN DEFAULT FALSE,
                face_confidence FLOAT,
                emotion VARCHAR(50),
                status VARCHAR(50) DEFAULT 'present',
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        """)
        
        self._execute_safe("""
            CREATE TABLE IF NOT EXISTS fraud_attempts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                student_id VARCHAR(255),
                fraud_type VARCHAR(100) NOT NULL,
                details TEXT,
                image_path VARCHAR(500),
                ip_address VARCHAR(50),
                latitude FLOAT,
                longitude FLOAT,
                severity VARCHAR(50) DEFAULT 'medium',
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        """)
        
        self._execute_safe("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                classroom VARCHAR(255) NOT NULL,
                subject VARCHAR(255),
                teacher_name VARCHAR(255),
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                total_students INTEGER DEFAULT 0,
                present_students INTEGER DEFAULT 0,
                engagement_score FLOAT,
                emotion_data TEXT
            )
        """)
        
        self._execute_safe("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level VARCHAR(50) NOT NULL,
                module VARCHAR(100),
                message TEXT NOT NULL,
                details TEXT
            )
        """)
        
        self._execute_safe("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # Create indexes
        self._execute_safe("CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)")
        self._execute_safe("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
        self._execute_safe("CREATE INDEX IF NOT EXISTS idx_fraud_timestamp ON fraud_attempts(timestamp)")
        
        print("[DB] PostgreSQL database initialized")


class AttendanceDatabase:
    """Factory that returns SQLite or PostgreSQL instance"""
    
    def __new__(cls, db_path: str = "data/smartattend.db"):
        db_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
        db_url = os.getenv("DATABASE_URL")
        
        if db_type == "postgresql" and db_url:
            print("[DB] Using PostgreSQL backend")
            return PostgreSQLDatabase(db_url)
        else:
            print("[DB] Using SQLite backend")
            return SQLiteDatabase(db_path)
