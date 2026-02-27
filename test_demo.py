#!/usr/bin/env python3
"""
Demo script to test SmartAttendAI functionality
"""

from src.face_recognition.recognizer import FaceRecognitionSystem
from config.settings import FACE_CONFIG
import numpy as np
import cv2

def create_sample_image():
    """Create a sample image for testing"""
    # Create a dummy image with a face-like region
    img = np.zeros((400, 300, 3), dtype=np.uint8)
    
    # Add some color to make it look like a photo
    img[:, :] = (50, 100, 150)  # Brownish background
    
    # Add a face-like oval
    center = (150, 200)
    axes = (80, 100)
    cv2.ellipse(img, center, axes, 0, 0, 360, (220, 180, 140), -1)
    
    # Add some basic features
    # Eyes
    cv2.circle(img, (120, 170), 10, (0, 0, 0), -1)
    cv2.circle(img, (180, 170), 10, (0, 0, 0), -1)
    
    # Nose
    cv2.ellipse(img, (150, 200), (8, 15), 0, 0, 360, (200, 160, 120), -1)
    
    # Mouth
    cv2.ellipse(img, (150, 230), (20, 8), 0, 0, 360, (150, 100, 100), -1)
    
    return img

def main():
    print("=== SmartAttendAI Demo ===")
    
    # Create face recognition system
    print("1. Initializing Face Recognition System...")
    face_system = FaceRecognitionSystem(FACE_CONFIG)
    
    # Create sample image
    print("2. Creating sample student image...")
    sample_image = create_sample_image()
    image_path = "data/faces/demo_student.jpg"
    cv2.imwrite(image_path, sample_image)
    print(f"   Sample image saved to: {image_path}")
    
    # Register a student
    print("3. Registering demo student...")
    result = face_system.register_face(
        image_path=image_path,
        student_name="Demo Student",
        student_id="DEMO001",
        roll_number="D001",
        email="demo@example.com",
        phone="+1234567890"
    )
    
    if result:
        print("   ✓ Student registration successful!")
    else:
        print("   ✗ Student registration failed!")
    
    # List registered students
    print("4. Listing registered students...")
    students = face_system.list_registered_students()
    print(f"   Found {len(students)} registered students:")
    for student in students:
        print(f"   - {student['name']} (ID: {student['id']})")
    
    # Test face recognition on the same image
    print("5. Testing face recognition...")
    test_image = cv2.imread(image_path)
    if test_image is not None:
        matched_student, annotated_frame, face_locations = face_system.recognize_face(test_image)
        
        if matched_student:
            print(f"   ✓ Face recognized: {matched_student['name']} (Confidence: {matched_student['confidence']:.2f})")
        else:
            print("   ✗ No face recognized")
        
        print(f"   Found {len(face_locations)} face(s) in image")
    
    print("6. Demo completed!")
    print("\nNote: This demo uses a mock implementation of face_recognition.")
    print("For production use, install the proper face_recognition library.")

if __name__ == "__main__":
    main()