#!/usr/bin/env python3
"""Debug script to test Telegram notifications"""
import os
import sys
import asyncio

# Add project root to path
sys.path.insert(0, '/c/SmartAttendAI')

from dotenv import load_dotenv
load_dotenv()

from config.settings import API_KEYS, NOTIFICATION_CONFIG
from src.utils.notifications import NotificationManager, TelegramNotifier

async def test_telegram():
    print("=" * 60)
    print("TELEGRAM NOTIFICATION TEST")
    print("=" * 60)
    
    # Check environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    print(f"\n1. Environment Check:")
    print(f"   TELEGRAM_BOT_TOKEN from os.getenv: {token[:20] if token else 'NOT FOUND'}...")
    
    # Check config settings
    print(f"\n2. Config Settings Check:")
    print(f"   API_KEYS['TELEGRAM_BOT_TOKEN']: {API_KEYS.get('TELEGRAM_BOT_TOKEN', 'NOT FOUND')[:20] if API_KEYS.get('TELEGRAM_BOT_TOKEN') else 'NOT FOUND'}...")
    print(f"   NOTIFICATION_CONFIG: {NOTIFICATION_CONFIG}")
    
    # Test NotificationManager
    print(f"\n3. NotificationManager Test:")
    config = {
        "API_KEYS": API_KEYS,
        "NOTIFICATION_CONFIG": NOTIFICATION_CONFIG
    }
    manager = NotificationManager(config)
    print(f"   Manager initialized: {manager is not None}")
    print(f"   Telegram available: {manager.telegram is not None}")
    
    if not manager.telegram:
        print("\n❌ ERROR: Telegram notifier is None! Bot token not loaded.")
        return False
    
    # Test actual message send
    print(f"\n4. Telegram Message Send Test:")
    print(f"   Testing with chat_id: 123456789 (replace with your actual chat ID)")
    
    # Note: This will fail with invalid chat ID, but we can see if the library works
    try:
        result = await manager.telegram.send_message(
            chat_id="123456789",
            message="🧪 Test message from SmartAttendAI"
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error (expected if invalid chat ID): {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    asyncio.run(test_telegram())
