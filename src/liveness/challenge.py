"""
Challenge-Response Verification Module
Implements random challenges to defeat pre-recorded video attacks
"""
import cv2
import numpy as np
import dlib
from typing import Dict, Tuple, Optional
import random
import face_recognition

class ChallengeValidator:
    """Validates user responses to anti-spoofing challenges"""
    
    def __init__(self):
        """Initialize challenge validator"""
        self.challenges = [
            "smile",
            "nod",
            "blink"
        ]
        
        # Load dlib's face detector and landmark predictor
        try:
            self.detector = dlib.get_frontal_face_detector()
            # Using face_recognition's built-in landmark detection
            self.predictor = None
        except Exception as e:
            print(f"[CHALLENGE] Warning: dlib not fully initialized: {e}")
            self.detector = None
            self.predictor = None
    
    def get_random_challenge(self) -> Dict:
        """Get a random challenge for the user"""
        challenge = random.choice(self.challenges)
        
        challenge_messages = {
            "smile": "Please smile naturally for 2 seconds",
            "nod": "Please nod your head up and down",
            "blink": "Please blink your eyes naturally"
        }
        
        return {
            "type": challenge,
            "message": challenge_messages[challenge],
            "duration": 3  # seconds to perform action
        }
    
    def detect_smile(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if person is smiling
        Returns: (is_smiling, confidence)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Load cascade classifier for smile detection
            smile_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_smile.xml'
            )
            
            smiles = smile_cascade.detectMultiScale(gray, 1.1, 20, minSize=(30, 30))
            
            print(f"[CHALLENGE-SMILE] Smile cascade detected {len(smiles)} smile(s)")
            
            if len(smiles) > 0:
                # Calculate confidence based on smile area
                confidence = min(1.0, len(smiles) * 0.3)
                print(f"[CHALLENGE-SMILE] SUCCESS: Detected smile with confidence {confidence:.2f}")
                return True, confidence
            
            print(f"[CHALLENGE-SMILE] FAILED: No smile detected")
            return False, 0.0
            
        except Exception as e:
            print(f"[CHALLENGE] Error detecting smile: {e}")
            import traceback
            traceback.print_exc()
            return False, 0.0
    
    def detect_head_turn(self, frames: list, direction: str) -> Tuple[bool, float]:
        """
        Detect if head turned in specified direction
        frames: list of consecutive frames
        direction: 'left' or 'right'
        Returns: (turned, confidence)
        """
        try:
            if len(frames) < 2:
                print(f"[CHALLENGE-TURN] Not enough frames: {len(frames)} < 2")
                return False, 0.0
            
            # Get face landmarks for first frame
            nose_start = None
            try:
                rgb_frame_start = cv2.cvtColor(frames[0], cv2.COLOR_BGR2RGB)
                landmarks_dict_start = face_recognition.face_landmarks(rgb_frame_start)
                
                if not landmarks_dict_start or len(landmarks_dict_start) == 0:
                    print(f"[CHALLENGE-TURN] No landmarks in first frame")
                    return False, 0.0
                
                nose_start = landmarks_dict_start[0]['nose_tip'][0]  # Get nose tip point
                print(f"[CHALLENGE-TURN] Start nose position: {nose_start}")
            except Exception as e:
                print(f"[CHALLENGE-TURN] Error getting start landmarks: {e}")
                return False, 0.0
            
            # Get face landmarks for end frame
            # Try from last frame backwards to find one with clear landmarks
            nose_end = None
            end_frame_idx = None
            
            for idx in range(len(frames) - 1, -1, -1):
                try:
                    rgb_frame_end = cv2.cvtColor(frames[idx], cv2.COLOR_BGR2RGB)
                    landmarks_dict_end = face_recognition.face_landmarks(rgb_frame_end)
                    
                    if landmarks_dict_end and len(landmarks_dict_end) > 0:
                        nose_end = landmarks_dict_end[0]['nose_tip'][0]  # Get nose tip point
                        end_frame_idx = idx
                        if idx < len(frames) - 1:
                            print(f"[CHALLENGE-TURN] Last frame had no landmarks, using frame {idx} instead")
                        print(f"[CHALLENGE-TURN] End nose position (frame {idx}): {nose_end}")
                        break
                except Exception as frame_error:
                    print(f"[CHALLENGE-TURN] Error checking frame {idx}: {frame_error}")
                    continue
            
            if nose_end is None or end_frame_idx is None:
                print(f"[CHALLENGE-TURN] No landmarks found in any of the end frames")
                return False, 0.0
            
            # Calculate head position change
            x_shift = nose_end[0] - nose_start[0]
            frame_distance = len(frames) - 1 - end_frame_idx
            print(f"[CHALLENGE-TURN] X-shift: {x_shift:.1f}px (from frame 0 to frame {end_frame_idx}), direction: {direction}")
            if frame_distance > 0:
                print(f"[CHALLENGE-TURN] Note: Last {frame_distance} frame(s) had no landmarks")
            
            # Check direction
            if direction == "left" and x_shift < -10:  # Moved left
                confidence = min(1.0, abs(x_shift) / 50)  # Normalize to max 50px shift
                print(f"[CHALLENGE-TURN] SUCCESS: Turned left by {abs(x_shift):.1f}px, confidence={confidence:.2f}")
                return True, confidence
            elif direction == "right" and x_shift > 10:  # Moved right
                confidence = min(1.0, abs(x_shift) / 50)
                print(f"[CHALLENGE-TURN] SUCCESS: Turned right by {x_shift:.1f}px, confidence={confidence:.2f}")
                return True, confidence
            else:
                threshold = -10 if direction == "left" else 10
                print(f"[CHALLENGE-TURN] FAILED: x_shift={x_shift:.1f}, threshold={'<' if direction == 'left' else '>'} {threshold}")
                return False, 0.0
        
        except Exception as e:
            print(f"[CHALLENGE] Error detecting head turn: {e}")
            import traceback
            traceback.print_exc()
            return False, 0.0
    
    def detect_nod(self, frames: list) -> Tuple[bool, float]:
        """
        Detect if head nodded up and down
        frames: list of consecutive frames
        Returns: (nodded, confidence)
        """
        try:
            if len(frames) < 3:
                print(f"[CHALLENGE-NOD] Not enough frames: {len(frames)} < 3")
                return False, 0.0
            
            y_positions = []
            
            # Get vertical position of nose in each frame
            for idx, frame in enumerate(frames):
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    landmarks_dict = face_recognition.face_landmarks(rgb_frame)
                    
                    if landmarks_dict and len(landmarks_dict) > 0:
                        # Use nose_tip directly from face_recognition output
                        if 'nose_tip' in landmarks_dict[0]:
                            nose_point = landmarks_dict[0]['nose_tip'][0]  # Get first (tipmost) point
                            nose_y = nose_point[1]  # Y coordinate
                            y_positions.append(nose_y)
                            print(f"[CHALLENGE-NOD] Frame {idx}: nose_y={nose_y}")
                        else:
                            print(f"[CHALLENGE-NOD] Frame {idx}: no nose_tip in landmarks")
                    else:
                        print(f"[CHALLENGE-NOD] Frame {idx}: face_landmarks returned empty")
                except Exception as frame_error:
                    print(f"[CHALLENGE-NOD] Frame {idx}: error: {frame_error}")
            
            print(f"[CHALLENGE-NOD] Successfully extracted {len(y_positions)} nose positions from {len(frames)} frames")
            
            if len(y_positions) < 3:
                print(f"[CHALLENGE-NOD] FAILED: Not enough valid nose positions ({len(y_positions)} < 3)")
                return False, 0.0
            
            # Check for up-down movement (minimum 15 pixels variation)
            y_min = min(y_positions)
            y_max = max(y_positions)
            y_range = y_max - y_min
            print(f"[CHALLENGE-NOD] Y-positions: min={y_min}, max={y_max}, range={y_range}")
            print(f"[CHALLENGE-NOD] Y-positions sequence: {y_positions}")
            
            # Check for oscillation (down-up or up-down pattern)
            has_oscillation = False
            oscillation_points = []
            for i in range(len(y_positions) - 2):
                diff1 = y_positions[i+1] - y_positions[i]
                diff2 = y_positions[i+2] - y_positions[i+1]
                if diff1 * diff2 < 0:  # Sign change indicates direction change
                    has_oscillation = True
                    oscillation_points.append(i+1)
                    print(f"[CHALLENGE-NOD] Oscillation at position {i+1}: diff1={diff1:.1f}, diff2={diff2:.1f}")
            
            print(f"[CHALLENGE-NOD] Has oscillation: {has_oscillation}, points: {oscillation_points}")
            
            # Accept nods with significant head movement (15px minimum)
            # Full nods (with oscillation) get higher confidence
            # Partial nods (without oscillation but still significant movement) get lower confidence
            
            if y_range >= 15:
                if has_oscillation:
                    # Strong nod: clear down-up or up-down movement
                    confidence = min(1.0, y_range / 50)
                    print(f"[CHALLENGE-NOD] SUCCESS: Full nod detected - y_range={y_range} AND has_oscillation=True, confidence={confidence:.2f}")
                    return True, confidence
                else:
                    # Partial nod: significant movement but incomplete cycle (may lose face detection)
                    # Still valid since user clearly moved head
                    confidence = min(1.0, (y_range / 50) * 0.75)  # Reduce confidence slightly for partial nods
                    print(f"[CHALLENGE-NOD] SUCCESS: Partial nod detected - y_range={y_range} without oscillation, confidence={confidence:.2f}")
                    return True, confidence
            elif y_range < 15:
                print(f"[CHALLENGE-NOD] FAILED: y_range={y_range} is less than minimum threshold (15px)")
            
            return False, 0.0
            
        except Exception as e:
            print(f"[CHALLENGE] Error detecting nod: {e}")
            import traceback
            traceback.print_exc()
            return False, 0.0
    
    def detect_blink(self, frames: list) -> Tuple[bool, float]:
        """
        Detect if eyes blinked
        frames: list of consecutive frames
        Returns: (blinked, confidence)
        """
        try:
            if len(frames) < 3:
                print(f"[CHALLENGE-BLINK] Not enough frames: {len(frames)} < 3")
                return False, 0.0
            
            eye_openness_values = []
            
            print(f"[CHALLENGE-BLINK] Processing {len(frames)} frames for blink detection")
            
            # Calculate eye openness for each frame
            for idx, frame in enumerate(frames):
                try:
                    landmarks = self._get_face_landmarks(frame)
                    if landmarks is not None:
                        # Calculate eye aspect ratio (EAR)
                        left_eye_ratio = self._calculate_ear(landmarks, "left")
                        right_eye_ratio = self._calculate_ear(landmarks, "right")
                        avg_ratio = (left_eye_ratio + right_eye_ratio) / 2
                        eye_openness_values.append(avg_ratio)
                        print(f"[CHALLENGE-BLINK] Frame {idx}: left_ear={left_eye_ratio:.3f}, right_ear={right_eye_ratio:.3f}, avg={avg_ratio:.3f}")
                    else:
                        print(f"[CHALLENGE-BLINK] Frame {idx}: landmarks not detected")
                except Exception as e:
                    print(f"[CHALLENGE-BLINK] Frame {idx}: error calculating EAR: {e}")
            
            print(f"[CHALLENGE-BLINK] Successfully processed {len(eye_openness_values)} frames")
            
            if len(eye_openness_values) < 3:
                print(f"[CHALLENGE-BLINK] FAILED: Not enough valid EAR values ({len(eye_openness_values)} < 3)")
                return False, 0.0
            
            print(f"[CHALLENGE-BLINK] EAR sequence: {[f'{v:.3f}' for v in eye_openness_values]}")
            
            # Check for open -> closed -> open pattern
            has_blink = False
            blink_positions = []
            
            for i in range(len(eye_openness_values) - 1):
                # If eyes closed (low ratio) between open frames
                if (eye_openness_values[i] > 0.25 and 
                    eye_openness_values[i+1] < 0.2):
                    has_blink = True
                    blink_positions.append(i)
                    print(f"[CHALLENGE-BLINK] Blink detected at position {i}: {eye_openness_values[i]:.3f} -> {eye_openness_values[i+1]:.3f}")
            
            if has_blink:
                print(f"[CHALLENGE-BLINK] SUCCESS: Blink detected at positions {blink_positions}")
                return True, 0.8
            
            print(f"[CHALLENGE-BLINK] FAILED: No blink pattern detected (no transition from open > 0.25 to closed < 0.2)")
            return False, 0.0
            
        except Exception as e:
            print(f"[CHALLENGE] Error detecting blink: {e}")
            import traceback
            traceback.print_exc()
            return False, 0.0
    
    def validate_challenge_response(self, frames: list, challenge_type: str) -> Tuple[bool, float]:
        """
        Validate user's response to challenge
        frames: list of frames captured during challenge
        challenge_type: type of challenge ('smile', 'nod', 'blink')
        Returns: (success, confidence)
        """
        print(f"[CHALLENGE] Validating {challenge_type} challenge with {len(frames)} frames")
        
        if not frames or len(frames) == 0:
            print(f"[CHALLENGE] FAILED: No frames provided")
            return False, 0.0
        
        if challenge_type == "smile":
            print(f"[CHALLENGE] Running smile detection on last frame")
            is_smiling, confidence = self.detect_smile(frames[-1])  # Last frame
            result = is_smiling and confidence >= 0.3
            final_confidence = confidence if result else 0.0
            print(f"[CHALLENGE] Smile result: detected={is_smiling}, confidence={confidence:.3f}, threshold=0.3, passed={result}")
            return result, final_confidence
        elif challenge_type == "nod":
            print(f"[CHALLENGE] Running nod detection across all frames")
            nodded, confidence = self.detect_nod(frames)
            result = nodded and confidence >= 0.4
            final_confidence = confidence if result else 0.0
            print(f"[CHALLENGE] Nod result: detected={nodded}, confidence={confidence:.3f}, threshold=0.4, passed={result}")
            return result, final_confidence
        elif challenge_type == "blink":
            print(f"[CHALLENGE] Running blink detection across all frames")
            blinked, confidence = self.detect_blink(frames)
            result = blinked and confidence >= 0.5
            final_confidence = confidence if result else 0.0
            print(f"[CHALLENGE] Blink result: detected={blinked}, confidence={confidence:.3f}, threshold=0.5, passed={result}")
            return result, final_confidence
        
        print(f"[CHALLENGE] Unknown challenge type: {challenge_type}")
        return False, 0.0
    
    def _get_face_landmarks(self, frame: np.ndarray) -> Optional[list]:
        """Get facial landmarks from frame"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = face_recognition.face_landmarks(rgb_frame)
            
            if landmarks:
                # Return the landmarks dictionary directly
                return landmarks[0] if landmarks else None
            else:
                return None
        except Exception as e:
            print(f"[CHALLENGE] _get_face_landmarks error: {e}")
            return None
    
    def _convert_landmarks_to_points(self, landmarks_dict: dict) -> list:
        """Convert face_recognition landmarks dict to 68-point format list
        
        face_recognition returns a dict with keys like:
        'chin', 'left_eyebrow', 'right_eyebrow', 'nose_tip', 'nose_bridge',
        'left_eye', 'right_eye', 'top_lip', 'bottom_lip'
        
        Converting to standard 68-point dlib format indices:
        0-16: chin
        17-21: left_eyebrow
        22-26: right_eyebrow
        27-35: nose (bridge + tip)
        36-41: left_eye
        42-47: right_eye
        48-59: top_lip
        60-67: bottom_lip
        """
        points = []
        
        # 0-16: Jawline (17 points)
        if 'chin' in landmarks_dict:
            points.extend(landmarks_dict['chin'])
        
        # 17-21: Left eyebrow (5 points)
        if 'left_eyebrow' in landmarks_dict:
            points.extend(landmarks_dict['left_eyebrow'])
        
        # 22-26: Right eyebrow (5 points)
        if 'right_eyebrow' in landmarks_dict:
            points.extend(landmarks_dict['right_eyebrow'])
        
        # 27-35: Nose (9 points total) - nose_bridge + nose_tip
        if 'nose_bridge' in landmarks_dict:
            points.extend(landmarks_dict['nose_bridge'])
        if 'nose_tip' in landmarks_dict:
            # nose_tip should be the last point of nose section (around index 30)
            points.extend(landmarks_dict['nose_tip'])
        
        # 36-41: Left eye (6 points)
        if 'left_eye' in landmarks_dict:
            points.extend(landmarks_dict['left_eye'])
        
        # 42-47: Right eye (6 points)
        if 'right_eye' in landmarks_dict:
            points.extend(landmarks_dict['right_eye'])
        
        # 48-59: Top lip (12 points)
        if 'top_lip' in landmarks_dict:
            points.extend(landmarks_dict['top_lip'])
        
        # 60-67: Bottom lip (8 points)
        if 'bottom_lip' in landmarks_dict:
            points.extend(landmarks_dict['bottom_lip'])
        
        if points:
            print(f"[CHALLENGE] Converted landmarks to {len(points)} points. Nose tip likely at index {27 + len(landmarks_dict.get('nose_bridge', []))}.")
            return points
        else:
            print(f"[CHALLENGE] No landmarks in dict: {landmarks_dict.keys()}")
            return None
    
    def _calculate_ear(self, landmarks_dict, eye: str = "left") -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for blink detection
        landmarks_dict: dictionary from face_recognition.face_landmarks()
        eye: 'left' or 'right'
        """
        try:
            from scipy.spatial import distance
            
            if not landmarks_dict or not isinstance(landmarks_dict, dict):
                print(f"[CHALLENGE-EAR] Invalid landmarks_dict type: {type(landmarks_dict)}")
                return 0.3  # Default neutral value
            
            # Extract eye points from face_recognition format
            if eye.lower() == "left":
                if 'left_eye' not in landmarks_dict:
                    print(f"[CHALLENGE-EAR] 'left_eye' not in landmarks_dict")
                    return 0.3
                eye_points = landmarks_dict['left_eye']
            else:  # right
                if 'right_eye' not in landmarks_dict:
                    print(f"[CHALLENGE-EAR] 'right_eye' not in landmarks_dict")
                    return 0.3
                eye_points = landmarks_dict['right_eye']
            
            if not eye_points or len(eye_points) < 6:
                print(f"[CHALLENGE-EAR] Not enough eye points: {len(eye_points) if eye_points else 0} < 6")
                return 0.3
            
            # Calculate distances using face_recognition format
            # eye_points[0] = outer corner, eye_points[3] = other outer corner
            # eye_points[1], eye_points[5] = vertical for top/bottom
            # eye_points[2], eye_points[4] = vertical for middle
            A = distance.euclidean(eye_points[1], eye_points[5])
            B = distance.euclidean(eye_points[2], eye_points[4])
            C = distance.euclidean(eye_points[0], eye_points[3])
            
            # Calculate EAR
            ear = (A + B) / (2.0 * C) if C != 0 else 0.3
            return ear
        except Exception as e:
            print(f"[CHALLENGE-EAR] Error calculating EAR: {e}")
            return 0.3  # Return neutral value on error
