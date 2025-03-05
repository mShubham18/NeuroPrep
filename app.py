import os
import datetime
import openai
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
from pipelines.question_generation_pipeline import question_generation_pipeline
from components.voice_chat import VoiceChat
from werkzeug.utils import secure_filename
from services.proctor_service import ProctorService
from services.speech_analysis import SpeechAnalyzer
import uuid
import sqlite3
import queue
import threading
import time
from services.validation_service import ValidationService
from services.code_validation import CodeValidationService
from services.question_service import QuestionService

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Add secret key for session management
CORS(app)  # Enable CORS
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize APIs and services
openai.api_key = OPENAI_API_KEY
voice_chat = VoiceChat()
proctor_service = None  # Will be initialized per session
speech_analyzer = None  # Will be initialized per session

# Global Variable (Initializes only when accessed)
INTERVIEW_QUESTIONS = {}
progress_queues = {}

# Function to check if questions are loaded
def questions_are_loaded():
    # Check both session and global variable for all question types
    required_question_types = ['introduction', 'aptitude', 'technical', 'coding', 'hr']
    
    # Check global variable
    if all(q_type in INTERVIEW_QUESTIONS for q_type in required_question_types):
        return True
        
    # Check session
    if all(session.get(f'{q_type}_questions') for q_type in required_question_types):
        return True
        
    return False

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
        # Initialize user session if not exists
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            
        # Initialize progress queue for this user
        user_id = session['user_id']
        if user_id not in progress_queues:
            progress_queues[user_id] = queue.Queue()
            
        if 'resume' not in request.files:
            print("No resume file in request")  # Debug log
            return jsonify({
                "success": False,
                "error": "No resume file uploaded"
            })
        
        file = request.files['resume']
        if file.filename == '':
            print("Empty filename")  # Debug log
            return jsonify({
                "success": False,
                "error": "No file selected"
            })
        
        if file and allowed_file(file.filename):
            try:
                # Save the file
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"Saving file to: {file_path}")  # Debug log
                file.save(file_path)
                
                # Verify file was saved
                if not os.path.exists(file_path):
                    raise Exception("Failed to save file")
                
                # Store the file path in session
                session['resume_path'] = file_path
                print(f"File saved successfully at: {file_path}")  # Debug log
                
                # Add initial progress message
                progress_queues[user_id].put("Resume uploaded successfully")
                
                return jsonify({
                    "success": True,
                    "redirect": "/preparing"
                })
            except Exception as save_error:
                print(f"Error saving file: {str(save_error)}")  # Debug log
                return jsonify({
                    "success": False,
                    "error": f"Failed to save file: {str(save_error)}"
                })
        else:
            print(f"Invalid file type: {file.filename}")  # Debug log
            return jsonify({
                "success": False,
                "error": "Invalid file type. Please upload PDF, DOC, or DOCX files only."
            })
    except Exception as e:
        print(f"Error processing resume: {str(e)}")  # Debug log
        return jsonify({
            "success": False,
            "error": f"Error processing resume: {str(e)}"
        })


@app.route('/progress-stream')
def progress_stream():
    try:
        # Initialize user session if not exists
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            
        user_id = session.get('user_id')
        if not user_id:
            print("No user_id in session for progress stream")  # Debug log
            return "data: ERROR:User session not found\n\n", 200, {'Content-Type': 'text/event-stream'}
            
        # Initialize progress queue if not exists
        if user_id not in progress_queues:
            progress_queues[user_id] = queue.Queue()
            progress_queues[user_id].put("Initializing progress tracking...")

        def generate():
            try:
                queue_obj = progress_queues[user_id]
                last_message_time = time.time()
                
                while True:
                    try:
                        # Send heartbeat every 15 seconds if no message
                        current_time = time.time()
                        if current_time - last_message_time >= 15:
                            yield "data: heartbeat\n\n"
                            last_message_time = current_time
                            
                        # Try to get a message from the queue
                        try:
                            message = queue_obj.get(timeout=1)
                            last_message_time = time.time()
                            
                            # Handle different message types
                            if message.startswith('ERROR:'):
                                yield f"data: {message}\n\n"
                                break
                            elif message.startswith('REDIRECT:'):
                                yield f"data: {message}\n\n"
                                break
                            else:
                                yield f"data: {message}\n\n"
                                
                        except queue.Empty:
                            continue
                            
                    except Exception as e:
                        print(f"Error in progress stream loop: {str(e)}")  # Debug log
                        yield f"data: ERROR:Internal server error: {str(e)}\n\n"
                        break
                        
            except Exception as e:
                print(f"Error in progress stream generator: {str(e)}")  # Debug log
                yield f"data: ERROR:Stream error: {str(e)}\n\n"
                
            finally:
                # Only remove the queue if we're stopping due to completion or error
                if user_id in progress_queues:
                    last_message = queue_obj.get() if not queue_obj.empty() else None
                    if last_message and (last_message.startswith('ERROR:') or last_message.startswith('REDIRECT:')):
                        del progress_queues[user_id]
                    
        return Response(generate(), mimetype='text/event-stream')
        
    except Exception as e:
        print(f"Error setting up progress stream: {str(e)}")  # Debug log
        return "data: ERROR:Failed to setup progress stream\n\n", 200, {'Content-Type': 'text/event-stream'}

