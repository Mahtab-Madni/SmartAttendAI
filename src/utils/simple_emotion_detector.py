"""
Simple Emotion Detection Utility
Detects basic emotions from facial images using OpenCV and basic heuristics
"""
import cv2
import numpy as np
from typing import Tuple, Optional

class SimpleEmotionDetector:
    """
    Detects emotion from face images using basic image processing
    This is a lightweight alternative to deep learning models
    """
    
    def __init__(self):
        """Initialize emotion detector with cascade classifiers"""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.smile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_smile.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def detect_emotion(self, frame: np.ndarray) -> Tuple[str, float]:
        """
        Detect emotion from a frame (can be full frame or face crop)
        Returns: (emotion_label, confidence_score)
        
        Emotion categories:
        - happy: smiling, eyes open
        - focused: neutral expression, eyes open  
        - engaged: neutral with good texture
        - neutral: no distinctive features
        - bored: low texture/expression
        """
        try:
            if frame is None or frame.size == 0:
                print("[EMOTION] Invalid frame")
                return "neutral", 0.5
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            # Check if input is likely already a face crop (not too wide/tall)
            is_face_crop = (h > 50 and w > 50) and (h * 0.5 < w < h * 2)
            
            face_region = None
            
            if is_face_crop:
                # Input is likely a face crop - use it directly
                print(f"[EMOTION] Detected face crop ({w}x{h})")
                face_region = gray
            else:
                # Input is full frame - detect faces
                print("[EMOTION] Searching for faces in frame...")
                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
                )
                
                if len(faces) > 0:
                    # Use largest face
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest_face
                    face_region = gray[y:y+h, x:x+w]
                    print(f"[EMOTION] Found face of size {w}x{h}")
                else:
                    print("[EMOTION] No faces found in frame")
                    # Return neutral with lower confidence
                    return "neutral", 0.5
            
            if face_region is None or face_region.size == 0:
                return "neutral", 0.5
            
            # Analyze texture first (most reliable)
            texture_score = self._analyze_texture(face_region)
            print(f"[EMOTION] Texture score: {texture_score:.2f}")
            
            # Try to detect smiles
            try:
                smiles = self.smile_cascade.detectMultiScale(
                    face_region, scaleFactor=1.3, minNeighbors=8, minSize=(15, 15)
                )
                smile_count = len(smiles)
                print(f"[EMOTION] Smiles detected: {smile_count}")
            except:
                smile_count = 0
            
            # Try to detect eyes
            try:
                eyes = self.eye_cascade.detectMultiScale(
                    face_region, scaleFactor=1.02, minNeighbors=10, minSize=(10, 10)
                )
                eyes_open = len(eyes) >= 2
                print(f"[EMOTION] Eyes detected: {len(eyes)}, Open: {eyes_open}")
            except:
                eyes_open = True  # Assume eyes open if detection fails
            
            # Determine emotion based on features
            if smile_count > 0 and eyes_open and texture_score > 0.3:
                return "happy", 0.9
            elif eyes_open and texture_score > 0.7:
                return "focused", 0.8
            elif eyes_open and texture_score > 0.5:
                return "engaged", 0.75
            elif texture_score > 0.3:
                return "neutral", 0.7
            else:
                # Default to neutral rather than unknown
                return "neutral", 0.6
        
        except Exception as e:
            print(f"[EMOTION] Error detecting emotion: {e}")
            return "neutral", 0.5
    
    def _analyze_texture(self, face_region: np.ndarray) -> float:
        """
        Analyze face texture to gauge engagement
        Higher texture variation indicates more expression
        """
        try:
            if face_region.size == 0:
                return 0.5
            
            # Calculate Laplacian variance (measure of texture complexity)
            laplacian = cv2.Laplacian(face_region, cv2.CV_64F)
            variance = laplacian.var()
            
            # Adjust normalization - empirically found thresholds
            # High variance (50+) = good expression, Low variance (<10) = low expression
            if variance < 10:
                texture_score = variance / 20  # 0-0.5
            elif variance < 100:
                texture_score = 0.5 + (variance - 10) / 180  # 0.5-1.0
            else:
                texture_score = 1.0
            
            return min(1.0, max(0.0, texture_score))
        except Exception as e:
            print(f"[EMOTION] Texture analysis error: {e}")
            return 0.5
    
    def detect_emotional_state(self, frame: np.ndarray) -> str:
        """
        More detailed emotion classification
        """
        emotion, confidence = self.detect_emotion(frame)
        
        # Map basic emotions to extended categories
        emotion_map = {
            "happy": "happy",
            "focused": "focused",
            "engaged": "engaged",
            "neutral": "neutral",
            "bored": "bored",
            "unknown": "neutral"
        }
        
        return emotion_map.get(emotion, "neutral")

