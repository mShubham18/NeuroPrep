import cv2
import mediapipe as mp
import numpy as np
import torch
from datetime import datetime
import sqlite3
from threading import Thread
import time
from utils import TryExcept

class ProctorService:
    def __init__(self, session_id):
        self.session_id = session_id
        self.cap = None
        self.is_monitoring = False
        self.incident_count = 0
        
        # Initialize MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Load YOLOv5 model for phone detection
        with TryExcept('Error loading YOLOv5 model'):
            try:
                import yolov5
                self.phone_detector = yolov5.load('yolov5s')
                self.phone_detector.classes = [67]  # Class index for cell phones
            except ImportError:
                print("YOLOv5 not installed. Phone detection will be disabled.")
                self.phone_detector = None
        
        # Initialize eye tracking parameters
        self.eye_threshold = 0.3
        self.distraction_threshold = 2.0  # seconds
        self.last_focused_time = time.time()
        
    def start_monitoring(self):
        """Start webcam monitoring in a separate thread"""
        self.cap = cv2.VideoCapture(0)
        self.is_monitoring = True
        Thread(target=self._monitor_loop).start()
    
    def stop_monitoring(self):
        """Stop webcam monitoring"""
        self.is_monitoring = False
        if self.cap:
            self.cap.release()
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Process frame for various checks
            self._check_eye_gaze(frame)
            if self.phone_detector is not None:
                self._detect_phone(frame)
            
            time.sleep(0.1)  # Reduce CPU usage
    
    def _check_eye_gaze(self, frame):
        """Check eye gaze direction and detect distractions"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Get eye landmarks
            left_eye = self._get_eye_aspect_ratio(face_landmarks, "left")
            right_eye = self._get_eye_aspect_ratio(face_landmarks, "right")
            
            # Check if looking away
            if left_eye < self.eye_threshold or right_eye < self.eye_threshold:
                current_time = time.time()
                if current_time - self.last_focused_time > self.distraction_threshold:
                    self._log_incident("eye_distraction", 0.8, "User looking away from screen")
            else:
                self.last_focused_time = time.time()
    
    def _detect_phone(self, frame):
        """Detect phones or other devices in frame"""
        if self.phone_detector is None:
            return
            
        results = self.phone_detector(frame)
        
        # Check if any phones detected
        if len(results.pred[0]) > 0:
            for *box, conf, cls in results.pred[0]:
                if cls == 67 and conf > 0.5:  # Phone detected with high confidence
                    self._log_incident("phone_detected", float(conf), "Phone detected in frame")
    
    def _get_eye_aspect_ratio(self, landmarks, eye_side):
        """Calculate eye aspect ratio to detect eye closure/gaze"""
        if eye_side == "left":
            points = [33, 160, 158, 133, 153, 144]
        else:
            points = [362, 385, 387, 263, 373, 380]
        
        coords = [(landmarks.landmark[point].x, landmarks.landmark[point].y) 
                 for point in points]
        
        # Calculate vertical distances
        v1 = np.linalg.norm(np.array(coords[1]) - np.array(coords[5]))
        v2 = np.linalg.norm(np.array(coords[2]) - np.array(coords[4]))
        
        # Calculate horizontal distance
        h = np.linalg.norm(np.array(coords[0]) - np.array(coords[3]))
        
        # Calculate aspect ratio
        return (v1 + v2) / (2.0 * h)
    
    def _log_incident(self, incident_type, confidence, details):
        """Log proctoring incidents to database"""
        self.incident_count += 1
        
        conn = sqlite3.connect('interview.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO proctoring_incidents 
            (session_id, timestamp, incident_type, confidence_score, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.session_id,
            datetime.now(),
            incident_type,
            confidence,
            details
        ))
        
        conn.commit()
        conn.close()
    
    def get_incident_summary(self):
        """Get summary of incidents for the session"""
        conn = sqlite3.connect('interview.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT incident_type, COUNT(*) as count, AVG(confidence_score) as avg_confidence
            FROM proctoring_incidents
            WHERE session_id = ?
            GROUP BY incident_type
        """, (self.session_id,))
        
        summary = cursor.fetchall()
        conn.close()
        
        return {
            'total_incidents': self.incident_count,
            'incident_breakdown': [{
                'type': incident[0],
                'count': incident[1],
                'avg_confidence': incident[2]
            } for incident in summary]
        } 