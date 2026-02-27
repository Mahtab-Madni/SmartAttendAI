#!/usr/bin/env python3
"""Check student data in database"""
import sys
sys.path.insert(0, '/c/SmartAttendAI')

from src.utils.database import AttendanceDatabase

db = AttendanceDatabase()
students = db.list_students()

print("=" * 70)
print("STUDENTS IN DATABASE")
print("=" * 70)

if not students:
    print("No students found!")
else:
    for student in students:
        print(f"\nStudent ID: {student['student_id']}")
        print(f"  Name: {student['name']}")
        print(f"  Email: {student.get('email', 'N/A')}")
        print(f"  Phone: {student.get('phone', 'N/A')}")
        print(f"  Telegram ID: {student.get('telegram_id', 'N/A')}")
        print(f"  Status: {'Active' if student.get('is_active') else 'Inactive'}")

print("\n" + "=" * 70)
