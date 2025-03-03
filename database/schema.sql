-- User table to store basic information
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    resume_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interview sessions table
CREATE TABLE IF NOT EXISTS interview_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- MCQ scores table
CREATE TABLE IF NOT EXISTS mcq_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    round_type TEXT NOT NULL,  -- 'aptitude' or 'technical'
    category TEXT NOT NULL,
    total_questions INTEGER,
    correct_answers INTEGER,
    score FLOAT,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
);

-- Behavioral metrics table
CREATE TABLE IF NOT EXISTS behavioral_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    round_type TEXT NOT NULL,  -- 'introduction' or 'hr'
    confidence_score FLOAT,
    nervousness_score FLOAT,
    clarity_score FLOAT,
    engagement_score FLOAT,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
);

-- Proctoring incidents table
CREATE TABLE IF NOT EXISTS proctoring_incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    timestamp TIMESTAMP,
    incident_type TEXT NOT NULL,  -- 'eye_distraction', 'phone_detected', etc.
    confidence_score FLOAT,
    details TEXT,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
);

-- Detailed question responses
CREATE TABLE IF NOT EXISTS question_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    round_type TEXT NOT NULL,
    question_number INTEGER,
    question_text TEXT,
    user_answer TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    category TEXT,
    response_time FLOAT,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
);

-- Speech analysis metrics
CREATE TABLE IF NOT EXISTS speech_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    question_number INTEGER,
    round_type TEXT NOT NULL,
    emotion TEXT,
    confidence_level FLOAT,
    speech_rate FLOAT,
    clarity_score FLOAT,
    volume_variation FLOAT,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
); 