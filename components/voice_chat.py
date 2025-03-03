from flask import jsonify
import json

class VoiceChat:
    def __init__(self):
        self.current_question_index = 0
        self.questions = []
        
    def set_questions(self, questions):
        self.questions = questions
        self.current_question_index = 0
        
    def get_next_question(self):
        if self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            self.current_question_index += 1
            return question
        return None
        
    def process_response(self, text_response):
        try:
            # Process the response and determine if we should continue
            next_question = self.get_next_question()
            if next_question:
                return jsonify({
                    "success": True,
                    "next_question": next_question,
                    "continue": True
                })
            else:
                return jsonify({
                    "success": True,
                    "message": "Interview round complete",
                    "continue": False
                })
        except Exception as e:
            return jsonify({"error": str(e), "success": False}) 