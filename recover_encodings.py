#!/usr/bin/env python3
"""
Recover face encodings from stored student photos
"""
import os
import face_recognition
import json
import pickle
from pathlib import Path
from src.utils.database import AttendanceDatabase
from config.settings import FACE_CONFIG

def recover_encodings():
    """Regenerate face encodings from student photos"""
    
    # Get students from database
    db = AttendanceDatabase()
    students = db.list_students()
    
    print(f"Found {len(students)} students in database")
    
    # Initialize face recognition system
    face_db_path = Path("data/faces")
    face_db_path.mkdir(parents=True, exist_ok=True)
    
    known_encodings = []
    known_metadata = []
    
    for student in students:
        student_id = student['student_id']
        photo_path = face_db_path / f"{student_id}.jpg"
        
        if not photo_path.exists():
            print(f"⚠️  No photo found for {student['name']} (ID: {student_id})")
            continue
        
        try:
            # Load image
            print(f"🔄 Processing {student['name']}...", end=" ")
            image = face_recognition.load_image_file(str(photo_path))
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                print(f"❌ No face detected in photo")
                continue
            
            if len(face_encodings) > 1:
                print(f"⚠️  Multiple faces detected, using first one")
            
            # Use first face encoding
            face_encoding = face_encodings[0]
            
            # Create metadata
            metadata = {
                "name": student['name'],
                "id": student['student_id'],
                "student_id": student['student_id'],  # Add this for compatibility
                "roll_number": student['roll_number'],
                "email": student['email'],
                "phone": student['phone'],
                "registered_at": student['registered_at'],
                "image_path": str(photo_path)
            }
            
            # Add to lists
            known_encodings.append(face_encoding)
            known_metadata.append(metadata)
            
            print(f"✓ Encoding generated (shape: {face_encoding.shape})")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    # Save encodings
    if known_encodings:
        encodings_file = face_db_path / "encodings.pkl"
        metadata_file = face_db_path / "metadata.json"
        
        with open(encodings_file, 'wb') as f:
            pickle.dump(known_encodings, f)
        
        with open(metadata_file, 'w') as f:
            json.dump(known_metadata, f, indent=2)
        
        print(f"\n✅ Successfully recovered {len(known_encodings)} face encodings")
        print(f"📁 Saved to: {encodings_file}")
        print(f"📁 Saved to: {metadata_file}")
        
        # List recovered students
        print("\n📋 Recovered students:")
        for meta in known_metadata:
            print(f"  - {meta['name']} (ID: {meta['id']})")
        
        return True
    else:
        print("\n❌ No face encodings could be recovered")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Face Encoding Recovery Tool")
    print("=" * 60)
    recover_encodings()
