import os
import datetime
import openai
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from pipelines.question_generation_pipeline import question_generation_pipeline
from components.voice_chat import VoiceChat
from werkzeug.utils import secure_filename
from services.proctor_service import ProctorService
from services.speech_analysis import SpeechAnalyzer
import uuid
import sqlite3

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Add secret key for session management
socketio = SocketIO(app)

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize APIs and services
openai.api_key = OPENAI_API_KEY
voice_chat = VoiceChat()
proctor_service = None  # Will be initialized per session
speech_analyzer = None  # Will be initialized per session

# Global Variable (Initializes only when accessed)
INTERVIEW_QUESTIONS = {}

# Function to check if questions are loaded
def questions_are_loaded():
    return bool(INTERVIEW_QUESTIONS)

# Decorator to check if questions are loaded
def require_questions(f):
    def decorated_function(*args, **kwargs):
        if not questions_are_loaded():
            return redirect(url_for('upload'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.before_request
def initialize_session():
    global proctor_service, speech_analyzer
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    if proctor_service is None:
        proctor_service = ProctorService(session_id=session['user_id'])
    if speech_analyzer is None:
        speech_analyzer = SpeechAnalyzer(session_id=session['user_id'])

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/process-resume", methods=["POST"])
def process_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({
                "success": False,
                "error": "No resume file uploaded"
            })
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            })
        
        if file and allowed_file(file.filename):
            # Save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Store the file path in session
            session['resume_path'] = file_path
            
            return jsonify({
                "success": True,
                "redirect": "/preparing"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Invalid file type. Please upload PDF, DOC, or DOCX files only."
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/preparing")
def preparing():
    return render_template("preparing.html")

@app.route("/generate-questions")
def generate_questions():
    try:
        resume_path = session.get('resume_path')
        if not resume_path:
            return jsonify({
                "success": False,
                "error": "No resume found"
            })

        # Generate questions
        intro, apt, tech, code, hr = question_generation_pipeline(resume_path)
        
        # Store questions in global variable
        global INTERVIEW_QUESTIONS
        INTERVIEW_QUESTIONS = {
            "introduction": intro,
            "aptitude": apt,
            "technical": tech,
            "coding": code,
            "hr": hr
        }
        
        # Set introduction questions for voice chat
        voice_chat.set_questions(intro)
        
        return jsonify({
            "success": True,
            "redirect": "/introduction"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/introduction")
@require_questions
def introduction_instructions():
    return render_template("introduction_instructions.html")

@app.route("/introduction-test")
@require_questions
def introduction_test():
    return render_template("introduction.html")

@app.route("/aptitude")
@require_questions
def aptitude_instructions():
    return render_template("aptitude_instructions.html")

@app.route("/aptitude-test")
@require_questions
def aptitude_test():
    return render_template("aptitude.html")

@app.route("/technical")
@require_questions
def technical_instructions():
    return render_template("technical_instructions.html")

@app.route("/technical-test")
@require_questions
def technical_test():
    return render_template("technical.html")

@app.route("/coding")
@require_questions
def coding_instructions():
    return render_template("coding_instructions.html")

@app.route("/coding-test")
@require_questions
def coding_test():
    return render_template("coding.html")

@app.route("/hr")
@require_questions
def hr_instructions():
    return render_template("hr_instructions.html")

@app.route("/hr-test")
@require_questions
def hr_test():
    return render_template("hr.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

# Add this near the top of your file with other configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route("/start-interview", methods=["POST"])
def start_interview():
    try:
        round_type = request.json.get("round", "introduction")
        print(f"Starting interview round: {round_type}")  # Debug log
        
        if round_type == "introduction":
            voice_chat.set_questions(INTERVIEW_QUESTIONS["introduction"])
        elif round_type == "hr":
            voice_chat.set_questions(INTERVIEW_QUESTIONS["hr"])
        
        first_question = voice_chat.get_next_question()
        print(f"First question: {first_question}")  # Debug log
        
        return jsonify({
            "success": True,
            "question": first_question
        })
    except Exception as e:
        print(f"Error starting interview: {str(e)}")  # Debug log
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/process-response", methods=["POST"])
def process_response():
    try:
        text_response = request.json.get("response", "")
        print(f"Received response: {text_response}")  # Debug log
        
        if not text_response:
            print("Empty response received")
            return jsonify({
                "success": False,
                "error": "Empty response"
            })

        result = voice_chat.process_response(text_response)
        print(f"Processing result: {result}")  # Debug log
        return result
    except Exception as e:
        print(f"Error processing response: {str(e)}")  # Debug log
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/get-aptitude-questions")
@require_questions
def get_aptitude_questions():
    try:
        aptitude_questions = INTERVIEW_QUESTIONS.get("aptitude", {})
        formatted_questions = []
        
        for question, (options_str, answer) in aptitude_questions.items():
            options = [opt.strip() for opt in options_str.split(",")]
            formatted_questions.append({
                "question": question,
                "options": options,
                "correct_answer": answer
            })
        
        return jsonify({
            "success": True,
            "questions": formatted_questions
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/get-technical-questions")
def get_technical_questions():
    try:
        technical_questions = INTERVIEW_QUESTIONS["technical"]
        
        # Format questions for the frontend
        formatted_questions = []
        for question, data in technical_questions.items():
            options = [opt.strip() for opt in data[0].split(",")]  # Split options string into list
            correct_answer = data[1]  # Get the correct answer
            formatted_questions.append({
                "question": question,
                "options": options,  # List of options
                "type": "mcq",
                "category": "technical",
                "correct_answer": correct_answer,  # Include correct answer
                "hints": [],  # No hints in the current format
                "test_cases": None  # No test cases for MCQs
            })
        
        return jsonify({
            "success": True,
            "questions": formatted_questions
        })
    except Exception as e:
        print(f"Error getting technical questions: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to load technical questions"
        })

@app.route("/submit-aptitude", methods=["POST"])
@require_questions
def submit_aptitude():
    try:
        answers = request.json.get("answers", [])
        # Here you can process and store the answers
        
        return jsonify({
            "success": True,
            "next_round_url": "/technical"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/submit-technical", methods=["POST"])
def submit_technical():
    try:
        answers = request.json.get("answers", [])
        
        # Get technical questions and initialize scoring
        technical_questions = INTERVIEW_QUESTIONS["technical"]
        questions_list = list(technical_questions.items())
        total_questions = len(technical_questions)
        
        # Initialize metrics
        metrics = {
            'system_design': {'correct': 0, 'total': 0},
            'operating_systems': {'correct': 0, 'total': 0},
            'databases': {'correct': 0, 'total': 0},
            'networking': {'correct': 0, 'total': 0},
            'data_structures': {'correct': 0, 'total': 0},
            'algorithms': {'correct': 0, 'total': 0}
        }
        
        question_results = []
        correct_answers = 0
        
        # Validate each answer and calculate metrics
        for i, answer in enumerate(answers):
            if i < len(questions_list):
                question_data = questions_list[i]
                question_text = question_data[0]
                correct_answer = question_data[1][1]
                
                # Determine question category based on content
                category = determine_technical_category(question_text)
                metrics[category]['total'] += 1
                
                # Check if answer is correct
                is_correct = str(answer) == str(correct_answer)
                if is_correct:
                    correct_answers += 1
                    metrics[category]['correct'] += 1
                
                # Store detailed result
                result = {
                    "question_number": i + 1,
                    "question_text": question_text,
                    "user_answer": answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "category": category,
                    "feedback": "Correct!" if is_correct else f"Incorrect. The correct answer was: {correct_answer}"
                }
                question_results.append(result)
        
        # Calculate scores
        overall_score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        category_scores = {}
        for category, data in metrics.items():
            if data['total'] > 0:
                category_scores[category] = (data['correct'] / data['total']) * 100
            else:
                category_scores[category] = 0
        
        # Store comprehensive results in session
        session['technical_score'] = {
            'overall_score': overall_score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'category_scores': category_scores,
            'metrics': metrics,
            'question_results': question_results
        }
        
        return jsonify({
            "success": True,
            "overall_score": overall_score,
            "category_scores": category_scores,
            "metrics": metrics,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "question_results": question_results,
            "next_round_url": "/hr"
        })
    except Exception as e:
        print(f"Error submitting technical answers: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to submit answers"
        })

def determine_aptitude_category(question_text):
    """Determine the category of an aptitude question based on its content."""
    question_lower = question_text.lower()
    
    # Numerical reasoning patterns
    if any(word in question_lower for word in ['calculate', 'sum', 'multiply', 'divide', 'percentage', 'ratio', 'number']):
        return 'numerical_ability'
    
    # Logical reasoning patterns
    elif any(word in question_lower for word in ['if', 'then', 'all', 'some', 'none', 'logical', 'sequence']):
        return 'logical_reasoning'
    
    # Verbal ability patterns
    elif any(word in question_lower for word in ['word', 'sentence', 'grammar', 'meaning', 'opposite', 'analogy']):
        return 'verbal_ability'
    
    # Abstract reasoning patterns
    elif any(word in question_lower for word in ['pattern', 'series', 'next', 'figure', 'shape', 'sequence']):
        return 'abstract_reasoning'
    
    # Default to logical reasoning if no clear category is found
    return 'logical_reasoning'

def determine_technical_category(question_text):
    """Determine the category of a technical question based on its content."""
    question_lower = question_text.lower()
    
    # System Design patterns
    if any(word in question_lower for word in ['design', 'architecture', 'scalability', 'system', 'distributed']):
        return 'system_design'
    
    # Operating Systems patterns
    elif any(word in question_lower for word in ['os', 'process', 'thread', 'memory', 'cpu', 'scheduling']):
        return 'operating_systems'
    
    # Database patterns
    elif any(word in question_lower for word in ['database', 'sql', 'query', 'table', 'index', 'normalization']):
        return 'databases'
    
    # Networking patterns
    elif any(word in question_lower for word in ['network', 'protocol', 'tcp', 'ip', 'http', 'dns']):
        return 'networking'
    
    # Data Structures patterns
    elif any(word in question_lower for word in ['array', 'list', 'tree', 'graph', 'stack', 'queue']):
        return 'data_structures'
    
    # Algorithms patterns
    elif any(word in question_lower for word in ['algorithm', 'complexity', 'sort', 'search', 'dynamic', 'recursive']):
        return 'algorithms'
    
    # Default to system design if no clear category is found
    return 'system_design'

@app.route("/view-scores")
def view_scores():
    try:
        # Get scores from session
        aptitude_score = session.get('aptitude_score', {})
        technical_score = session.get('technical_score', {})
        
        return render_template(
            "scores.html",
            aptitude_score=aptitude_score,
            technical_score=technical_score
        )
    except Exception as e:
        print(f"Error viewing scores: {str(e)}")
        return "Error loading scores", 500

@socketio.on('connect')
def handle_connect():
    session['monitoring'] = True
    emit('connection_response', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    session['monitoring'] = False
    proctor_service.end_monitoring(session.get('user_id'))

@socketio.on('frame')
def handle_frame(frame_data):
    if not session.get('monitoring'):
        return
    
    incidents = proctor_service.analyze_frame(
        frame_data,
        session.get('user_id'),
        session.get('current_question')
    )
    
    if incidents:
        emit('incident_detected', {'incidents': incidents})

@socketio.on('audio')
def handle_audio(audio_data):
    if not session.get('monitoring'):
        return
    
    metrics = speech_analyzer.analyze_audio(
        audio_data,
        session.get('user_id'),
        session.get('current_question')
    )
    
    if metrics:
        emit('speech_metrics', {'metrics': metrics})

@app.route('/start-monitoring', methods=['POST'])
def start_monitoring():
    user_id = session.get('user_id')
    question_id = request.json.get('question_id')
    
    session['current_question'] = question_id
    proctor_service.start_monitoring(user_id)
    
    return jsonify({'status': 'success'})

@app.route('/end-monitoring', methods=['POST'])
def end_monitoring():
    user_id = session.get('user_id')
    proctor_service.end_monitoring(user_id)
    session['monitoring'] = False
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    # Create the uploads directory if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Create the database tables
    with app.app_context():
        conn = sqlite3.connect('interview.db')
        cursor = conn.cursor()
        
        # Create proctoring_incidents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proctoring_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                incident_type TEXT NOT NULL,
                confidence_score FLOAT NOT NULL,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # Configure for immediate output
    import sys
    import logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    
    # Run the Flask app with SocketIO and force output to be unbuffered
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, log_output=True)
