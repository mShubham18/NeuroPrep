import librosa
import numpy as np
from transformers import pipeline
import speech_recognition as sr
import sqlite3
from datetime import datetime

class SpeechAnalyzer:
    def __init__(self, session_id):
        self.session_id = session_id
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
        self.recognizer = sr.Recognizer()
        
    def analyze_response(self, audio_data, question_number, round_type):
        """Analyze speech response for various metrics"""
        try:
            # Convert audio to text
            text = self._speech_to_text(audio_data)
            
            # Analyze various aspects
            emotions = self._analyze_emotion(text)
            speech_metrics = self._analyze_speech_metrics(audio_data)
            
            # Combine metrics
            metrics = {
                'emotion': emotions['dominant_emotion'],
                'confidence_level': emotions['confidence'],
                'speech_rate': speech_metrics['speech_rate'],
                'clarity_score': speech_metrics['clarity'],
                'volume_variation': speech_metrics['volume_variation']
            }
            
            # Store in database
            self._store_metrics(metrics, question_number, round_type)
            
            return metrics
            
        except Exception as e:
            print(f"Error analyzing speech: {str(e)}")
            return None
    
    def _speech_to_text(self, audio_data):
        """Convert speech to text"""
        try:
            with sr.AudioFile(audio_data) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                return text
        except Exception as e:
            print(f"Error in speech to text: {str(e)}")
            return ""
    
    def _analyze_emotion(self, text):
        """Analyze emotion in text"""
        if not text:
            return {'dominant_emotion': 'unknown', 'confidence': 0.0}
        
        # Get emotion predictions
        emotions = self.emotion_classifier(text)[0]
        
        # Find dominant emotion
        dominant = max(emotions, key=lambda x: x['score'])
        
        return {
            'dominant_emotion': dominant['label'],
            'confidence': dominant['score'],
            'all_emotions': emotions
        }
    
    def _analyze_speech_metrics(self, audio_data):
        """Analyze speech metrics like rate, clarity, etc."""
        try:
            # Load audio
            y, sr = librosa.load(audio_data)
            
            # Calculate speech rate (syllables per second)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
            speech_rate = tempo / 60  # Convert BPM to syllables per second
            
            # Calculate clarity (using spectral centroid)
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)
            clarity_score = np.mean(spec_cent) / 1000  # Normalize
            
            # Calculate volume variation
            rms = librosa.feature.rms(y=y)[0]
            volume_variation = np.std(rms)
            
            return {
                'speech_rate': float(speech_rate),
                'clarity': float(clarity_score),
                'volume_variation': float(volume_variation)
            }
            
        except Exception as e:
            print(f"Error analyzing speech metrics: {str(e)}")
            return {
                'speech_rate': 0.0,
                'clarity': 0.0,
                'volume_variation': 0.0
            }
    
    def _store_metrics(self, metrics, question_number, round_type):
        """Store speech metrics in database"""
        conn = sqlite3.connect('interview.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO speech_metrics 
            (session_id, question_number, round_type, emotion, confidence_level, 
             speech_rate, clarity_score, volume_variation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.session_id,
            question_number,
            round_type,
            metrics['emotion'],
            metrics['confidence_level'],
            metrics['speech_rate'],
            metrics['clarity_score'],
            metrics['volume_variation']
        ))
        
        conn.commit()
        conn.close()
    
    def get_speech_summary(self):
        """Get summary of speech metrics for the session"""
        conn = sqlite3.connect('interview.db')
        cursor = conn.cursor()
        
        # Get average metrics
        cursor.execute("""
            SELECT 
                round_type,
                AVG(confidence_level) as avg_confidence,
                AVG(speech_rate) as avg_speech_rate,
                AVG(clarity_score) as avg_clarity,
                AVG(volume_variation) as avg_volume_var
            FROM speech_metrics
            WHERE session_id = ?
            GROUP BY round_type
        """, (self.session_id,))
        
        metrics = cursor.fetchall()
        
        # Get emotion distribution
        cursor.execute("""
            SELECT emotion, COUNT(*) as count
            FROM speech_metrics
            WHERE session_id = ?
            GROUP BY emotion
        """, (self.session_id,))
        
        emotions = cursor.fetchall()
        
        conn.close()
        
        return {
            'metrics_by_round': [{
                'round': m[0],
                'avg_confidence': m[1],
                'avg_speech_rate': m[2],
                'avg_clarity': m[3],
                'avg_volume_variation': m[4]
            } for m in metrics],
            'emotion_distribution': [{
                'emotion': e[0],
                'count': e[1]
            } for e in emotions]
        } 