"""
Notification Module
Send attendance confirmations and alerts via Telegram/SMS
"""
import os
from typing import Optional
from datetime import datetime
import asyncio

# Telegram
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
    print("✓ Telegram notifications enabled")
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("python-telegram-bot not installed. Telegram notifications disabled.")

# Twilio (SMS)
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("twilio not installed. SMS notifications disabled.")


class TelegramNotifier:
    """
    Send notifications via Telegram Bot
    """
    
    def __init__(self, bot_token: str):
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot is not installed")
        
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token) if bot_token else None
        
        if not self.bot:
            print("Warning: No Telegram bot token provided")
    
    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a Telegram user"""
        if not self.bot:
            print("Telegram bot not configured")
            return False
        
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            return True
        except TelegramError as e:
            print(f"Telegram error: {e}")
            return False
    
    async def send_attendance_confirmation(self, chat_id: str, student_name: str,
                                          classroom: str, timestamp: datetime) -> bool:
        """Send attendance confirmation message"""
        message = f"""
✅ Attendance Marked Successfully

Student: {student_name}
Classroom: {classroom}
Time: {timestamp.strftime('%I:%M %p')}
Date: {timestamp.strftime('%d %B %Y')}

Have a great class! 📚
        """
        return await self.send_message(chat_id, message.strip())
    
    async def send_fraud_alert(self, chat_id: str, fraud_type: str,
                              timestamp: datetime) -> bool:
        """Send fraud attempt alert"""
        message = f"""
🚨 SECURITY ALERT 🚨

Suspicious activity detected!

Type: {fraud_type}
Time: {timestamp.strftime('%I:%M %p, %d %B %Y')}

Your attendance was NOT marked.
If this was you, please try again or contact support.
        """
        return await self.send_message(chat_id, message.strip())
    
    async def send_daily_summary(self, chat_id: str, present_count: int,
                                total_count: int, date: str) -> bool:
        """Send daily attendance summary"""
        percentage = (present_count / total_count * 100) if total_count > 0 else 0
        
        message = f"""
📊 Daily Attendance Summary

Date: {date}
Present: {present_count}/{total_count} ({percentage:.1f}%)

{'✅ Great attendance!' if percentage >= 75 else '⚠️ Low attendance'}
        """
        return await self.send_message(chat_id, message.strip())


class SMSNotifier:
    """
    Send notifications via SMS (Twilio)
    """
    
    def __init__(self, account_sid: str, auth_token: str, phone_number: str):
        if not TWILIO_AVAILABLE:
            raise ImportError("twilio is not installed")
        
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        
        if account_sid and auth_token:
            self.client = TwilioClient(account_sid, auth_token)
        else:
            self.client = None
            print("Warning: Twilio credentials not provided")
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS message"""
        if not self.client:
            print("Twilio client not configured")
            return False
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            return True
        except TwilioRestException as e:
            print(f"Twilio error: {e}")
            return False
    
    def send_attendance_confirmation(self, to_number: str, student_name: str,
                                    classroom: str, timestamp: datetime) -> bool:
        """Send attendance confirmation SMS"""
        message = (
            f"Attendance marked for {student_name} "
            f"in {classroom} at {timestamp.strftime('%I:%M %p')}. "
            f"SmartAttendAI"
        )
        return self.send_sms(to_number, message)
    
    def send_fraud_alert(self, to_number: str, fraud_type: str) -> bool:
        """Send fraud alert SMS"""
        message = (
            f"ALERT: Suspicious attendance attempt detected ({fraud_type}). "
            f"Attendance NOT marked. Contact support if this was you. "
            f"SmartAttendAI"
        )
        return self.send_sms(to_number, message)


