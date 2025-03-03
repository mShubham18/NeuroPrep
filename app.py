import os
import jwt
import datetime
import openai
import random
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from pipelines.question_generation_pipeline import question_generation_pipeline

load_dotenv()

app = Flask(__name__)

# Load environment variables
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_SECRET = os.getenv("LIVEKIT_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# 🔹 Global Variable (Initializes only when accessed)
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

@app.before_request
def ensure_questions_loaded():
    """Ensures questions are loaded before any request."""
    load_questions()

# Track current question index
user_sessions = {}

@app.route("/")
def index():
    return render_template("test.html")

@app.route("/get-token", methods=["POST"])
def get_token():
    user_name = request.json.get("name", "Guest")

    now = datetime.datetime.utcnow()
    payload = {
        "video": True,
        "audio": True,
        "sub": user_name,
        "exp": now + datetime.timedelta(hours=1),
    }
    
    token = jwt.encode(payload, LIVEKIT_SECRET, algorithm="HS256")
    return jsonify({"token": token, "url": LIVEKIT_URL})

@app.route("/ai-response", methods=["POST"])
def ai_response():
    user_name = request.json.get("user", "Guest")
    round_type = request.json.get("round", "introduction")

    if user_name not in user_sessions:
        user_sessions[user_name] = {"index": 0}

    index = user_sessions[user_name]["index"]

    if index < len(INTERVIEW_QUESTIONS[round_type]):
        question = INTERVIEW_QUESTIONS[round_type][index]
        user_sessions[user_name]["index"] += 1
    else:
        question = "That's all for this round. Please proceed to the next round."

    return jsonify({"reply": question})

if __name__ == "__main__":
    app.run(debug=True)
