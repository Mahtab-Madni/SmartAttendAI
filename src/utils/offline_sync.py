"""
Offline Sync Module
Handles offline data storage and automatic sync when connection is restored
"""
import sqlite3
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
import requests
from enum import Enum


class SyncStatus(Enum):
    """Sync operation status"""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    RETRYING = "retrying"


class OfflineSyncManager:
    """
    Manages offline data sync
    Stores attendance records locally when offline and syncs when online
    """
    
    def __init__(self, queue_db_path: str = "data/offline_queue.db", max_queue_size: int = 1000):
        self.queue_db_path = Path(queue_db_path)
        self.queue_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_queue_size = max_queue_size
        self.sync_interval = 30  # Check for sync every 30 seconds
        self.is_syncing = False
        self._initialize_sync_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.queue_db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_sync_database(self):
        """Create offline sync tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Offline attendance queue
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_attendance_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    classroom TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    gps_accuracy REAL,
                    face_confidence REAL,
                    emotion TEXT,
                    student_name TEXT,
                    phone TEXT,
                    email TEXT,
                    telegram_id TEXT,
                    sync_status TEXT DEFAULT 'pending',
                    sync_attempt_count INTEGER DEFAULT 0,
                    last_sync_attempt TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Offline notifications queue
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_notifications_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    phone TEXT,
                    message TEXT NOT NULL,
                    notification_type TEXT,
                    classroom TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending',
                    sync_attempt_count INTEGER DEFAULT 0,
                    last_sync_attempt TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sync history for monitoring
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type TEXT NOT NULL,
                    records_synced INTEGER,
                    records_failed INTEGER,
                    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds FLOAT,
                    error_message TEXT
                )
            """)
    
    def queue_attendance(self, attendance_data: Dict) -> bool:
        """
        Queue an attendance record for offline/sync
        
        Args:
            attendance_data: Dict with attendance information
            
        Returns:
            bool: True if queued successfully
        """
        try:
            if not self._check_queue_space():
                print("[WARNING] Offline queue is full, dropping oldest record")
                self._delete_oldest_record()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now()
                
                cursor.execute("""
                    INSERT INTO offline_attendance_queue (
                        student_id, classroom, date, time, latitude, longitude,
                        gps_accuracy, face_confidence, emotion, student_name,
                        phone, email, telegram_id, sync_status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    attendance_data.get('student_id'),
                    attendance_data.get('classroom'),
                    now.date(),
                    now.time(),
                    attendance_data.get('latitude'),
                    attendance_data.get('longitude'),
                    attendance_data.get('gps_accuracy'),
                    attendance_data.get('face_confidence', 0.0),
                    attendance_data.get('emotion'),
                    attendance_data.get('student_name'),
                    attendance_data.get('phone'),
                    attendance_data.get('email'),
                    attendance_data.get('telegram_id'),
                    SyncStatus.PENDING.value,
                    now
                ))
                
                print(f"[OFFLINE] Queued attendance for {attendance_data.get('student_id')}")
                return True
        
        except Exception as e:
            print(f"[ERROR] Failed to queue attendance: {e}")
            return False
    
    def queue_notification(self, notification_data: Dict) -> bool:
        """
        Queue a notification for offline/sync
        
        Args:
            notification_data: Dict with notification information
            
        Returns:
            bool: True if queued successfully
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now()
                
                cursor.execute("""
                    INSERT INTO offline_notifications_queue (
                        student_id, phone, message, notification_type,
                        classroom, sync_status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    notification_data.get('student_id'),
                    notification_data.get('phone'),
                    notification_data.get('message'),
                    notification_data.get('notification_type', 'attendance'),
                    notification_data.get('classroom'),
                    SyncStatus.PENDING.value,
                    now
                ))
                
                print(f"[OFFLINE] Queued notification for {notification_data.get('student_id')}")
                return True
        
        except Exception as e:
            print(f"[ERROR] Failed to queue notification: {e}")
            return False
    
    def get_pending_attendance(self, limit: int = 100) -> List[Dict]:
        """Get pending attendance records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM offline_attendance_queue
                    WHERE sync_status = ?
                    LIMIT ?
                """, (SyncStatus.PENDING.value, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except Exception as e:
            print(f"[ERROR] Failed to get pending attendance: {e}")
            return []
    
    def get_pending_notifications(self, limit: int = 100) -> List[Dict]:
        """Get pending notifications"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM offline_notifications_queue
                    WHERE sync_status = ?
                    LIMIT ?
                """, (SyncStatus.PENDING.value, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except Exception as e:
            print(f"[ERROR] Failed to get pending notifications: {e}")
            return []
    
    def mark_record_synced(self, table: str, record_id: int) -> bool:
        """Mark a record as successfully synced"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE {table}
                    SET sync_status = ?, last_sync_attempt = ?
                    WHERE id = ?
                """, (SyncStatus.SYNCED.value, datetime.now(), record_id))
                
                return True
        
        except Exception as e:
            print(f"[ERROR] Failed to mark record synced: {e}")
            return False
    
    def mark_record_failed(self, table: str, record_id: int, error_message: str) -> bool:
        """Mark a record as failed sync"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current attempt count
                cursor.execute(f"SELECT sync_attempt_count FROM {table} WHERE id = ?", (record_id,))
                row = cursor.fetchone()
                current_count = row[0] if row else 0
                
                # Update to retrying status if under max attempts, else failed
                max_attempts = 5
                new_status = SyncStatus.RETRYING.value if current_count < max_attempts else SyncStatus.FAILED.value
                
                cursor.execute(f"""
                    UPDATE {table}
                    SET sync_status = ?, sync_attempt_count = ?, 
                        last_sync_attempt = ?, error_message = ?
                    WHERE id = ?
                """, (
                    new_status,
                    current_count + 1,
                    datetime.now(),
                    error_message,
                    record_id
                ))
                
                return True
        
        except Exception as e:
            print(f"[ERROR] Failed to mark record failed: {e}")
            return False
    
    def get_queue_stats(self) -> Dict:
        """Get statistics about the offline queue"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Attendance queue stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN sync_status = ? THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN sync_status = ? THEN 1 ELSE 0 END) as synced,
                        SUM(CASE WHEN sync_status = ? THEN 1 ELSE 0 END) as failed
                    FROM offline_attendance_queue
                """, (SyncStatus.PENDING.value, SyncStatus.SYNCED.value, SyncStatus.FAILED.value))
                
                attendance_stats = dict(cursor.fetchone())
                
                # Notification queue stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN sync_status = ? THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN sync_status = ? THEN 1 ELSE 0 END) as synced,
                        SUM(CASE WHEN sync_status = ? THEN 1 ELSE 0 END) as failed
                    FROM offline_notifications_queue
                """, (SyncStatus.PENDING.value, SyncStatus.SYNCED.value, SyncStatus.FAILED.value))
                
                notification_stats = dict(cursor.fetchone())
                
                return {
                    "attendance_queue": attendance_stats,
                    "notification_queue": notification_stats,
                    "is_syncing": self.is_syncing
                }
        
        except Exception as e:
            print(f"[ERROR] Failed to get queue stats: {e}")
            return {}
    
    def clear_synced_records(self, days_old: int = 7) -> int:
        """
        Clear successfully synced records older than N days
        
        Args:
            days_old: Number of days before deletion
            
        Returns:
            int: Number of records deleted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now().timestamp() - (days_old * 86400)
                
                # Delete old synced attendance records
                cursor.execute("""
                    DELETE FROM offline_attendance_queue
                    WHERE sync_status = ? AND created_at < datetime(?, 'unixepoch')
                """, (SyncStatus.SYNCED.value, cutoff_date))
                
                att_deleted = cursor.rowcount
                
                # Delete old synced notification records
                cursor.execute("""
                    DELETE FROM offline_notifications_queue
                    WHERE sync_status = ? AND created_at < datetime(?, 'unixepoch')
                """, (SyncStatus.SYNCED.value, cutoff_date))
                
                notif_deleted = cursor.rowcount
                total_deleted = att_deleted + notif_deleted
                
                print(f"[CLEANUP] Deleted {total_deleted} old synced records")
                return total_deleted
        
        except Exception as e:
            print(f"[ERROR] Failed to clear synced records: {e}")
            return 0
    
    def _check_queue_space(self) -> bool:
        """Check if queue has space"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM offline_attendance_queue")
                count = cursor.fetchone()[0]
                return count < self.max_queue_size
        except:
            return True
    
    def _delete_oldest_record(self):
        """Delete oldest record from queue"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM offline_attendance_queue
                    WHERE id = (
                        SELECT id FROM offline_attendance_queue
                        ORDER BY created_at ASC LIMIT 1
                    )
                """)
        except Exception as e:
            print(f"[ERROR] Failed to delete oldest record: {e}")


class NetworkMonitor:
    """
    Monitors network connectivity
    """
    
    def __init__(self, check_urls: List[str] = None, timeout: int = 5):
        self.check_urls = check_urls or [
            "https://8.8.8.8",
            "https://1.1.1.1",
            "https://www.google.com"
        ]
        self.timeout = timeout
        self._is_online = True
    
    async def is_online(self) -> bool:
        """
        Check if device is online
        
        Returns:
            bool: True if online, False if offline
        """
        for url in self.check_urls:
            try:
                response = requests.head(url, timeout=self.timeout, allow_redirects=True)
                if response.status_code < 400:
                    self._is_online = True
                    return True
            except:
                continue
        
        self._is_online = False
        return False
    
    def get_status(self) -> str:
        """Get current status"""
        return "online" if self._is_online else "offline"


# Global instances
_offline_sync_manager = None
_network_monitor = None


def get_offline_sync_manager(queue_db_path: str = "data/offline_queue.db", 
                             max_queue_size: int = 1000) -> OfflineSyncManager:
    """Get or create offline sync manager instance"""
    global _offline_sync_manager
    if _offline_sync_manager is None:
        _offline_sync_manager = OfflineSyncManager(queue_db_path, max_queue_size)
    return _offline_sync_manager


def get_network_monitor() -> NetworkMonitor:
    """Get or create network monitor instance"""
    global _network_monitor
    if _network_monitor is None:
        _network_monitor = NetworkMonitor()
    return _network_monitor
