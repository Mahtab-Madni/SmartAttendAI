"""
Sync Service
Background service for syncing offline data when connection is restored
"""
import asyncio
import time
from datetime import datetime
from typing import Optional
import requests
import json

from .offline_sync import get_offline_sync_manager, get_network_monitor


class SyncService:
    """
    Background service that:
    1. Monitors network connectivity
    2. Syncs pending records when online
    3. Handles retry logic for failed records
    """
    
    def __init__(self, db_manager=None, sync_interval: int = 30):
        self.offline_sync = get_offline_sync_manager()
        self.network_monitor = get_network_monitor()
        self.db = db_manager
        self.sync_interval = sync_interval
        self.is_running = False
        self.last_sync_time = 0
    
    async def start(self):
        """Start the background sync service"""
        self.is_running = True
        print("[SYNC SERVICE] Started")
        
        while self.is_running:
            try:
                # Check if online
                is_online = await self.network_monitor.is_online()
                
                if is_online:
                    # Check if enough time has passed since last sync
                    current_time = time.time()
                    if current_time - self.last_sync_time > self.sync_interval:
                        await self.sync_pending_records()
                        self.last_sync_time = current_time
                else:
                    print(f"[SYNC SERVICE] Device offline, will retry in {self.sync_interval}s")
                
                # Wait before next check
                await asyncio.sleep(self.sync_interval)
            
            except Exception as e:
                print(f"[SYNC SERVICE] Error: {e}")
                await asyncio.sleep(self.sync_interval)
    
    async def sync_pending_records(self):
        """Sync all pending records from offline queue"""
        print("[SYNC] Checking for pending records...")
        
        # Get pending attendance records
        pending_attendance = self.offline_sync.get_pending_attendance(limit=50)
        pending_notifications = self.offline_sync.get_pending_notifications(limit=50)
        
        if not pending_attendance and not pending_notifications:
            print("[SYNC] No pending records")
            return
        
        print(f"[SYNC] Found {len(pending_attendance)} attendance records, {len(pending_notifications)} notifications")
        
        # Sync attendance records
        if pending_attendance and self.db:
            await self._sync_attendance_records(pending_attendance)
        
        # Sync notifications
        if pending_notifications:
            await self._sync_notifications(pending_notifications)
        
        # Log sync completion
        stats = self.offline_sync.get_queue_stats()
        print(f"[SYNC] Complete. Queue stats: {stats}")
    
    async def _sync_attendance_records(self, records: list):
        """
        Sync pending attendance records with main database
        """
        print(f"[SYNC] Syncing {len(records)} attendance records...")
        
        synced_count = 0
        failed_count = 0
        
        for record in records:
            try:
                # Skip if already synced
                if record['sync_status'] == 'synced':
                    continue
                
                # Insert into main database
                if self.db:
                    success = self.db.mark_attendance(
                        student_id=record['student_id'],
                        classroom=record['classroom'],
                        latitude=record['latitude'],
                        longitude=record['longitude'],
                        gps_accuracy=record['gps_accuracy'],
                        liveness_verified=False,
                        face_confidence=record['face_confidence'],
                        emotion=record['emotion']
                    )
                    
                    if success:
                        # Mark as synced in offline queue
                        self.offline_sync.mark_record_synced(
                            'offline_attendance_queue',
                            record['id']
                        )
                        synced_count += 1
                        print(f"[SYNC] ✓ Synced attendance for {record['student_id']}")
                    else:
                        # Mark as failed
                        self.offline_sync.mark_record_failed(
                            'offline_attendance_queue',
                            record['id'],
                            "Database insertion failed"
                        )
                        failed_count += 1
                else:
                    failed_count += 1
            
            except Exception as e:
                print(f"[SYNC] ✗ Error syncing record {record['id']}: {e}")
                self.offline_sync.mark_record_failed(
                    'offline_attendance_queue',
                    record['id'],
                    str(e)
                )
                failed_count += 1
        
        print(f"[SYNC] Attendance sync complete: {synced_count} synced, {failed_count} failed")
    
    async def _sync_notifications(self, records: list):
        """
        Retry sending pending notifications
        """
        print(f"[SYNC] Retrying {len(records)} notifications...")
        
        from .notifications import NotificationManager
        from config.settings import API_KEYS, NOTIFICATION_CONFIG
        
        config = {
            "API_KEYS": API_KEYS,
            "NOTIFICATION_CONFIG": NOTIFICATION_CONFIG
        }
        
        notif_manager = NotificationManager(config)
        synced_count = 0
        failed_count = 0
        
        for record in records:
            try:
                if record['sync_status'] == 'synced':
                    continue
                
                # Get full student data from database
                student = self.db.get_student(record['student_id'])
                if not student:
                    print(f"[SYNC] ✗ Student {record['student_id']} not found")
                    self.offline_sync.mark_record_failed(
                        'offline_notifications_queue',
                        record['id'],
                        "Student not found"
                    )
                    continue
                
                # Reconstruct student data for notification
                student_data = {
                    "student_id": record['student_id'],
                    "student_name": student.get('name', record['student_id']),
                    "telegram_id": student.get('telegram_id'),
                    "phone": record['phone'],
                    "classroom": record['classroom'],
                    "timestamp": datetime.now()
                }
                
                # Send notification based on type
                success = False
                if record['notification_type'] == 'attendance_success':
                    results = await notif_manager.notify_attendance_success(student_data)
                    success = any(results.values())
                else:
                    # Generic message send via Telegram
                    if notif_manager.telegram and student_data.get('telegram_id'):
                        success = await notif_manager.telegram.send_message(
                            chat_id=student_data['telegram_id'],
                            message=record['message']
                        )
                
                if success:
                    self.offline_sync.mark_record_synced(
                        'offline_notifications_queue',
                        record['id']
                    )
                    synced_count += 1
                    print(f"[SYNC] ✓ Notification sent to {record['student_id']}")
                else:
                    self.offline_sync.mark_record_failed(
                        'offline_notifications_queue',
                        record['id'],
                        "Notification send failed"
                    )
                    failed_count += 1
            
            except Exception as e:
                print(f"[SYNC] ✗ Error syncing notification {record['id']}: {e}")
                self.offline_sync.mark_record_failed(
                    'offline_notifications_queue',
                    record['id'],
                    str(e)
                )
                failed_count += 1
        
        print(f"[SYNC] Notification sync complete: {synced_count} sent, {failed_count} failed")
    
    def stop(self):
        """Stop the sync service"""
        self.is_running = False
        print("[SYNC SERVICE] Stopped")
    
    async def force_sync(self):
        """Force immediate sync (useful for testing)"""
        print("[SYNC] Force sync initiated")
        await self.sync_pending_records()


# Global sync service instance
_sync_service: Optional[SyncService] = None


def get_sync_service(db_manager=None, sync_interval: int = 30) -> SyncService:
    """Get or create sync service instance"""
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService(db_manager, sync_interval)
    return _sync_service


def start_sync_service(db_manager=None, sync_interval: int = 30):
    """Start the background sync service"""
    service = get_sync_service(db_manager, sync_interval)
    # Return the coroutine to be awaited elsewhere
    return service.start()
