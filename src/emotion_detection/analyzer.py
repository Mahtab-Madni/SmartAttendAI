"""
Emotion Analysis Module
Analyzes student emotions and engagement during lectures
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing.image import img_to_array
    KERAS_AVAILABLE = True
    print(f"TensorFlow {tf.__version__} loaded successfully")
except ImportError as e:
    KERAS_AVAILABLE = False
    print(f"Warning: TensorFlow not available ({e}). Emotion analysis will use basic detection.")


class EmotionAnalyzer:
    """
    Analyzes facial emotions to gauge student engagement
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.emotions = config["EMOTIONS"]
        self.model = self._load_emotion_model()
        
        # Load face cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Emotion history for analysis
        self.emotion_history = []
        self.analysis_window = config["ANALYSIS_INTERVAL"]
    
    def _load_emotion_model(self):
        """
        Load pre-trained emotion recognition model
        Model should be trained on FER2013 or similar dataset
        """
        try:
            if KERAS_AVAILABLE:
                model_path = "models/emotion_model.h5"
                # In production, download model from:
                # https://github.com/oarriaga/face_classification
                # Or train your own on FER2013 dataset
                if os.path.exists(model_path):
                    return load_model(model_path)
                else:
                    print(f"Emotion model not found at {model_path}")
                    print("Using fallback emotion detection")
            return None
        except Exception as e:
            print(f"Error loading emotion model: {e}")
            return None
    
    def detect_emotion(self, frame: np.ndarray) -> Tuple[Optional[str], float, np.ndarray]:
        """
        Detect emotion from a face in the frame
        
        Returns:
            Tuple of (emotion_label, confidence, annotated_frame)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) == 0:
            return None, 0.0, frame
        
        # Process first face
        (x, y, w, h) = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        
        if self.model is not None:
            # Use deep learning model
            face_resized = cv2.resize(face_roi, (48, 48))
            face_normalized = face_resized / 255.0
            face_reshaped = face_normalized.reshape(1, 48, 48, 1)
            
            predictions = self.model.predict(face_reshaped, verbose=0)[0]
            emotion_idx = np.argmax(predictions)
            confidence = predictions[emotion_idx]
            emotion = self.emotions[emotion_idx]
        else:
            # Fallback: Simple emotion detection using facial features
            emotion, confidence = self._basic_emotion_detection(face_roi)
        
        # Draw rectangle and label
        color = self._get_emotion_color(emotion)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # Draw label background
        label = f"{emotion}: {confidence:.2f}"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x, y - label_size[1] - 10), 
                     (x + label_size[0], y), color, cv2.FILLED)
        
        # Draw label text
        cv2.putText(frame, label, (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return emotion, confidence, frame
    
    def _basic_emotion_detection(self, face_roi: np.ndarray) -> Tuple[str, float]:
        """
        Basic emotion detection using image features
        This is a simplified fallback when deep learning model is not available
        """
        # Calculate image statistics
        mean_intensity = np.mean(face_roi)
        std_intensity = np.std(face_roi)
        
        # Simple heuristics (not very accurate, but better than nothing)
        if mean_intensity > 140:
            return "happy", 0.6
        elif mean_intensity < 100:
            return "sad", 0.5
        elif std_intensity > 50:
            return "surprise", 0.5
        else:
            return "neutral", 0.7
    
    def _get_emotion_color(self, emotion: str) -> Tuple[int, int, int]:
        """Get color for emotion visualization"""
        emotion_colors = {
            "happy": (0, 255, 0),      # Green
            "sad": (255, 0, 0),        # Blue
            "angry": (0, 0, 255),      # Red
            "surprise": (0, 255, 255), # Yellow
            "fear": (128, 0, 128),     # Purple
            "disgust": (0, 128, 128),  # Teal
            "neutral": (128, 128, 128) # Gray
        }
        return emotion_colors.get(emotion, (255, 255, 255))
    
    def record_emotion(self, emotion: str, confidence: float, student_id: str = None):
        """Record emotion for historical analysis"""
        record = {
            "timestamp": datetime.now(),
            "emotion": emotion,
            "confidence": confidence,
            "student_id": student_id
        }
        self.emotion_history.append(record)
    
    def get_engagement_score(self) -> float:
        """
        Calculate overall engagement score (0-100)
        Based on emotion distribution
        """
        if not self.emotion_history:
            return 0.0
        
        # Define engagement weights
        engagement_weights = {
            "happy": 1.0,
            "neutral": 0.7,
            "surprise": 0.8,
            "sad": 0.3,
            "angry": 0.2,
            "fear": 0.4,
            "disgust": 0.3
        }
        
        total_weight = 0
        for record in self.emotion_history:
            emotion = record["emotion"]
            confidence = record["confidence"]
            weight = engagement_weights.get(emotion, 0.5)
            total_weight += weight * confidence
        
        score = (total_weight / len(self.emotion_history)) * 100
        return min(max(score, 0), 100)


class ClassroomAnalytics:
    """
    Generates analytics reports for classroom engagement
    """
    
    def __init__(self):
        self.session_data = []
        self.start_time = None
    
    def start_session(self, session_name: str = None):
        """Start a new analytics session"""
        self.start_time = datetime.now()
        self.session_data = []
        print(f"Analytics session started: {session_name or 'Unnamed'}")
    
    def log_emotion(self, emotion: str, confidence: float, 
                   timestamp: datetime = None, student_id: str = None):
        """Log an emotion detection event"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.session_data.append({
            "timestamp": timestamp,
            "emotion": emotion,
            "confidence": confidence,
            "student_id": student_id
        })
    
    def generate_report(self) -> Dict:
        """
        Generate comprehensive engagement report
        """
        if not self.session_data:
            return {"error": "No data available"}
        
        # Calculate duration
        duration = datetime.now() - self.start_time
        duration_minutes = duration.total_seconds() / 60
        
        # Emotion distribution
        emotion_counts = defaultdict(int)
        emotion_confidences = defaultdict(list)
        
        for entry in self.session_data:
            emotion = entry["emotion"]
            confidence = entry["confidence"]
            emotion_counts[emotion] += 1
            emotion_confidences[emotion].append(confidence)
        
        # Calculate percentages and average confidence
        total_detections = len(self.session_data)
        emotion_stats = {}
        
        for emotion, count in emotion_counts.items():
            percentage = (count / total_detections) * 100
            avg_confidence = np.mean(emotion_confidences[emotion])
            emotion_stats[emotion] = {
                "count": count,
                "percentage": round(percentage, 2),
                "avg_confidence": round(avg_confidence, 2)
            }
        
        # Time-based analysis (segment by time periods)
        time_segments = self._analyze_time_segments()
        
        # Overall engagement score
        engagement_score = self._calculate_engagement_score(emotion_counts, total_detections)
        
        # Identify problem periods
        problem_periods = self._identify_problem_periods()
        
        report = {
            "session_start": self.start_time.isoformat(),
            "session_end": datetime.now().isoformat(),
            "duration_minutes": round(duration_minutes, 2),
            "total_detections": total_detections,
            "emotion_distribution": emotion_stats,
            "engagement_score": round(engagement_score, 2),
            "time_segments": time_segments,
            "problem_periods": problem_periods,
            "recommendations": self._generate_recommendations(emotion_stats, problem_periods)
        }
        
        return report
    
    def _calculate_engagement_score(self, emotion_counts: Dict, total: int) -> float:
        """Calculate overall class engagement (0-100)"""
        weights = {
            "happy": 1.0,
            "neutral": 0.7,
            "surprise": 0.8,
            "sad": 0.3,
            "angry": 0.2,
            "fear": 0.4,
            "disgust": 0.3
        }
        
        weighted_sum = sum(
            emotion_counts.get(emotion, 0) * weight 
            for emotion, weight in weights.items()
        )
        
        score = (weighted_sum / total) * 100 if total > 0 else 0
        return score
    
    def _analyze_time_segments(self, segment_minutes: int = 15) -> List[Dict]:
        """Analyze emotions by time segments"""
        if not self.session_data:
            return []
        
        segments = []
        segment_duration = timedelta(minutes=segment_minutes)
        current_segment_start = self.start_time
        
        while current_segment_start < datetime.now():
            segment_end = current_segment_start + segment_duration
            
            # Filter data for this segment
            segment_emotions = [
                entry for entry in self.session_data
                if current_segment_start <= entry["timestamp"] < segment_end
            ]
            
            if segment_emotions:
                # Calculate dominant emotion
                emotion_counts = defaultdict(int)
                for entry in segment_emotions:
                    emotion_counts[entry["emotion"]] += 1
                
                dominant_emotion = max(emotion_counts, key=emotion_counts.get)
                
                segments.append({
                    "start_time": current_segment_start.strftime("%H:%M"),
                    "end_time": segment_end.strftime("%H:%M"),
                    "dominant_emotion": dominant_emotion,
                    "detection_count": len(segment_emotions)
                })
            
            current_segment_start = segment_end
        
        return segments
    
    def _identify_problem_periods(self) -> List[Dict]:
        """Identify time periods with low engagement"""
        segments = self._analyze_time_segments(segment_minutes=10)
        
        problem_emotions = {"sad", "angry", "fear", "disgust"}
        problems = []
        
        for segment in segments:
            if segment["dominant_emotion"] in problem_emotions:
                problems.append({
                    "time": f"{segment['start_time']} - {segment['end_time']}",
                    "issue": segment["dominant_emotion"],
                    "severity": "high" if segment["dominant_emotion"] in {"angry", "disgust"} else "medium"
                })
        
        return problems
    
    def _generate_recommendations(self, emotion_stats: Dict, 
                                 problem_periods: List) -> List[str]:
        """Generate actionable recommendations for teachers"""
        recommendations = []
        
        # Check for high boredom/disengagement
        if emotion_stats.get("neutral", {}).get("percentage", 0) > 40:
            recommendations.append(
                "High neutral emotion detected (>40%). Consider adding more interactive elements or examples."
            )
        
        # Check for confusion/fear
        if emotion_stats.get("fear", {}).get("percentage", 0) > 20:
            recommendations.append(
                "Students showing signs of confusion or anxiety. Consider slowing down or reviewing concepts."
            )
        
        # Check for negative emotions
        negative_total = sum(
            emotion_stats.get(emotion, {}).get("percentage", 0)
            for emotion in ["sad", "angry", "disgust"]
        )
        if negative_total > 25:
            recommendations.append(
                f"High negative emotions detected ({negative_total:.1f}%). Check if material is too difficult or presentation style needs adjustment."
            )
        
        # Problem period recommendations
        if len(problem_periods) > 2:
            recommendations.append(
                f"Multiple disengagement periods detected ({len(problem_periods)}). Consider shorter lecture segments with breaks."
            )
        
        # Positive feedback
        if emotion_stats.get("happy", {}).get("percentage", 0) > 30:
            recommendations.append(
                "Good engagement levels! Students are responding positively to the material."
            )
        
        if not recommendations:
            recommendations.append("Overall engagement is balanced. Continue with current teaching approach.")
        
        return recommendations
    
    def export_report(self, filepath: str):
        """Export report to JSON file"""
        report = self.generate_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report exported to {filepath}")


if __name__ == "__main__":
    import os
    from config.settings import EMOTION_CONFIG
    
    # Initialize analyzer
    analyzer = EmotionAnalyzer(EMOTION_CONFIG)
    analytics = ClassroomAnalytics()
    analytics.start_session("Test Lecture")
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    print("Starting emotion analysis... Press 'q' to quit and generate report")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect emotion every 30 frames (~1 second)
        if frame_count % 30 == 0:
            emotion, confidence, annotated = analyzer.detect_emotion(frame)
            
            if emotion:
                print(f"Detected: {emotion} ({confidence:.2f})")
                analytics.log_emotion(emotion, confidence)
        else:
            annotated = frame
        
        cv2.imshow("Emotion Analysis", annotated)
        frame_count += 1
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Generate and display report
    print("\n" + "="*50)
    print("ENGAGEMENT REPORT")
    print("="*50)
    
    report = analytics.generate_report()
    print(json.dumps(report, indent=2))
    
    # Export report
    analytics.export_report("data/logs/emotion_report.json")