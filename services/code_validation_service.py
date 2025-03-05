import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class CodeValidationService:
    def __init__(self):
        self.api_url = "https://api.compilebox.com/compile"
        self.language_map = {
            'python': 'python3',
            'javascript': 'nodejs',
            'java': 'java'
        }
        
    def validate_code(self, code, language, test_cases):
        """
        Validate code using CompileBox API
        Args:
            code (str): The code to validate
            language (str): Programming language (python/javascript/java)
            test_cases (list): List of test cases to run
        Returns:
            dict: Validation results including test case outcomes
        """
        try:
            # Map our language names to CompileBox language codes
            lang_code = self.language_map.get(language, 'python3')
            
            # Run test cases
            test_results = []
            for test_case in test_cases:
                # Prepare the code with test case
                full_code = f"{code}\n\n# Test case\n{test_case['test_code']}"
                
                # Prepare the request payload
                payload = {
                    "lang": lang_code,
                    "code": full_code,
                    "input": "",
                    "timeout": 10
                }
                
                # Make the API request
                response = requests.post(self.api_url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # Check if there were any compilation errors
                if result.get('status') == 'error':
                    return {
                        'success': False,
                        'error': result.get('error', 'Compilation error'),
                        'output': None,
                        'test_results': []
                    }
                
                # Get the output
                output = result.get('output', '').strip()
                
                # Check if test passed
                test_passed = output == test_case['expected_output'].strip()
                
                test_results.append({
                    'test_case': test_case['description'],
                    'passed': test_passed,
                    'output': output,
                    'expected_output': test_case['expected_output']
                })
            
            # Calculate overall success
            all_passed = all(test['passed'] for test in test_results)
            
            return {
                'success': all_passed,
                'output': result.get('output', ''),
                'test_results': test_results
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"API request failed: {str(e)}",
                'output': None,
                'test_results': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Validation failed: {str(e)}",
                'output': None,
                'test_results': []
            }
    
    def get_test_cases(self, question_id):
        """
        Get test cases for a specific question
        Args:
            question_id (str): The ID of the question
        Returns:
            list: List of test cases
        """
        # This will be implemented when we integrate with LeetCode API
        # For now, return sample test cases
        return [
            {
                'description': 'Basic test case',
                'test_code': 'print(solution([1, 2, 3]))',
                'expected_output': '6'
            },
            {
                'description': 'Edge case',
                'test_code': 'print(solution([]))',
                'expected_output': '0'
            }
        ] 