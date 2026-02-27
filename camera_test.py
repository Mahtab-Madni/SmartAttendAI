#!/usr/bin/env python3
"""
Camera Test Utility for SmartAttendAI
Tests camera availability and face detection
"""

import cv2
import numpy as np
from src.face_recognition.recognizer import FaceRecognitionSystem
from config.settings import FACE_CONFIG

def list_cameras():
    """Test available cameras"""
    print("Scanning for available cameras...")
    available_cameras = []
    
    for i in range(10):  # Test first 10 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                height, width = frame.shape[:2]
                print(f"  Camera {i}: Available ({width}x{height})")
                available_cameras.append(i)
            cap.release()
    
    if not available_cameras:
        print("  No cameras detected")
    
    return available_cameras

def test_face_detection(camera_id=0):
    """Test face detection with camera"""
    print(f"\nTesting face detection with camera {camera_id}...")
    print("Press 'q' to quit, 's' to save a test image")
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_id}")
        return False
    
    # Initialize face recognition
    face_system = FaceRecognitionSystem(FACE_CONFIG)
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to read frame")
                break
            
            frame_count += 1
            
            # Perform face recognition every 5 frames for performance
            if frame_count % 5 == 0:
                matched_student, annotated_frame, face_locations = face_system.recognize_face(frame)
                frame = annotated_frame
                
                # Display detection info
                info_text = f"Faces: {len(face_locations)}"
                if matched_student:
                    info_text += f" | Matched: {matched_student['name']} ({matched_student['confidence']:.2f})"
                
                cv2.putText(frame, info_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add instruction text
            cv2.putText(frame, "Press 'q' to quit, 's' to save image", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('SmartAttendAI Camera Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save test image
                filename = f"camera_test_{camera_id}_frame_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Saved image: {filename}")
                
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    return True

def create_test_pattern():
    """Create a test pattern for testing without camera"""
    print("\nCreating test pattern for offline testing...")
    
    # Create test image with multiple faces
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:, :] = (40, 40, 40)  # Dark background
    
    # Add title
    cv2.putText(img, "SmartAttendAI Test Pattern", (150, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Create face-like regions
    faces = [
        (100, 150, 120, 140),  # (x, y, w, h) Left face
        (400, 150, 120, 140),  # Right face
    ]
    
    names = ["Test Face 1", "Test Face 2"]
    
    for i, (x, y, w, h) in enumerate(faces):
        # Face oval
        center = (x + w//2, y + h//2)
        cv2.ellipse(img, center, (w//2, h//2), 0, 0, 360, (220, 180, 140), -1)
        
        # Eyes
        cv2.circle(img, (x + w//3, y + h//3), 8, (0, 0, 0), -1)
        cv2.circle(img, (x + 2*w//3, y + h//3), 8, (0, 0, 0), -1)
        
        # Nose
        cv2.ellipse(img, (x + w//2, y + h//2), (6, 12), 0, 0, 360, (200, 160, 120), -1)
        
        # Mouth
        cv2.ellipse(img, (x + w//2, y + 2*h//3), (15, 6), 0, 0, 360, (150, 100, 100), -1)
        
        # Name label
        cv2.putText(img, names[i], (x, y + h + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Save test pattern
    filename = "test_pattern.jpg"
    cv2.imwrite(filename, img)
    print(f"Test pattern saved as: {filename}")
    
    return filename

def test_face_recognition_offline():
    """Test face recognition with saved images"""
    print("\nTesting face recognition with test pattern...")
    
    # Create and load test pattern
    test_image_path = create_test_pattern()
    
    # Initialize face recognition
    face_system = FaceRecognitionSystem(FACE_CONFIG)
    
    # Load test image
    frame = cv2.imread(test_image_path)
    if frame is None:
        print("Error: Could not load test image")
        return
    
    # Perform face recognition
    matched_student, annotated_frame, face_locations = face_system.recognize_face(frame)
    
    print(f"Detected {len(face_locations)} faces")
    if matched_student:
        print(f"Recognized: {matched_student['name']} (confidence: {matched_student['confidence']:.2f})")
    else:
        print("No faces recognized (expected - no registered faces)")
    
    # Display result
    cv2.imshow('Face Recognition Test', annotated_frame)
    print("Press any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def main():
    print("=== SmartAttendAI Camera Test Utility ===")
    
    # Test available cameras
    cameras = list_cameras()
    
    if cameras:
        print(f"\nFound {len(cameras)} camera(s)")
        
        # Test with first available camera
        camera_id = cameras[0]
        print(f"Testing with camera {camera_id}...")
        
        choice = input("\nStart live camera test? (y/n): ").lower().strip()
        if choice == 'y':
            test_face_detection(camera_id)
    else:
        print("\nNo cameras available - running offline test")
    
    # Always run offline test
    print("\n" + "="*50)
    test_face_recognition_offline()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()