"""
Face Recognition Module
Handles face encoding, matching, and database management
Uses face_recognition library for better accuracy
"""
import cv2
import numpy as np
import pickle
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import json
from datetime import datetime
import face_recognition

print("Loading face recognition with face_recognition library...")

class FaceRecognitionSystem:
    def __init__(self, config, database_path: str = "data/faces", db_instance=None):
        self.config = config
        self.database_path = Path(database_path)
        self.database_path.mkdir(parents=True, exist_ok=True)
        self.db = db_instance  # Database instance for saving encodings
        
        self.known_encodings = []
        self.known_metadata = []  # Store name, id, etc.
        
        self.encodings_file = self.database_path / "encodings.pkl"
        self.metadata_file = self.database_path / "metadata.json"
        
        self.load_database()
    
    def load_database(self):
        """Load existing face encodings and metadata"""
        if self.encodings_file.exists() and self.metadata_file.exists():
            try:
                with open(self.encodings_file, 'rb') as f:
                    loaded_encodings = pickle.load(f)
                
                with open(self.metadata_file, 'r') as f:
                    self.known_metadata = json.load(f)
                
                # Validate and clean encodings - ensure they're all proper numpy arrays
                valid_encodings = []
                valid_metadata = []
                
                for idx, encoding in enumerate(loaded_encodings):
                    try:
                        # Convert to numpy array if needed
                        if isinstance(encoding, list):
                            encoding = np.array(encoding, dtype=np.float64)
                        elif not isinstance(encoding, np.ndarray):
                            print(f"[LOAD] Skipping encoding {idx}: Wrong type {type(encoding)}")
                            continue
                        
                        # Check shape - should be (128,)
                        if encoding.shape != (128,):
                            print(f"[LOAD] Skipping encoding {idx}: Wrong shape {encoding.shape}, expected (128,)")
                            continue
                        
                        # Ensure float64 type
                        encoding = encoding.astype(np.float64)
                        
                        valid_encodings.append(encoding)
                        if idx < len(self.known_metadata):
                            valid_metadata.append(self.known_metadata[idx])
                        
                    except Exception as e:
                        print(f"[LOAD] Error validating encoding {idx}: {e}")
                        continue
                
                self.known_encodings = valid_encodings
                self.known_metadata = valid_metadata
                
                print(f"Loaded {len(self.known_encodings)} valid face encodings from database (cleaned {len(loaded_encodings) - len(self.known_encodings)} invalid)")
            
            except (ModuleNotFoundError, pickle.UnpicklingError, EOFError) as e:
                # Pickle file is corrupted or incompatible - start fresh
                print(f"[LOAD] Pickle file corrupted/incompatible ({type(e).__name__}): {e}")
                print("[LOAD] Starting fresh with empty database")
                self.known_encodings = []
                self.known_metadata = []
        else:
            print("No existing database found. Starting fresh.")
    
    def save_database(self):
        """Save face encodings and metadata to disk"""
        # Ensure all encodings are proper numpy arrays before saving
        cleaned_encodings = []
        for enc in self.known_encodings:
            if isinstance(enc, np.ndarray):
                cleaned_encodings.append(enc.astype(np.float64))
            elif isinstance(enc, list):
                cleaned_encodings.append(np.array(enc, dtype=np.float64))
            else:
                print(f"[SAVE] Warning: Skipping encoding of type {type(enc)}")
                continue
        
        with open(self.encodings_file, 'wb') as f:
            pickle.dump(cleaned_encodings, f)
        
        with open(self.metadata_file, 'w') as f:
            json.dump(self.known_metadata, f, indent=2)
        
        print(f"Database saved with {len(cleaned_encodings)} encodings")
    
    def register_face(self, image_path: str, student_name: str, student_id: str,
                     roll_number: str, email: str = "", phone: str = "") -> bool:
        """
        Register a new student face in the system using face_recognition library
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Resize for faster processing (optional but recommended)
            image = cv2.resize(image, (500, 500))
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                print(f"No face found in {image_path}")
                return False
            
            if len(face_encodings) > 1:
                print(f"Multiple faces found in {image_path}. Use a photo with only one face.")
                return False
            
            # Get the single face encoding
            face_encoding = face_encodings[0]
            
            # Create metadata
            metadata = {
                "name": student_name,
                "id": student_id,
                "roll_number": roll_number,
                "email": email,
                "phone": phone,
                "registered_at": datetime.now().isoformat(),
                "image_path": str(image_path)
            }
            
            # Add to database
            self.known_encodings.append(face_encoding)
            self.known_metadata.append(metadata)
            
            # Save to disk
            self.save_database()
            
            # Save face encodings to database if db instance is available
            if self.db:
                import json as json_module
                encodings_list = [enc.tolist() if isinstance(enc, np.ndarray) else enc 
                                 for enc in self.known_encodings]
                encodings_json = json_module.dumps(encodings_list)
                self.db.save_face_encodings(student_id, encodings_json)
                print(f"[DB] Face encodings saved for student {student_id}")
            
            print(f"Successfully registered: {student_name} (ID: {student_id})")
            return True
            
        except Exception as e:
            print(f"Error registering face: {e}")
            return False
    
    def recognize_face(self, frame: np.ndarray) -> Tuple[Optional[Dict], np.ndarray, List]:
        """
        Recognize faces in the frame using face_recognition library
        
        Returns:
            Tuple of (matched_student_metadata, annotated_frame, face_locations)
        """
        # Resize frame for faster processing but keep quality
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)  # 50% instead of 25%
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find faces in frame - use HOG for speed
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        
        print(f"[RECOGNIZER] Faces detected in frame: {len(face_locations)}")
        
        if len(face_locations) == 0:
            return None, frame, []
        
        # Get face encodings for detected faces
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        print(f"[RECOGNIZER] Got {len(face_encodings)} face encodings")
        print(f"[RECOGNIZER] Known encodings in database: {len(self.known_encodings)}")
        
        # Validate face encodings
        valid_face_encodings = []
        valid_face_locations = []
        for i, encoding in enumerate(face_encodings):
            if isinstance(encoding, np.ndarray) and encoding.shape == (128,):
                valid_face_encodings.append(encoding.astype(np.float64))
                valid_face_locations.append(face_locations[i])
            else:
                print(f"[RECOGNIZER] Warning: Invalid face encoding {i}, shape {encoding.shape if isinstance(encoding, np.ndarray) else 'not ndarray'}")
        
        if not valid_face_encodings:
            print("[RECOGNIZER] No valid face encodings extracted")
            return None, frame, []
        
        face_encodings = valid_face_encodings
        face_locations = valid_face_locations
        
        matched_student = None
        best_confidence = 0.0
        best_distance = float('inf')
        
        # Process each face
        for idx, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
            # Scale back up face locations
            top, right, bottom, left = face_location
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2
            
            # Check minimum face size
            face_width = right - left
            face_height = bottom - top
            min_width, min_height = self.config.get("MIN_FACE_SIZE", (80, 80))
            
            print(f"[RECOGNIZER] Face {idx+1}: Size {face_width}x{face_height}, Min required: {min_width}x{min_height}")
            
            if face_width < min_width or face_height < min_height:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, "Face too small", (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                continue
            
            # Compare with known faces
            if len(self.known_encodings) > 0:
                try:
                    # Convert known_encodings list to numpy array for comparison
                    known_encodings_array = np.array(self.known_encodings, dtype=np.float64)
                    
                    # Ensure face_encoding is float64
                    face_encoding = face_encoding.astype(np.float64)
                    
                    # Calculate face distances
                    face_distances = face_recognition.face_distance([enc for enc in self.known_encodings], face_encoding)
                    
                    print(f"[RECOGNIZER] Face {idx+1} distances: min={face_distances.min():.3f}, max={face_distances.max():.3f}, mean={face_distances.mean():.3f}")
                    
                    # Get best match
                    best_match_index = np.argmin(face_distances)
                    best_distance_current = face_distances[best_match_index]
                    
                except Exception as e:
                    print(f"[RECOGNIZER] Error comparing face {idx+1}: {e}")
                    print(f"[RECOGNIZER] Known encodings: {len(self.known_encodings)}, Face encoding shape: {face_encoding.shape}")
                    continue
                
                # Convert distance to confidence (0.0 to 1.0)
                # Lower distance = higher confidence
                confidence = 1.0 - best_distance_current
                
                # Check tolerance
                tolerance = self.config.get("TOLERANCE", 0.6)
                
                print(f"[RECOGNIZER] Best match: Index {best_match_index}, Distance {best_distance_current:.3f}, Tolerance {tolerance:.3f}, Confidence {confidence:.3f}")
                
                if best_distance_current <= tolerance:
                    # Face recognized
                    student_info = self.known_metadata[best_match_index].copy()
                    student_info["confidence"] = float(confidence)
                    
                    print(f"[RECOGNIZER] ✓ MATCH FOUND: {student_info.get('name')} (confidence: {confidence:.3f})")
                    
                    # Only update matched_student if this is the best match so far
                    if confidence > best_confidence:
                        matched_student = student_info
                        best_confidence = confidence
                        best_distance = best_distance_current
                    
                    # Draw green box for recognized face
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    
                    # Draw label background
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                    
                    # Display name and confidence
                    text = f"{student_info['name']} ({confidence:.2f})"
                    cv2.putText(frame, text, (left + 6, bottom - 6),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                else:
                    # Unknown face (distance too high)
                    print(f"[RECOGNIZER] X NO MATCH: Distance {best_distance_current:.3f} exceeds tolerance {tolerance:.3f}")
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, f"Unknown ({confidence:.2f})", (left, top - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            else:
                # No database
                print(f"[RECOGNIZER] ! Database is empty - no students registered")
                cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
                cv2.putText(frame, "No database", (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Scale face locations back to original size
        face_locations_scaled = [(top*2, right*2, bottom*2, left*2) for (top, right, bottom, left) in face_locations]
        
        print(f"[RECOGNIZER] Final result: Matched={matched_student is not None}, Best confidence={best_confidence:.3f}")
        
        return matched_student, frame, face_locations_scaled
    
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
    # Example configuration
    FACE_CONFIG = {
        "TOLERANCE": 0.5,
        "MIN_FACE_SIZE": (80, 80)
    }
    
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