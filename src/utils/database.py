"""
Database Module - PostgreSQL & SQLite Support
Handles attendance records, student data, and system logs
Supports both PostgreSQL (production) and SQLite (development)
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from contextlib import contextmanager
from collections import defaultdict

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False


class DatabaseBase:
    """Base class for database operations"""
    
    def _initialize_database(self):
        """Create database tables if they don't exist - to be implemented by subclasses"""
        raise NotImplementedError


class SQLiteDatabase(DatabaseBase):
    """SQLite database for attendance management"""
    
    def __init__(self, db_path: str = "data/smartattend.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_type = "sqlite"
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
            print("[DB] SQLite database initialized successfully")


class PostgreSQLDatabase(DatabaseBase):
    """PostgreSQL database for attendance management"""
    
    def __init__(self, database_url: str):
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("psycopg2 not available. Install with: pip install psycopg2-binary")
        
        self.database_url = database_url
        self.db_type = "postgresql"
        
        # Parse connection parameters
        self._parse_connection_url()
        self._initialize_database()
    
    def _parse_connection_url(self):
        """Parse PostgreSQL connection URL and test connection"""
        try:
            # Test the connection
            conn = psycopg2.connect(self.database_url)
            conn.close()
            print("[DB] PostgreSQL connection established")
        except Exception as e:
            print(f"[DB] PostgreSQL connection error: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(self.database_url)
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
        # Helper function to execute statement safely
        def execute_sql(sql: str, description: str = ""):
            try:
                conn = psycopg2.connect(self.database_url)
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                conn.close()
                if description:
                    print(f"[DB] {description}")
            except psycopg2.errors.DuplicateTable:
                pass  # Table already exists
            except psycopg2.errors.DuplicateColumn:
                pass  # Column already exists
            except psycopg2.errors.DuplicateObject:
                pass  # Index already exists
            except Exception as e:
                print(f"[DB] Warning during initialization: {e}")
        
        # Execute each CREATE TABLE in separate transaction
        execute_sql("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                roll_number VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(20),
                telegram_id VARCHAR(255),
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """, "Created students table")
        
        execute_sql("""
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
        """, "Created attendance table")
        
        execute_sql("""
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
        """, "Created fraud_attempts table")
        
        execute_sql("""
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
        """, "Created sessions table")
        
        execute_sql("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level VARCHAR(50) NOT NULL,
                module VARCHAR(100),
                message TEXT NOT NULL,
                details TEXT
            )
        """, "Created system_logs table")
        
        execute_sql("""
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
        """, "Created admin_users table")
        
        # Create indexes
        execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_attendance_student 
            ON attendance(student_id)
        """, "Created index idx_attendance_student")
        
        execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_attendance_date 
            ON attendance(date)
        """, "Created index idx_attendance_date")
        
        execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_fraud_timestamp 
            ON fraud_attempts(timestamp)
        """, "Created index idx_fraud_timestamp")
        
        print("[DB] PostgreSQL database initialization complete")


class AttendanceDatabase:
    """
    Smart wrapper that uses PostgreSQL or SQLite based on configuration
    Maintains same interface for backward compatibility
    """
    
    def __new__(cls, db_path: str = "data/smartattend.db"):
        # Check for PostgreSQL configuration
        database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
        database_url = os.getenv("DATABASE_URL")
        
        if database_type == "postgresql" and database_url:
            print("[DB] Using PostgreSQL as database backend")
            return PostgreSQLDatabase(database_url)
        else:
            print("[DB] Using SQLite as database backend")
            return SQLiteDatabase(db_path)
    
    # These methods are for the wrapper pattern
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        raise NotImplementedError
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        raise NotImplementedError
    
    # Student Operations (common interface)
    
    def add_student(self, student_id: str, name: str, roll_number: str,
                   email: str = "", phone: str = "", telegram_id: str = "") -> bool:
        """Add a new student to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO students (student_id, name, roll_number, email, phone, telegram_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (student_id, name, roll_number, email, phone, telegram_id))
                else:  # PostgreSQL
                    cursor.execute("""
                        INSERT INTO students (student_id, name, roll_number, email, phone, telegram_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (student_id, name, roll_number, email, phone, telegram_id))
                return True
        except (sqlite3.IntegrityError, psycopg2.IntegrityError) as e:
            print(f"Student already exists: {e}")
            return False
        except Exception as e:
            print(f"Error adding student: {e}")
            return False
    
    def get_student(self, student_id: str) -> Optional[Dict]:
        """Get student information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT * FROM students WHERE student_id = ?
                """, (student_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT * FROM students WHERE student_id = %s
                """, (student_id,))
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                return dict(zip(columns, row)) if row else None
    
    def list_students(self, active_only: bool = True) -> List[Dict]:
        """Get list of all students"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM students"
            if active_only:
                query += " WHERE is_active = TRUE" if self.db_type == "postgresql" else " WHERE is_active = 1"
            query += " ORDER BY name"
            
            cursor.execute(query)
            
            if self.db_type == "sqlite":
                return [dict(row) for row in cursor.fetchall()]
            else:  # PostgreSQL
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def delete_student(self, student_id: str) -> bool:
        """Soft delete a student by setting is_active to 0"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db_type == "sqlite":
                    cursor.execute("""
                        UPDATE students SET is_active = 0 WHERE student_id = ?
                    """, (student_id,))
                else:  # PostgreSQL
                    cursor.execute("""
                        UPDATE students SET is_active = FALSE WHERE student_id = %s
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
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO admin_users (username, email, full_name, password_hash)
                        VALUES (?, ?, ?, ?)
                    """, (username, email, full_name, password_hash))
                else:  # PostgreSQL
                    cursor.execute("""
                        INSERT INTO admin_users (username, email, full_name, password_hash)
                        VALUES (%s, %s, %s, %s)
                    """, (username, email, full_name, password_hash))
                return True
        except (sqlite3.IntegrityError, psycopg2.IntegrityError) as e:
            print(f"Admin user already exists: {e}")
            return False
        except Exception as e:
            print(f"Error creating admin user: {e}")
            return False
    
    def get_admin_user(self, username: str) -> Optional[Dict]:
        """Get admin user by username"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db_type == "sqlite":
                    cursor.execute("""
                        SELECT id, username, email, full_name, password_hash, is_active
                        FROM admin_users WHERE username = ? AND is_active = 1
                    """, (username,))
                    row = cursor.fetchone()
                    return dict(row) if row else None
                else:  # PostgreSQL
                    cursor.execute("""
                        SELECT id, username, email, full_name, password_hash, is_active
                        FROM admin_users WHERE username = %s AND is_active = TRUE
                    """, (username,))
                    columns = [desc[0] for desc in cursor.description]
                    row = cursor.fetchone()
                    return dict(zip(columns, row)) if row else None
        except Exception as e:
            print(f"Error getting admin user: {e}")
            return None
    
    def check_admin_exists(self, username: str = None, email: str = None) -> bool:
        """Check if admin user exists"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if username:
                    if self.db_type == "sqlite":
                        cursor.execute("SELECT 1 FROM admin_users WHERE username = ?", (username,))
                    else:  # PostgreSQL
                        cursor.execute("SELECT 1 FROM admin_users WHERE username = %s", (username,))
                elif email:
                    if self.db_type == "sqlite":
                        cursor.execute("SELECT 1 FROM admin_users WHERE email = ?", (email,))
                    else:  # PostgreSQL
                        cursor.execute("SELECT 1 FROM admin_users WHERE email = %s", (email,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking admin exists: {e}")
            return False
    
    def update_admin_last_login(self, username: str) -> bool:
        """Update admin user last login timestamp"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db_type == "sqlite":
                    cursor.execute("""
                        UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE username = ?
                    """, (username,))
                else:  # PostgreSQL
                    cursor.execute("""
                        UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE username = %s
                    """, (username,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating admin last login: {e}")
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
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO attendance 
                        (student_id, classroom, date, time, latitude, longitude, gps_accuracy, 
                         liveness_verified, face_confidence, emotion)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (student_id, classroom, date, time, latitude, longitude, gps_accuracy,
                          liveness_verified, face_confidence, emotion))
                else:  # PostgreSQL
                    cursor.execute("""
                        INSERT INTO attendance 
                        (student_id, classroom, date, time, latitude, longitude, gps_accuracy, 
                         liveness_verified, face_confidence, emotion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (student_id, classroom, date, time, latitude, longitude, gps_accuracy,
                          liveness_verified, face_confidence, emotion))
                return True
        except Exception as e:
            print(f"Error adding attendance record: {e}")
            return False
    
    def get_attendance_for_student(self, student_id: str, days: int = 7) -> List[Dict]:
        """Get recent attendance records for a student"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE student_id = ? AND date >= date('now', '-' || ? || ' days')
                    ORDER BY timestamp DESC
                """, (student_id, days))
                return [dict(row) for row in cursor.fetchall()]
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE student_id = %s AND date >= CURRENT_DATE - INTERVAL '%s days'
                    ORDER BY timestamp DESC
                """, (student_id, days))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_attendance_by_date(self, date: str) -> List[Dict]:
        """Get all attendance records for a specific date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT * FROM attendance WHERE date = ? ORDER BY timestamp DESC
                """, (date,))
                return [dict(row) for row in cursor.fetchall()]
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT * FROM attendance WHERE date = %s ORDER BY timestamp DESC
                """, (date,))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_recent_attendance(self, limit: int = 50) -> List[Dict]:
        """Get recent attendance records"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT * FROM attendance ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT * FROM attendance ORDER BY timestamp DESC LIMIT %s
                """, (limit,))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Fraud Detection Operations
    
    def add_fraud_attempt(self, student_id: str, fraud_type: str, details: str = "",
                         image_path: str = "", ip_address: str = "",
                         latitude: float = None, longitude: float = None,
                         severity: str = "medium") -> bool:
        """Log a fraud attempt"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO fraud_attempts 
                        (student_id, fraud_type, details, image_path, ip_address, latitude, longitude, severity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (student_id, fraud_type, details, image_path, ip_address, latitude, longitude, severity))
                else:  # PostgreSQL
                    cursor.execute("""
                        INSERT INTO fraud_attempts 
                        (student_id, fraud_type, details, image_path, ip_address, latitude, longitude, severity)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (student_id, fraud_type, details, image_path, ip_address, latitude, longitude, severity))
                return True
        except Exception as e:
            print(f"Error adding fraud attempt: {e}")
            return False
    
    def get_fraud_attempts(self, days: int = 7) -> List[Dict]:
        """Get fraud attempts from the past N days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT * FROM fraud_attempts 
                    WHERE timestamp >= datetime('now', '-' || ? || ' days')
                    ORDER BY timestamp DESC
                """, (days,))
                return [dict(row) for row in cursor.fetchall()]
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT * FROM fraud_attempts 
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                    ORDER BY timestamp DESC
                """, (days,))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # System Logs
    
    def log_system_event(self, level: str, module: str, message: str, details: str = "") -> bool:
        """Log a system event"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO system_logs (level, module, message, details)
                        VALUES (?, ?, ?, ?)
                    """, (level, module, message, details))
                else:  # PostgreSQL
                    cursor.execute("""
                        INSERT INTO system_logs (level, module, message, details)
                        VALUES (%s, %s, %s, %s)
                    """, (level, module, message, details))
                return True
        except Exception as e:
            print(f"Error logging system event: {e}")
            return False
    
    # Sessions
    
    def create_session(self, session_id: str, classroom: str, subject: str = "",
                      teacher_name: str = "", start_time: datetime = None) -> bool:
        """Create a new session"""
        try:
            if start_time is None:
                start_time = datetime.now()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO sessions (session_id, classroom, subject, teacher_name, start_time)
                        VALUES (?, ?, ?, ?, ?)
                    """, (session_id, classroom, subject, teacher_name, start_time))
                else:  # PostgreSQL
                    cursor.execute("""
                        INSERT INTO sessions (session_id, classroom, subject, teacher_name, start_time)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (session_id, classroom, subject, teacher_name, start_time))
                return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT * FROM sessions WHERE session_id = ?
                """, (session_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT * FROM sessions WHERE session_id = %s
                """, (session_id,))
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                return dict(zip(columns, row)) if row else None
    
    def end_session(self, session_id: str) -> bool:
        """End a session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db_type == "sqlite":
                    cursor.execute("""
                        UPDATE sessions SET end_time = CURRENT_TIMESTAMP WHERE session_id = ?
                    """, (session_id,))
                else:  # PostgreSQL
                    cursor.execute("""
                        UPDATE sessions SET end_time = CURRENT_TIMESTAMP WHERE session_id = %s
                    """, (session_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error ending session: {e}")
            return False
