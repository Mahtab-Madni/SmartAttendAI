"""
Face Recognition Module
Handles face encoding, matching, and database management
"""
import cv2
import numpy as np
import pickle
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import json
from datetime import datetime

print("Loading face recognition with OpenCV implementation...")

# Enhanced face_recognition implementation using OpenCV
class FaceRecognitionSystem:
    def __init__(self, config, database_path: str = "data/faces"):
        self.config = config
        self.database_path = Path(database_path)
        self.database_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenCV face detector and recognizer
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Use LBPH (Local Binary Patterns Histograms) face recognizer
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        self.known_encodings = []
        self.known_metadata = []  # Store name, id, etc.
        self.known_face_ids = []  # For LBPH training
        
        self.encodings_file = self.database_path / "encodings.pkl"
        self.metadata_file = self.database_path / "metadata.json"
        self.recognizer_file = self.database_path / "face_recognizer.yml"
        
        self.is_trained = False
        self.load_database()
    
    def load_database(self):
        """Load existing face encodings and metadata"""
        if (self.encodings_file.exists() and 
            self.metadata_file.exists() and
            self.recognizer_file.exists()):
            
            with open(self.encodings_file, 'rb') as f:
                self.known_encodings = pickle.load(f)
            
            with open(self.metadata_file, 'r') as f:
                self.known_metadata = json.load(f)
            
            # Rebuild face_ids from metadata
            self.known_face_ids = []
            for metadata in self.known_metadata:
                if 'face_id' in metadata:
                    self.known_face_ids.append(metadata['face_id'])
                else:
                    # Assign new face_id if missing
                    metadata['face_id'] = len(self.known_face_ids)
                    self.known_face_ids.append(metadata['face_id'])
            
            # Load the trained recognizer
            try:
                self.face_recognizer.read(str(self.recognizer_file))
                self.is_trained = True
            except Exception as e:
                print(f"Could not load trained model: {e}")
                self.is_trained = False
            
            print(f"Loaded {len(self.known_encodings)} face encodings from database")
        else:
            print("No existing database found. Starting fresh.")
    
    def save_database(self):
        """Save face encodings and metadata to disk"""
        with open(self.encodings_file, 'wb') as f:
            pickle.dump(self.known_encodings, f)
        
        with open(self.metadata_file, 'w') as f:
            json.dump(self.known_metadata, f, indent=2)
        
        # Save the trained recognizer
        if self.is_trained:
            self.face_recognizer.save(str(self.recognizer_file))
        
        print(f"Database saved with {len(self.known_encodings)} encodings")
    
    def _extract_face_features(self, image, face_rect):
        """Extract face features for recognition"""
        x, y, w, h = face_rect
        face_roi = image[y:y+h, x:x+w]
        
        # Resize to standard size
        face_roi = cv2.resize(face_roi, (200, 200))
        
        # Convert to grayscale if needed
        if len(face_roi.shape) == 3:
            face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        return face_roi
    
    def register_face(self, image_path: str, student_name: str, student_id: str,
                     roll_number: str, email: str = "", phone: str = "") -> bool:
        """
        Register a new student face in the system using OpenCV
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image: {image_path}")
            return False
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            print(f"No face found in {image_path}")
            return False
        
        if len(faces) > 1:
            print(f"Multiple faces found in {image_path}. Use a photo with only one face.")
            return False
        
        # Get the face region
        face_rect = faces[0]
        face_features = self._extract_face_features(gray, face_rect)
        
        # Store face ID for training
        face_id = len(self.known_metadata)
        
        # Create metadata
        metadata = {
            "name": student_name,
            "id": student_id,
            "roll_number": roll_number,
            "email": email,
            "phone": phone,
            "registered_at": datetime.now().isoformat(),
            "image_path": str(image_path),
            "face_id": face_id
        }
        
        # Add to database
        self.known_encodings.append(face_features)
        self.known_metadata.append(metadata)
        self.known_face_ids.append(face_id)
        
        # Retrain the recognizer
        self._train_recognizer()
        
        # Save to disk
        self.save_database()
        
        print(f"Successfully registered: {student_name} (ID: {student_id})")
        return True
    
    def _train_recognizer(self):
        """Train the LBPH face recognizer with current data"""
        if len(self.known_encodings) > 0 and len(self.known_face_ids) > 0:
            # Ensure arrays are compatible
            if len(self.known_encodings) == len(self.known_face_ids):
                try:
                    self.face_recognizer.train(self.known_encodings, np.array(self.known_face_ids))
                    self.is_trained = True
                    print(f"Face recognizer trained with {len(self.known_encodings)} samples")
                except Exception as e:
                    print(f"Training failed: {e}")
                    self.is_trained = False
            else:
                print(f"Warning: Sample count ({len(self.known_encodings)}) doesn't match label count ({len(self.known_face_ids)})")
                self.is_trained = False
    
    def recognize_face(self, frame: np.ndarray) -> Tuple[Optional[Dict], np.ndarray, List]:
        """
        Recognize faces in the frame using OpenCV LBPH
        
        Returns:
            Tuple of (matched_student_metadata, annotated_frame, face_locations)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return None, frame, []
        
        matched_student = None
        
        # Process each face
        for (x, y, w, h) in faces:
            # Check face size
            min_width, min_height = self.config["MIN_FACE_SIZE"]
            
            if w < min_width or h < min_height:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Face too small", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                continue
            
            # Extract face features
            face_roi = self._extract_face_features(gray, (x, y, w, h))
            
            # Recognize face if model is trained
            if self.is_trained and len(self.known_metadata) > 0:
                try:
                    # Predict using LBPH
                    label, confidence = self.face_recognizer.predict(face_roi)
                    
                    # Convert confidence to similarity (lower confidence = better match)
                    similarity = max(0, (100 - confidence) / 100)
                    
                    # Check if confidence is good enough
                    confidence_threshold = (1.0 - self.config["TOLERANCE"]) * 100
                    
                    if confidence < confidence_threshold:
                        # Find metadata for this face
                        for metadata in self.known_metadata:
                            if metadata.get("face_id") == label:
                                matched_student = metadata.copy()
                                matched_student["confidence"] = similarity
                                break
                        
                        if matched_student:
                            # Draw green box for recognized face
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            
                            # Draw label background
                            cv2.rectangle(frame, (x, y+h-35), (x+w, y+h), (0, 255, 0), cv2.FILLED)
                            
                            # Display name and confidence
                            text = f"{matched_student['name']} ({matched_student['confidence']:.2f})"
                            cv2.putText(frame, text, (x + 6, y+h - 6),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                        else:
                            # Unknown face (not in metadata)
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                            cv2.putText(frame, "Unknown", (x, y - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    else:
                        # Low confidence - unknown face
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(frame, f"Unknown ({similarity:.2f})", (x, y - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        
                except Exception as e:
                    print(f"Recognition error: {e}")
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.putText(frame, "Error", (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            else:
                # No trained model
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                cv2.putText(frame, "No database", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Convert face rectangles to the format expected by the rest of the system
        face_locations = [(y, x+w, y+h, x) for (x, y, w, h) in faces]  # (top, right, bottom, left)
        
        return matched_student, frame, face_locations
    
    def remove_face(self, student_id: str) -> bool:
        """Remove a student from the database"""
        for i, metadata in enumerate(self.known_metadata):
            if metadata["id"] == student_id:
                del self.known_encodings[i]
                del self.known_metadata[i]
                self.save_database()
                print(f"Removed student ID: {student_id}")
                return True
        
        print(f"Student ID {student_id} not found")
        return False
    
    def list_registered_students(self) -> List[Dict]:
        """Get list of all registered students"""
        return [
            {
                "name": m["name"],
                "id": m["id"],
                "roll_number": m["roll_number"],
                "registered_at": m["registered_at"]
            }
            for m in self.known_metadata
        ]
    
    def get_student_info(self, student_id: str) -> Optional[Dict]:
        """Get information about a specific student"""
        for metadata in self.known_metadata:
            if metadata["id"] == student_id:
                return metadata
        return None


def register_bulk_students(face_system: FaceRecognitionSystem, csv_file: str):
    """
    Register multiple students from a CSV file
    CSV format: name, id, roll_number, email, phone, image_path
    """
    import pandas as pd
    
    df = pd.read_csv(csv_file)
    
    success_count = 0
    fail_count = 0
    
    for _, row in df.iterrows():
        try:
            success = face_system.register_face(
                image_path=row['image_path'],
                student_name=row['name'],
                student_id=row['id'],
                roll_number=row['roll_number'],
                email=row.get('email', ''),
                phone=row.get('phone', '')
            )
            
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"Error registering {row['name']}: {e}")
            fail_count += 1
    
    print(f"\nRegistration complete: {success_count} successful, {fail_count} failed")


if __name__ == "__main__":
    from config.settings import FACE_CONFIG
    
    # Initialize system
    face_system = FaceRecognitionSystem(FACE_CONFIG)
    
    # Example: Register a student
    # face_system.register_face(
    #     image_path="data/faces/john_doe.jpg",
    #     student_name="John Doe",
    #     student_id="STU001",
    #     roll_number="22",
    #     email="john@example.com",
    #     phone="+1234567890"
    # )
    
    # Example: Test recognition
    cap = cv2.VideoCapture(0)
    
    print("Starting face recognition... Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        student, annotated, locations = face_system.recognize_face(frame)
        
        if student:
            print(f"Recognized: {student['name']} (Confidence: {student['confidence']:.2f})")
        
        cv2.imshow("Face Recognition", annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()