@app.route("/generate-questions")
def generate_questions():
    try:
        # Initialize user session if not exists
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            
        user_id = session.get('user_id')
        if user_id not in progress_queues:
            progress_queues[user_id] = queue.Queue()
            
        # Send initial progress message
        progress_queues[user_id].put("Starting question generation...")
        
        # Get the resume path from session
        resume_path = session.get('resume_path')
        if not resume_path:
            progress_queues[user_id].put("ERROR:No resume found")
            return jsonify({'success': False, 'error': 'No resume found'})
            
        # Generate all questions using the pipeline
        try:
            intro_questions, aptitude_questions, technical_questions, coding_questions, hr_questions = question_generation_pipeline(
                resume_path,
                progress_callback=lambda msg: progress_queues[user_id].put(msg)
            )
            
            # Store all questions in both session and global variable
            session['introduction_questions'] = intro_questions
            session['aptitude_questions'] = aptitude_questions
            session['technical_questions'] = technical_questions
            session['coding_questions'] = coding_questions
            session['hr_questions'] = hr_questions
            
            INTERVIEW_QUESTIONS['introduction'] = intro_questions
            INTERVIEW_QUESTIONS['aptitude'] = aptitude_questions
            INTERVIEW_QUESTIONS['technical'] = technical_questions
            INTERVIEW_QUESTIONS['coding'] = coding_questions
            INTERVIEW_QUESTIONS['hr'] = hr_questions
            
            progress_queues[user_id].put("Questions generated successfully")
            
            # Send redirect message
            progress_queues[user_id].put("REDIRECT:/introduction")
            print(f"Sent redirect message for user {user_id}")  # Debug log
            
            return jsonify({'success': True})
            
        except Exception as e:
            print(f"Error in question generation pipeline: {str(e)}")
            progress_queues[user_id].put(f"ERROR:{str(e)}")
            return jsonify({'success': False, 'error': str(e)})
            
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        if user_id in progress_queues:
            progress_queues[user_id].put(f"ERROR:{str(e)}")
        return jsonify({'success': False, 'error': str(e)})

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
    try:
        # Initialize session if not exists
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            
        # Initialize coding questions if not in session
        if 'coding_questions' not in session:
            session['coding_questions'] = INTERVIEW_QUESTIONS.get('coding', [])
            
        if 'current_coding_question' not in session:
            session['current_coding_question'] = 0
            
        # Verify we have questions
        if not session.get('coding_questions'):
            return redirect(url_for('coding_instructions'))
            
        return render_template("coding.html")
    except Exception as e:
        print(f"Error in coding_test: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

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

@app.route("/start-interview", methods=["POST"])
@require_questions
def start_interview():
    try:
        round_type = request.json.get("round")
        if not round_type:
            return jsonify({
                "success": False,
                "error": "Round type not specified"
            })
            
        if round_type == "introduction":
            # Get introduction questions from session or global variable
            questions = session.get('introduction_questions') or INTERVIEW_QUESTIONS.get('introduction', [])
            if not questions:
                return jsonify({
                    "success": False,
                    "error": "Introduction questions not loaded"
                })
                
            # Initialize voice chat with questions and round type
            voice_chat.set_questions(questions, round_type)
            
            # Get the first question
            question = voice_chat.get_next_question()
            if not question:
                return jsonify({
                    "success": False,
                    "error": "No questions available"
                })
                
            return jsonify({
                "success": True,
                "question": question
            })
            
        elif round_type == "hr":
            # Get HR questions from session or global variable
            questions = session.get('hr_questions') or INTERVIEW_QUESTIONS.get('hr', [])
            if not questions:
                return jsonify({
                    "success": False,
                    "error": "HR questions not loaded"
                })
                
            # Initialize voice chat with questions and round type
            voice_chat.set_questions(questions, round_type)
            
            # Get the first question
            question = voice_chat.get_next_question()
            if not question:
                return jsonify({
                    "success": False,
                    "error": "No questions available"
                })
                
            return jsonify({
                "success": True,
                "question": question
            })
            
        else:
            return jsonify({
                "success": False,
                "error": f"Invalid round type: {round_type}"
            })
            
    except Exception as e:
        print(f"Error in start_interview: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/process-response", methods=["POST"])
@require_questions
def process_response():
    try:
        text_response = request.json.get("response")
        print(f"Received response: {text_response}")  # Debug log
        
        if not text_response:
            print("Empty response received")
            return jsonify({
                "success": False,
                "error": "Empty response"
            })

        # Process the response using voice chat
        result = voice_chat.process_response(text_response)
        print(f"Processing result: {result}")  # Debug log
        
        # If the round is complete, store the results
        if result.get("is_complete"):
            session_id = session.get("session_id")
            if session_id:
                validation_service = ValidationService(session_id)
                # Store the round completion in the database
                validation_service._store_round_completion(voice_chat.round_type)
        
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
@require_questions
def get_technical_questions():
    try:
        technical_questions = INTERVIEW_QUESTIONS.get("technical", {})
        if not technical_questions:
            return jsonify({
                "success": False,
                "error": "Technical questions not loaded"
            })
        
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
def submit_aptitude():
    try:
        answers = request.json.get("answers", [])
        session_id = session.get("session_id")
        
        if not session_id:
            return jsonify({"success": False, "error": "No active session"})
            
        validation_service = ValidationService(session_id)
        aptitude_questions = INTERVIEW_QUESTIONS["aptitude"]
        questions_list = list(aptitude_questions.items())
        total_questions = len(aptitude_questions)
        
        # Initialize metrics
        metrics = {
            'numerical_ability': {'correct': 0, 'total': 0},
            'logical_reasoning': {'correct': 0, 'total': 0},
            'verbal_ability': {'correct': 0, 'total': 0},
            'data_interpretation': {'correct': 0, 'total': 0}
        }
        
        question_results = []
        correct_answers = 0
        
        # Validate each answer
        for i, answer in enumerate(answers):
            if i < len(questions_list):
                question_data = questions_list[i]
                question_text = question_data[0]
                correct_answer = question_data[1][1]
                
                # Determine question category
                category = determine_aptitude_category(question_text)
                metrics[category]['total'] += 1
                
                # Validate answer using Gemini LLM
                is_correct = validation_service.validate_aptitude_answer(
                    question_text,
                    answer,
                    correct_answer
                )
                
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
            category_scores[category] = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        
        # Store comprehensive results in session
        session['aptitude_score'] = {
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
            "next_round_url": "/technical"
        })
    except Exception as e:
        print(f"Error submitting aptitude answers: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to submit answers"
        })

