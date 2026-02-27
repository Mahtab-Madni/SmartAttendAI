"""
Liveness Detection Module
Implements Eye Blink Detection using Eye Aspect Ratio (EAR)
"""
import cv2
import numpy as np
from scipy.spatial import distance
import dlib
from imutils import face_utils
import time
from typing import Tuple, Optional

class LivenessDetector:
    def __init__(self, config):
        self.config = config
        self.ear_threshold = config["EAR_THRESHOLD"]
        self.consecutive_frames = config["CONSECUTIVE_FRAMES"]
        self.blink_counter = 0
        self.frame_counter = 0
        self.total_blinks = 0
        self.start_time = time.time()
        
        # Load dlib's face detector and facial landmark predictor
        self.detector = dlib.get_frontal_face_detector()
        # Download shape predictor: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
        self.predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
        
        # Eye landmark indices
        self.LEFT_EYE_START = 42
        self.LEFT_EYE_END = 48
        self.RIGHT_EYE_START = 36
        self.RIGHT_EYE_END = 42
    
    def calculate_ear(self, eye: np.ndarray) -> float:
        """
        Calculate Eye Aspect Ratio (EAR)
        
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        
        Where p1-p6 are eye landmark coordinates
        """
        # Vertical distances
        A = distance.euclidean(eye[1], eye[5])
        B = distance.euclidean(eye[2], eye[4])
        
        # Horizontal distance
        C = distance.euclidean(eye[0], eye[3])
        
        # Calculate EAR
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blinks(self, frame: np.ndarray) -> Tuple[bool, str, np.ndarray]:
        """
        Detect eye blinks in the frame
        
        Returns:
            Tuple of (is_live, status_message, annotated_frame)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray, 0)
        
        if len(faces) == 0:
            return False, "No face detected", frame
        
        if len(faces) > 1:
            return False, "Multiple faces detected", frame
        
        # Get facial landmarks
        face = faces[0]
        landmarks = self.predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)
        
        # Extract eye coordinates
        left_eye = landmarks[self.LEFT_EYE_START:self.LEFT_EYE_END]
        right_eye = landmarks[self.RIGHT_EYE_START:self.RIGHT_EYE_END]
        
        # Calculate EAR for both eyes
        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Draw eye contours
        left_eye_hull = cv2.convexHull(left_eye)
        right_eye_hull = cv2.convexHull(right_eye)
        cv2.drawContours(frame, [left_eye_hull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [right_eye_hull], -1, (0, 255, 0), 1)
        
        # Check if eyes are closed (blink detected)
        if avg_ear < self.ear_threshold:
            self.frame_counter += 1
        else:
            # Eyes opened after being closed
            if self.frame_counter >= self.consecutive_frames:
                self.total_blinks += 1
            self.frame_counter = 0
        
        # Check elapsed time
        elapsed_time = time.time() - self.start_time
        
        # Display information
        cv2.putText(frame, f"EAR: {avg_ear:.2f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Blinks: {self.total_blinks}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Time: {int(elapsed_time)}s", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Verify liveness based on blink count and time
        if elapsed_time >= self.config["BLINK_TIME_WINDOW"]:
            min_blinks = self.config["MIN_BLINKS"]
            max_blinks = self.config["MAX_BLINKS"]
            
            if self.total_blinks < min_blinks:
                return False, "Suspicious: Too few blinks (possible photo)", frame
            elif self.total_blinks > max_blinks:
                return False, "Suspicious: Too many blinks (possible attack)", frame
            else:
                return True, "Liveness verified", frame
        
        return None, f"Verifying... ({int(elapsed_time)}s)", frame
    
    def reset(self):
        """Reset detection counters"""
        self.blink_counter = 0
        self.frame_counter = 0
        self.total_blinks = 0
        self.start_time = time.time()


class TextureAnalyzer:
    """
    CNN-based texture analysis to detect screen/print patterns
    """
    def __init__(self, model_path: Optional[str] = None):
        self.model = self._load_model(model_path)
    
    def _load_model(self, model_path: Optional[str]):
        """Load pre-trained CNN model for spoof detection"""
        try:
            import tensorflow as tf
            if model_path and os.path.exists(model_path):
                return tf.keras.models.load_model(model_path)
            else:
                # Return None if model not available
                # In production, train this model using real/fake face dataset
                print("Warning: Texture analysis model not found. Using basic checks.")
                return None
        except Exception as e:
            print(f"Error loading texture model: {e}")
            return None
            return None
    
    def analyze(self, face_region: np.ndarray) -> Tuple[bool, float]:
        """
        Analyze face texture for spoofing patterns
        
        Returns:
            Tuple of (is_real, confidence_score)
        """
        if self.model is None:
            # Fallback: Basic texture analysis using frequency domain
            return self._basic_analysis(face_region)
        
        # Preprocess for CNN
        face_resized = cv2.resize(face_region, (224, 224))
        face_normalized = face_resized / 255.0
        face_batch = np.expand_dims(face_normalized, axis=0)
        
        # Predict
        prediction = self.model.predict(face_batch)[0][0]
        is_real = prediction > 0.5
        confidence = prediction if is_real else 1 - prediction
        
        return is_real, confidence
    
    def _basic_analysis(self, face_region: np.ndarray) -> Tuple[bool, float]:
        """
        Basic texture analysis using frequency domain (FFT)
        Screens have regular pixel patterns that show up in frequency domain
        """
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        
        # Apply FFT
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.abs(f_shift)
        
        # High-frequency content indicates screen patterns
        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2
        
        # Calculate high-frequency energy (corners)
        corner_size = min(h, w) // 4
        corners = (
            magnitude[:corner_size, :corner_size].sum() +
            magnitude[:corner_size, -corner_size:].sum() +
            magnitude[-corner_size:, :corner_size].sum() +
            magnitude[-corner_size:, -corner_size:].sum()
        )
        
        # Calculate center energy (low frequency)
        center = magnitude[
            center_h - corner_size:center_h + corner_size,
            center_w - corner_size:center_w + corner_size
        ].sum()
        
        # Ratio: Real faces have more low-frequency content
        ratio = center / (corners + 1e-6)
        
        # Threshold-based decision
        is_real = ratio > 5.0  # Empirical threshold
        confidence = min(ratio / 10.0, 1.0)
        
        return is_real, confidence


class ChallengeResponseVerifier:
    """
    Random challenge-response verification
    """
    def __init__(self, challenges: list):
        self.challenges = challenges
        self.current_challenge = None
        self.challenge_start_time = None
        self.timeout = 10  # seconds
    
    def generate_challenge(self) -> str:
        """Generate random challenge"""
        import random
        self.current_challenge = random.choice(self.challenges)
        self.challenge_start_time = time.time()
        return self.current_challenge
    
    def verify_response(self, frame: np.ndarray) -> Tuple[bool, str]:
        """
        Verify if user performed the challenge
        This is a placeholder - actual implementation needs action recognition
        """
        if self.current_challenge is None:
            return False, "No active challenge"
        
        elapsed = time.time() - self.challenge_start_time
        if elapsed > self.timeout:
            return False, "Challenge timeout"
        
        # TODO: Implement actual action recognition
        # For now, return success after showing challenge for some time
        if elapsed > 3:
            return True, "Challenge passed"
        
        return None, f"Perform: {self.current_challenge}"
    
    def reset(self):
        """Reset challenge state"""
        self.current_challenge = None
        self.challenge_start_time = None


if __name__ == "__main__":
    # Test the liveness detector
    from config.settings import LIVENESS_CONFIG
    
    detector = LivenessDetector(LIVENESS_CONFIG)
    cap = cv2.VideoCapture(0)
    
    print("Starting liveness detection... Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        is_live, message, annotated = detector.detect_blinks(frame)
        
        # Display message
        color = (0, 255, 0) if is_live else (0, 0, 255) if is_live == False else (0, 255, 255)
        cv2.putText(annotated, message, (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.imshow("Liveness Detection", annotated)
        
        if is_live is not None:
            print(f"Result: {message}")
            break
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()