from components.model_configuration import model_config
import sqlite3
from datetime import datetime
import subprocess
import tempfile
import os

class ValidationService:
    def __init__(self, session_id):
        self.session_id = session_id
        self.model = model_config()
        
    def validate_aptitude_answer(self, question, user_answer, correct_answer):
        """Validate aptitude answer using Gemini LLM"""
        prompt = f"""You are an AI validating an aptitude test answer.

        Question: {question}
        User's Answer: {user_answer}
        Correct Answer: {correct_answer}

        Please analyze if the user's answer is correct. Consider:
        1. Exact match with correct answer
        2. Equivalent answers (e.g., "4" and "four")
        3. Numerical precision
        4. Logical equivalence

        Respond with ONLY "correct" or "incorrect"."""

        response = self.model.generate_content(prompt)
        is_correct = response.text.strip().lower() == "correct"
        
        # Store the result
        self._store_question_response(
            round_type="aptitude",
            question_text=question,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct
        )
        
        return is_correct

    def validate_technical_answer(self, question, user_answer, correct_answer):
        """Validate technical answer using Gemini LLM"""
        prompt = f"""You are an AI validating a technical interview answer.

        Question: {question}
        User's Answer: {user_answer}
        Correct Answer: {correct_answer}

        Please analyze if the user's answer is correct. Consider:
        1. Technical accuracy
        2. Key concepts covered
        3. Alternative valid approaches
        4. Level of detail

        Respond with ONLY "correct" or "incorrect"."""

        response = self.model.generate_content(prompt)
        is_correct = response.text.strip().lower() == "correct"
        
        # Store the result
        self._store_question_response(
            round_type="technical",
            question_text=question,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct
        )
        
        return is_correct

    def validate_coding_solution(self, question, code, language):
        """Validate coding solution using Gemini LLM and code execution"""
        # First, validate the code structure and logic
        prompt = f"""You are an AI validating a coding solution.

        Question: {question}
        Code:
        ```{language}
        {code}
        ```

        Please analyze the code for:
        1. Correct algorithm implementation
        2. Edge case handling
        3. Time and space complexity
        4. Code quality and best practices

        Respond with ONLY "correct" or "incorrect"."""

        response = self.model.generate_content(prompt)
        is_correct = response.text.strip().lower() == "correct"
        
        # If the code is logically correct, try to execute it
        if is_correct:
            is_correct = self._execute_code(code, language)
        
        # Store the result
        self._store_question_response(
            round_type="coding",
            question_text=question,
            user_answer=code,
            correct_answer="[Code Solution]",
            is_correct=is_correct
        )
        
        return is_correct

    def _execute_code(self, code, language):
        """Execute code in a safe environment"""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Execute based on language
            if language == 'python':
                result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=5)
            elif language == 'javascript':
                result = subprocess.run(['node', temp_file], capture_output=True, text=True, timeout=5)
            elif language == 'java':
                # Compile first
                compile_result = subprocess.run(['javac', temp_file], capture_output=True, text=True)
                if compile_result.returncode == 0:
                    # Run the compiled class
                    class_file = temp_file[:-5]  # Remove .java extension
                    result = subprocess.run(['java', class_file], capture_output=True, text=True, timeout=5)
                else:
                    return False
            else:
                return False

            # Clean up
            os.unlink(temp_file)
            if language == 'java':
                os.unlink(f"{class_file}.class")

            # Check if execution was successful
            return result.returncode == 0

        except Exception as e:
            print(f"Error executing code: {str(e)}")
            return False

    def _store_question_response(self, round_type, question_text, user_answer, correct_answer, is_correct):
        """Store question response in database"""
        conn = sqlite3.connect('interview.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO question_responses 
            (session_id, round_type, question_text, user_answer, correct_answer, is_correct)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            self.session_id,
            round_type,
            question_text,
            user_answer,
            correct_answer,
            is_correct
        ))
        
        conn.commit()
        conn.close()

    def get_round_summary(self, round_type):
        """Get summary of round performance"""
        conn = sqlite3.connect('interview.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_questions,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
            FROM question_responses
            WHERE session_id = ? AND round_type = ?
        """, (self.session_id, round_type))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            return {
                'total_questions': result[0],
                'correct_answers': result[1],
                'score': (result[1] / result[0]) * 100
            }
        return {
            'total_questions': 0,
            'correct_answers': 0,
            'score': 0
        }

    def _store_round_completion(self, round_type):
        """Store round completion in database"""
        conn = sqlite3.connect('interview.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO round_completions 
            (session_id, round_type, completed_at)
            VALUES (?, ?, datetime('now'))
        """, (self.session_id, round_type))
        
        conn.commit()
        conn.close() 