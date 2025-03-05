from flask import jsonify
import json

class VoiceChat:
    def __init__(self):
        self.questions = []
        self.current_question_index = 0
        self.round_type = None
        
    def set_questions(self, questions, round_type=None):
        """Set the list of questions for the interview."""
        self.questions = questions
        self.current_question_index = 0
        self.round_type = round_type
        
    def get_next_question(self):
        """Get the next question in the sequence."""
        if self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            self.current_question_index += 1
            return question
        return None
        
    def process_response(self, text_response):
        """Process the user's response and determine next action."""
        try:
            next_question = self.get_next_question()
            
            if next_question:
                return {
                    "success": True,
                    "next_question": next_question,
                    "is_complete": False,
                    "continue": True
                }
            else:
                return {
                    "success": True,
                    "message": "Interview round complete",
                    "is_complete": True,
                    "continue": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 