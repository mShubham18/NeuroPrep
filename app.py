import os
import datetime
import openai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from pipelines.question_generation_pipeline import question_generation_pipeline
from components.voice_chat import VoiceChat

load_dotenv()

app = Flask(__name__)

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize APIs
openai.api_key = OPENAI_API_KEY

# Initialize VoiceChat
voice_chat = VoiceChat()

# Global Variable (Initializes only when accessed)
INTERVIEW_QUESTIONS = None

def load_questions():
    """Loads questions only once."""
    global INTERVIEW_QUESTIONS
    if INTERVIEW_QUESTIONS is None:
        print("Running question generation pipeline...")
        intro, apt, tech, code, hr = question_generation_pipeline("resume.pdf")
        INTERVIEW_QUESTIONS = {
            "introduction": intro,
            "aptitude": apt,
            "technical": tech,
            "coding": code,
            "hr": hr
        }
        # Set introduction questions for voice chat
        voice_chat.set_questions(intro)

@app.before_request
def ensure_questions_loaded():
    """Ensures questions are loaded before any request."""
    load_questions()

@app.route("/")
def index():
    return render_template("interview.html")

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

if __name__ == "__main__":
    app.run(debug=True)