@app.route("/submit-technical", methods=["POST"])
def submit_technical():
    try:
        answers = request.json.get("answers", [])
        session_id = session.get("session_id")
        
        if not session_id:
            return jsonify({"success": False, "error": "No active session"})
            
        validation_service = ValidationService(session_id)
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
        
        # Validate each answer
        for i, answer in enumerate(answers):
            if i < len(questions_list):
                question_data = questions_list[i]
                question_text = question_data[0]
                correct_answer = question_data[1][1]
                
                # Determine question category
                category = determine_technical_category(question_text)
                metrics[category]['total'] += 1
                
                # Validate answer using Gemini LLM
                is_correct = validation_service.validate_technical_answer(
                    question_text,
                    answer,
                    correct_answer
                )
                
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
            category_scores[category] = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        
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
            "next_round_url": "/coding"
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
        coding_score = session.get('coding_score', {})
        
        return render_template(
            "scores.html",
            aptitude_score=aptitude_score,
            technical_score=technical_score,
            coding_score=coding_score
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

@app.route("/get-coding-question")
def get_coding_question():
    try:
        # Initialize coding questions if not in session
        if 'coding_questions' not in session:
            if not INTERVIEW_QUESTIONS.get('coding'):
                return jsonify({
                    'success': False,
                    'error': 'No coding questions available'
                })
            session['coding_questions'] = INTERVIEW_QUESTIONS['coding']
            
        if 'current_coding_question' not in session:
            session['current_coding_question'] = 0
            
        current_index = session.get('current_coding_question', 0)
        questions = session['coding_questions']
        
        if not questions:
            return jsonify({
                'success': False,
                'error': 'No coding questions available'
            })
            
        if current_index >= len(questions):
            return jsonify({
                'success': False,
                'completed': True
            })
            
        # Ensure the question has all required fields
        question = questions[current_index]
        required_fields = ['id', 'title', 'difficulty', 'content', 'test_cases', 'starter_code']
        if not all(field in question for field in required_fields):
            print(f"Question {current_index} is missing required fields")
            return jsonify({
                'success': False,
                'error': 'Invalid question format'
            })
            
        return jsonify({
            'success': True,
            'question': question
        })
        
    except Exception as e:
        print(f"Error in get_coding_question: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route("/run-code", methods=['POST'])
def run_code():
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        question_id = data.get('question_id')
        
        if not all([code, language, question_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            })
            
        # Get current question
        questions = session.get('coding_questions', [])
        if not questions:
            return jsonify({
                'success': False,
                'error': 'No coding questions available'
            })
            
        current_index = session.get('current_coding_question', 0)
        if current_index >= len(questions):
            return jsonify({
                'success': False,
                'error': 'Invalid question index'
            })
            
        current_question = questions[current_index]
        if current_question['id'] != question_id:
            return jsonify({
                'success': False,
                'error': 'Invalid question ID'
            })
            
        # Validate code
        validation_service = CodeValidationService()
        results = validation_service.validate_code(code, language, current_question)
        
        if not results:
            return jsonify({
                'success': False,
                'error': 'Code validation failed'
            })
            
        return jsonify({
            'success': True,
            'results': results.get('results', [])
        })
        
    except Exception as e:
        print(f"Error in run_code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route("/submit-coding", methods=['POST'])
def submit_coding():
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        question_id = data.get('question_id')
        
        if not all([code, language, question_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            })
            
        # Get current question
        questions = session.get('coding_questions', [])
        if not questions:
            return jsonify({
                'success': False,
                'error': 'No coding questions available'
            })
            
        current_index = session.get('current_coding_question', 0)
        if current_index >= len(questions):
            return jsonify({
                'success': False,
                'error': 'Invalid question index'
            })
            
        current_question = questions[current_index]
        if current_question['id'] != question_id:
            return jsonify({
                'success': False,
                'error': 'Invalid question ID'
            })
            
        # Validate code
        validation_service = CodeValidationService()
        results = validation_service.validate_code(code, language, current_question)
        
        if not results or not results.get('success'):
            return jsonify({
                'success': False,
                'error': 'Code validation failed'
            })
            
        # Store submission
        if 'submissions' not in session:
            session['submissions'] = {}
        session['submissions'][question_id] = {
            'code': code,
            'language': language,
            'results': results.get('results', [])
        }
        
        # Move to next question
        session['current_coding_question'] = current_index + 1
        
        # Check if all questions are completed
        if session['current_coding_question'] >= len(questions):
            # Calculate final score
            total_tests = sum(len(sub['results']) for sub in session['submissions'].values())
            passed_tests = sum(
                sum(1 for test in sub['results'] if test.get('passed', False))
                for sub in session['submissions'].values()
            )
            score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Store final score
            session['coding_score'] = {
                'overall_score': score,
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'submissions': session['submissions']
            }
            
            return jsonify({
                'success': True,
                'completed': True,
                'score': score
            })
        else:
            return jsonify({
                'success': True,
                'completed': False
            })
            
    except Exception as e:
        print(f"Error in submit_coding: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Modify the generate_coding_questions function to fetch from LeetCode
@app.route("/generate-coding-questions", methods=["POST"])
def generate_coding_questions():
    try:
        # Use LeetCode API to fetch coding questions
        question_service = QuestionService()
        print("Fetching coding questions from LeetCode API")  # Debug log
        questions = question_service.get_questions_by_difficulty([], 'beginner')
        print(f"Questions fetched: {questions}")  # Debug log

        # Check for required fields in each question
        for question in questions:
            required_fields = ['id', 'title', 'difficulty', 'content', 'test_cases', 'starter_code']
            if not all(field in question for field in required_fields):
                print(f"Question {question.get('id', 'unknown')} is missing required fields")
                return jsonify({'success': False, 'error': 'Invalid question format'})

        # Store the coding questions in session
        session['coding_questions'] = questions
        session['current_coding_question'] = 0

        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        print(f"Error fetching coding questions: {str(e)}")  # Debug log
        return jsonify({'success': False, 'error': str(e)})

# Update the preparing route to use the new coding round functionality
@app.route("/preparing")
def preparing():
    return render_template("preparing.html")

# Ensure the frontend calls the new endpoint to generate coding questions
@app.route("/start-coding-round", methods=["POST"])
def start_coding_round():
    try:
        # Call the generate coding questions endpoint
        response = generate_coding_questions()
        if not response.json.get('success'):
            raise Exception(response.json.get('error', 'Failed to start coding round'))

        return jsonify({'success': True, 'redirect': '/introduction'})
    except Exception as e:
        print(f"Error starting coding round: {str(e)}")  # Debug log
        return jsonify({'success': False, 'error': str(e)})

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
        
        # Create round_completions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS round_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                round_type TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
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
