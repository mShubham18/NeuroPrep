import os
import datetime
import openai
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from pipelines.question_generation_pipeline import question_generation_pipeline
from components.voice_chat import VoiceChat
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Add secret key for session management

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize APIs
openai.api_key = OPENAI_API_KEY

# Initialize VoiceChat
voice_chat = VoiceChat()

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
def get_aptitude_questions():
    try:
        # Get aptitude questions from the loaded questions
        aptitude_questions = INTERVIEW_QUESTIONS["aptitude"]
        
        # Format questions for the frontend
        formatted_questions = []
        for question, options in aptitude_questions.items():
            formatted_questions.append({
                "question": question,
                "options": options,  # This is already a list of 4 options
                "type": "mcq",  # Multiple choice questions for aptitude
                "category": "general"  # Default category
            })
        
        return jsonify({
            "success": True,
            "questions": formatted_questions
        })
    except Exception as e:
        print(f"Error getting aptitude questions: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to load aptitude questions"
        })

@app.route("/get-technical-questions")
def get_technical_questions():
    try:
        technical_questions = INTERVIEW_QUESTIONS["technical"]
        
        # Format questions for the frontend
        formatted_questions = []
        for question, options in technical_questions.items():
            formatted_questions.append({
                "question": question,
                "options": options,  # This is already a list of 4 options
                "type": "mcq",  # All technical questions are MCQs as per generate_Technical
                "category": "technical",  # Default category
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
        
        # Calculate score
        aptitude_questions = INTERVIEW_QUESTIONS["aptitude"]
        correct_answers = 0
        total_questions = len(aptitude_questions)
        
        for i, answer in enumerate(answers):
            if i < total_questions:
                # Assuming each question has a 'correct_answer' field
                if answer == aptitude_questions[i].get("correct_answer"):
                    correct_answers += 1
        
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        return jsonify({
            "success": True,
            "score": score,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
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
        
        # Process technical answers (can be more complex based on question type)
        technical_questions = INTERVIEW_QUESTIONS["technical"]
        results = []
        
        for i, answer in enumerate(answers):
            if i < len(technical_questions):
                question = technical_questions[i]
                if question.get("type") == "coding":
                    # Here you would evaluate the code against test cases
                    result = {
                        "question": i + 1,
                        "status": "Evaluated",  # You can add actual evaluation logic
                        "feedback": "Code submitted successfully"
                    }
                else:
                    # For theory/MCQ questions
                    result = {
                        "question": i + 1,
                        "status": "Submitted",
                        "feedback": "Answer recorded"
                    }
                results.append(result)
        
        return jsonify({
            "success": True,
            "results": results,
            "next_round_url": "/hr"  # Next round after technical
        })
    except Exception as e:
        print(f"Error submitting technical answers: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to submit answers"
        })

if __name__ == "__main__":
    app.run(debug=True)