class NotificationManager:
    """
    Unified notification manager supporting multiple channels
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.api_keys = config.get("API_KEYS", {})
        self.notification_config = config.get("NOTIFICATION_CONFIG", {})
        
        # Initialize Telegram
        self.telegram = None
        if self.notification_config.get("TELEGRAM_ENABLED") and TELEGRAM_AVAILABLE:
            token = self.api_keys.get("TELEGRAM_BOT_TOKEN")
            if token:
                try:
                    self.telegram = TelegramNotifier(token)
                    print("Telegram notifications enabled")
                except Exception as e:
                    print(f"Failed to initialize Telegram: {e}")
        
        # Initialize SMS
        self.sms = None
        if self.notification_config.get("SMS_ENABLED") and TWILIO_AVAILABLE:
            sid = self.api_keys.get("TWILIO_ACCOUNT_SID")
            token = self.api_keys.get("TWILIO_AUTH_TOKEN")
            phone = self.api_keys.get("TWILIO_PHONE_NUMBER")
            if sid and token and phone:
                try:
                    self.sms = SMSNotifier(sid, token, phone)
                    print("SMS notifications enabled")
                except Exception as e:
                    print(f"Failed to initialize SMS: {e}")
    
    async def notify_attendance_success(self, student_data: dict) -> dict:
        """
        Send attendance confirmation to student
        
        Args:
            student_data: Dict with student_name, classroom, timestamp, 
                         telegram_id (optional), phone (optional)
        
        Returns:
            Dict with success status for each channel
        """
        results = {
            "telegram": False,
            "sms": False
        }
        
        student_name = student_data.get("student_name", "Student")
        classroom = student_data.get("classroom", "Classroom")
        timestamp = student_data.get("timestamp", datetime.now())
        
        # Send Telegram notification
        if self.telegram and student_data.get("telegram_id"):
            try:
                results["telegram"] = await self.telegram.send_attendance_confirmation(
                    chat_id=student_data["telegram_id"],
                    student_name=student_name,
                    classroom=classroom,
                    timestamp=timestamp
                )
            except Exception as e:
                print(f"Telegram notification error: {e}")
        
        # Send SMS notification
        if self.sms and student_data.get("phone"):
            try:
                results["sms"] = self.sms.send_attendance_confirmation(
                    to_number=student_data["phone"],
                    student_name=student_name,
                    classroom=classroom,
                    timestamp=timestamp
                )
            except Exception as e:
                print(f"SMS notification error: {e}")
        
        return results
    
    async def notify_fraud_attempt(self, student_data: dict, fraud_type: str) -> dict:
        """Send fraud alert to student"""
        results = {
            "telegram": False,
            "sms": False
        }
        
        timestamp = datetime.now()
        
        # Send Telegram alert
        if self.telegram and student_data.get("telegram_id"):
            try:
                results["telegram"] = await self.telegram.send_fraud_alert(
                    chat_id=student_data["telegram_id"],
                    fraud_type=fraud_type,
                    timestamp=timestamp
                )
            except Exception as e:
                print(f"Telegram alert error: {e}")
        
        # Send SMS alert
        if self.sms and student_data.get("phone"):
            try:
                results["sms"] = self.sms.send_fraud_alert(
                    to_number=student_data["phone"],
                    fraud_type=fraud_type
                )
            except Exception as e:
                print(f"SMS alert error: {e}")
        
        return results
    
    async def notify_admin(self, message: str, admin_contacts: dict) -> bool:
        """Send notification to admin/teacher"""
        success = False
        
        if self.telegram and admin_contacts.get("telegram_id"):
            try:
                success = await self.telegram.send_message(
                    chat_id=admin_contacts["telegram_id"],
                    message=message
                )
            except Exception as e:
                print(f"Admin notification error: {e}")
        
        return success


async def test_notifications():
    """Test notification system"""
    from config.settings import API_KEYS, NOTIFICATION_CONFIG
    
    config = {
        "API_KEYS": API_KEYS,
        "NOTIFICATION_CONFIG": NOTIFICATION_CONFIG
    }
    
    manager = NotificationManager(config)
    
    # Test data
    student_data = {
        "student_name": "Test Student",
        "classroom": "Room_101",
        "timestamp": datetime.now(),
        "telegram_id": "YOUR_TELEGRAM_CHAT_ID",  # Replace with actual chat ID
        "phone": "+1234567890"  # Replace with actual phone number
    }
    
    print("Testing attendance confirmation...")
    results = await manager.notify_attendance_success(student_data)
    print(f"Results: {results}")
    
    print("\nTesting fraud alert...")
    fraud_results = await manager.notify_fraud_attempt(
        student_data, 
        "photo_attack"
    )
    print(f"Fraud Alert Results: {fraud_results}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_notifications())