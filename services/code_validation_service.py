import subprocess
import tempfile
import os
import json
from typing import Dict, Any, List
import requests
from datetime import datetime
from dotenv import load_dotenv
import logging
import re

load_dotenv()

logger = logging.getLogger(__name__)

class CodeValidationService:
    def __init__(self):
        self.supported_languages = ['python', 'javascript', 'java', 'cpp', 'c']
        self.api_url = "https://leetcode.com/api/problems/all/"
        self.graphql_url = "https://leetcode.com/graphql"
        
    def validate_code(self, code: str, language: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate user's code against test cases with enhanced security
        Args:
            code (str): User's code
            language (str): Programming language
            question_data (dict): Question data containing test cases and starter code
        Returns:
            dict: Validation results
        """
        if language not in self.supported_languages:
            return {
                'success': False,
                'error': f'Language {language} is not supported'
            }
            
        try:
            # Security checks
            if not self._is_code_safe(code, language):
                return {
                    'success': False,
                    'error': 'Code contains potentially unsafe operations'
                }

            # Get test cases and expected outputs
            test_cases = []
            expected_outputs = {}
            
            # 1. Try getting test cases from question data
            if 'test_cases' in question_data:
                for test_case in question_data['test_cases']:
                    if isinstance(test_case, dict):
                        test_cases.append(test_case['input'])
                        expected_outputs[test_case['input']] = test_case['output']
                    else:
                        test_cases.append(test_case)
            
            # 2. Try getting from example test cases
            if 'exampleTestcases' in question_data:
                examples = question_data['exampleTestcases']
                if isinstance(examples, list):
                    for example in examples:
                        if isinstance(example, dict):
                            test_cases.append(example['input'])
                            expected_outputs[example['input']] = example['output']
                        else:
                            test_cases.append(example)
                elif isinstance(examples, str):
                    for line in examples.strip().split('\n'):
                        if line.strip():
                            test_cases.append(line.strip())
            
            # 3. Try getting from sample test case
            if 'sampleTestCase' in question_data:
                sample = question_data['sampleTestCase']
                if sample and sample not in test_cases:
                    test_cases.append(sample)
            
            # 4. Extract test cases from content if needed
            if not test_cases and 'content' in question_data:
                content = question_data['content']
                examples = re.finditer(r'Example \d+:?\s*Input:?\s*(.*?)\s*Output:?\s*(.*?)(?=Example|$)', 
                                    content, re.DOTALL)
                for match in examples:
                    input_data = match.group(1).strip()
                    output_data = match.group(2).strip()
                    test_cases.append(input_data)
                    expected_outputs[input_data] = output_data
            
            # 5. Get expected outputs from metadata if available
            if 'metadata' in question_data and 'expected_outputs' in question_data['metadata']:
                expected_outputs.update(question_data['metadata']['expected_outputs'])
            
            # Prepare and run test code
            test_code = self._prepare_code_with_tests(code, language, test_cases, question_data['starter_code'][language])
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=self._get_file_extension(language), mode='w', delete=False) as f:
                f.write(test_code)
                temp_file = f.name
            
            try:
                # Run the code with resource limits
                output = self._execute_code(temp_file, language)
                
                # Parse results
                try:
                    results = json.loads(output)
                    
                    # Add expected outputs to results
                    for result in results:
                        test_case = result.get('test_case')
                        if test_case in expected_outputs:
                            result['expected_output'] = expected_outputs[test_case]
                    
                    # Calculate overall success
                    success = all(result.get('passed', False) for result in results)
                    
                    return {
                        'success': success,
                        'results': results
                    }
                    
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': f'Failed to parse test results: {output}'
                    }
                    
            finally:
                # Clean up
                try:
                    os.unlink(temp_file)
                    if language == 'java':
                        class_file = temp_file.replace('.java', '.class')
                        if os.path.exists(class_file):
                            os.unlink(class_file)
                except Exception as e:
                    self.logger.error(f"Error cleaning up temporary files: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error in code validation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _run_test_case(self, code: str, language: str, test_case: str, starter_code: str) -> Dict[str, Any]:
        """Run a single test case"""
        try:
            # Split test case into input and expected output
            parts = test_case.split('\n')
            input_part = parts[0] if parts else ''
            expected_output = parts[1] if len(parts) > 1 else ''
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=self._get_file_extension(language), mode='w', delete=False) as f:
                # Prepare code with test case
                test_code = self._prepare_code_with_test(code, language, input_part, starter_code)
                f.write(test_code)
                temp_file = f.name
            
            # Run the code
            output = self._execute_code(temp_file, language)
            
            # Clean up
            os.unlink(temp_file)
            
            # Parse output and compare with expected
            actual_output = self._parse_actual_output(output)
            
            # If expected_output is empty, we can't validate
            if not expected_output:
                return {
                    'input': input_part,
                    'actual_output': actual_output,
                    'error': 'No expected output provided',
                    'passed': False
                }
            
            # Try to parse expected output
            try:
                expected = json.loads(expected_output)
            except json.JSONDecodeError:
                expected = expected_output.strip()
            
            # Try to parse actual output if it's not already parsed
            if isinstance(actual_output, str):
                try:
                    actual = json.loads(actual_output)
                except json.JSONDecodeError:
                    actual = actual_output.strip()
            else:
                actual = actual_output
            
            # Compare outputs
            passed = self._compare_outputs(expected, actual)
            
            return {
                'input': input_part,
                'expected_output': expected,
                'actual_output': actual,
                'passed': passed
            }
            
        except Exception as e:
            logger.error(f"Error running test case: {str(e)}")
            return {
                'input': test_case,
                'error': str(e),
                'passed': False
            }
    
    def _prepare_code_with_test(self, code: str, language: str, test_case: str, starter_code: str) -> str:
        """Prepare code with test case for execution"""
        try:
            # Extract function name from starter code
            if language == 'python':
                match = re.search(r'def\s+(\w+)\s*\(', starter_code)
                if match:
                    function_name = match.group(1)
                    test_code = f"""
import json
import sys
import traceback

{code}

def run_test(test_input):
    try:
        # Parse input if it's a string representation of a data structure
        try:
            input_data = json.loads(test_input)
        except json.JSONDecodeError:
            # If not JSON, use as is (for strings, etc)
            input_data = test_input.strip('"\'')
        
        # Call the function with parsed input
        result = {function_name}(input_data)
        
        # Convert result to JSON if it's a complex type
        if isinstance(result, (list, dict, bool)):
            print(json.dumps(result))
        else:
            print(result)
    except Exception as e:
        print(f"Runtime error: {{str(e)}}")
        traceback.print_exc()

# Run the test
test_input = '''{test_case}'''
run_test(test_input)
"""
                    return test_code
            elif language == 'javascript':
                match = re.search(r'function\s+(\w+)\s*\(', starter_code)
                if match:
                    function_name = match.group(1)
                    return f"""
{code}

// Test case
try {{
    let input_data;
    try {{
        input_data = JSON.parse('{test_case}');
    }} catch (e) {{
        input_data = '{test_case}'.replace(/^["'](.*)["']$/, '$1');
    }}
    const result = {function_name}(input_data);
    console.log(typeof result === 'object' ? JSON.stringify(result) : result);
}} catch (e) {{
    console.log(`Runtime error: ${{e.message}}`);
    console.error(e);
}}
"""
            elif language == 'java':
                match = re.search(r'public\s+\w+\s+(\w+)\s*\(', starter_code)
                if match:
                    function_name = match.group(1)
                    return f"""
{code}

class Main {{
    public static void main(String[] args) {{
        try {{
            Solution solution = new Solution();
            String input = "{test_case}";
            Object result;
            
            // Try parsing as JSON
            try {{
                com.google.gson.Gson gson = new com.google.gson.Gson();
                Object inputData = gson.fromJson(input, Object.class);
                result = solution.{function_name}(inputData);
            }} catch (Exception e) {{
                // If not JSON, use as string
                result = solution.{function_name}(input.replaceAll("^\\"(.*)\\"$", "$1"));
            }}
            
            // Print result
            if (result instanceof String) {{
                System.out.println("\\"" + result + "\\"");
            }} else {{
                System.out.println(result);
            }}
        }} catch (Exception e) {{
            System.out.println("Runtime error: " + e.getMessage());
            e.printStackTrace();
        }}
    }}
}}
"""
            return code
        except Exception as e:
            logger.error(f"Error preparing test code: {str(e)}")
            return code
    
    def _execute_code(self, file_path: str, language: str) -> str:
        """Execute code in the specified language"""
        try:
            if language == 'python':
                result = subprocess.run(['python', file_path], capture_output=True, text=True, timeout=5)
            elif language == 'javascript':
                result = subprocess.run(['node', file_path], capture_output=True, text=True, timeout=5)
            elif language == 'java':
                # Compile first
                class_name = os.path.splitext(os.path.basename(file_path))[0]
                subprocess.run(['javac', file_path], check=True)
                result = subprocess.run(['java', class_name], capture_output=True, text=True, timeout=5)
            elif language == 'cpp':
                # Compile first
                output_file = file_path.rsplit('.', 1)[0]
                subprocess.run(['g++', file_path, '-o', output_file], check=True)
                result = subprocess.run([output_file], capture_output=True, text=True, timeout=5)
            elif language == 'c':
                # Compile first
                output_file = file_path.rsplit('.', 1)[0]
                subprocess.run(['gcc', file_path, '-o', output_file], check=True)
                result = subprocess.run([output_file], capture_output=True, text=True, timeout=5)
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            return "Execution timed out"
        except Exception as e:
            return f"Execution error: {str(e)}"
    
    def _get_file_extension(self, language: str) -> str:
        """Get file extension for the language"""
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'java': '.java',
            'cpp': '.cpp',
            'c': '.c'
        }
        return extensions.get(language, '.txt')
    
    def _is_code_safe(self, code: str, language: str) -> bool:
        """Check if code contains potentially unsafe operations"""
        unsafe_patterns = {
            'python': [
                'import os', 'import sys', 'import subprocess',
                'eval(', 'exec(', 'open(', 'file(',
                'os.system', 'os.popen', 'subprocess.call'
            ],
            'javascript': [
                'eval(', 'Function(', 'require(', 'import(',
                'process.', 'child_process.', 'fs.'
            ],
            'java': [
                'Runtime.', 'ProcessBuilder', 'System.exec',
                'File.', 'FileInputStream', 'FileOutputStream'
            ],
            'cpp': [
                'system(', 'exec', 'popen', 'fork',
                'open(', 'fopen', 'fstream'
            ],
            'c': [
                'system(', 'exec', 'popen', 'fork',
                'open(', 'fopen', 'FILE'
            ]
        }
        
        patterns = unsafe_patterns.get(language, [])
        return not any(pattern in code for pattern in patterns)
    
    def _parse_expected_output(self, test_case: str) -> Any:
        """Parse expected output from test case"""
        try:
            # First try to parse as JSON object containing input and expected output
            try:
                test_data = json.loads(test_case)
                if isinstance(test_data, dict) and 'input' in test_data and 'expected' in test_data:
                    return test_data['expected']
            except json.JSONDecodeError:
                pass

            # Try splitting by newline
            parts = test_case.split('\n')
            if len(parts) == 2:
                return parts[1].strip()

            # If single value, assume it's the input and extract expected from question data
            return test_case.strip()

        except Exception as e:
            logger.error(f"Error parsing expected output: {str(e)}")
            return None
    
    def _parse_actual_output(self, output: str) -> Any:
        """Parse actual output from code execution"""
        try:
            # Check for runtime errors
            if output.startswith("Runtime error:") or output.startswith("Execution error:"):
                return output
            
            # Try to parse as JSON if possible
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # If not JSON, return as string with quotes stripped
                return output.strip().strip('"\'')
                
        except Exception as e:
            logger.error(f"Error parsing actual output: {str(e)}")
            return output
    
    def _compare_outputs(self, expected: Any, actual: Any) -> bool:
        """Compare expected and actual outputs"""
        try:
            # Handle error cases
            if isinstance(actual, str) and (actual.startswith("Runtime error:") or 
                                         actual.startswith("Execution error:")):
                return False
            
            if expected is None:
                return False
                
            # If both are strings, compare them after stripping
            if isinstance(expected, str) and isinstance(actual, str):
                return expected.strip().strip('"\'') == actual.strip().strip('"\'')
                
            # For other types (lists, dicts, numbers), use direct comparison
            return expected == actual
            
        except Exception as e:
            logger.error(f"Error comparing outputs: {str(e)}")
            return False
    
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

    def _prepare_code_with_tests(self, code: str, language: str, test_cases: List[str], starter_code: str) -> str:
        """Prepare code with test cases for execution"""
        try:
            if language == 'python':
                # Extract function name from starter code
                match = re.search(r'def\s+(\w+)\s*\((.*?)\)', starter_code)
                if not match:
                    raise ValueError("Could not extract function signature from starter code")
                
                function_name = match.group(1)
                params = [p.split(':')[0].strip() for p in match.group(2).split(',') if p.strip()]
                param_count = len(params)
                
                test_code = f"""
import json
import sys
import traceback
import ast

{code}

def run_tests():
    test_cases = {json.dumps(test_cases)}
    results = []
    
    for test_case in test_cases:
        try:
            # Parse input
            try:
                # Try to parse as JSON first
                input_data = json.loads(test_case)
            except json.JSONDecodeError:
                try:
                    # Try to parse as Python literal
                    input_data = ast.literal_eval(test_case)
                except:
                    # If all else fails, use as string
                    input_data = test_case.strip('"\'')
            
            # Prepare arguments
            if isinstance(input_data, (list, tuple)):
                if len(input_data) == param_count:
                    args = input_data
                elif param_count == 1:
                    args = [input_data]
                else:
                    args = input_data[:param_count]
            else:
                args = [input_data]
            
            # Execute test
            try:
                result = {function_name}(*args[:param_count])
                
                # Format result
                if isinstance(result, (list, dict, bool)):
                    output = json.dumps(result)
                else:
                    output = str(result)
                
                results.append({{'test_case': test_case, 'output': output, 'passed': True}})
                
            except Exception as e:
                error_msg = f"Runtime Error: {{str(e)}}\\n{{traceback.format_exc()}}"
                results.append({{'test_case': test_case, 'error': error_msg, 'passed': False}})
                
        except Exception as e:
            error_msg = f"Test Case Error: {{str(e)}}\\n{{traceback.format_exc()}}"
            results.append({{'test_case': test_case, 'error': error_msg, 'passed': False}})
    
    print(json.dumps(results))

if __name__ == '__main__':
    run_tests()
"""
                return test_code
                
            elif language == 'javascript':
                match = re.search(r'function\s+(\w+)\s*\((.*?)\)', starter_code)
                if match:
                    function_name = match.group(1)
                    params = [p.trim() for p in match.group(2).split(',') if p.trim()]
                    param_count = len(params)
                    
                    return f"""
{code}

function runTests() {{
    const testCases = {json.dumps(test_cases)};
    const results = [];
    
    for (const testCase of testCases) {{
        try {{
            // Parse input
            let inputData;
            try {{
                inputData = JSON.parse(testCase);
            }} catch (e) {{
                inputData = testCase.replace(/^["'](.*)["']$/, '$1');
            }}
            
            // Prepare arguments
            let args;
            if (Array.isArray(inputData)) {{
                if (inputData.length === {param_count}) {{
                    args = inputData;
                }} else if ({param_count} === 1) {{
                    args = [inputData];
                }} else {{
                    args = inputData.slice(0, {param_count});
                }}
            }} else {{
                args = [inputData];
            }}
            
            // Execute test
            const result = {function_name}(...args.slice(0, {param_count}));
            const output = typeof result === 'object' ? JSON.stringify(result) : String(result);
            
            results.push({{ testCase, output, passed: true }});
            
        }} catch (e) {{
            results.push({{
                testCase,
                error: `Runtime Error: ${{e.message}}\\n${{e.stack}}`,
                passed: false
            }});
        }}
    }}
    
    console.log(JSON.stringify(results));
}}

runTests();
"""
            
            elif language == 'java':
                match = re.search(r'public\s+\w+\s+(\w+)\s*\((.*?)\)', starter_code)
                if match:
                    function_name = match.group(1)
                    params = [p.trim() for p in match.group(2).split(',') if p.trim()]
                    param_count = len(params)
                    
                    return f"""
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.util.*;

{code}

public class Main {{
    public static void main(String[] args) {{
        try {{
            Solution solution = new Solution();
            Gson gson = new Gson();
            List<String> testCases = gson.fromJson("{json.dumps(test_cases)}", new TypeToken<List<String>>(){{}}.getType());
            List<Map<String, Object>> results = new ArrayList<>();
            
            for (String testCase : testCases) {{
                try {{
                    // Parse input
                    Object inputData;
                    try {{
                        inputData = gson.fromJson(testCase, Object.class);
                    }} catch (Exception e) {{
                        inputData = testCase.replaceAll("^\\"(.*)\\"$", "$1");
                    }}
                    
                    // Prepare arguments and execute
                    Object result;
                    if (inputData instanceof List) {{
                        List<?> inputList = (List<?>) inputData;
                        if (inputList.size() == {param_count}) {{
                            result = solution.{function_name}(inputList.get(0));
                        }} else if ({param_count} == 1) {{
                            result = solution.{function_name}(inputList);
                        }} else {{
                            result = solution.{function_name}(inputList.get(0));
                        }}
                    }} else {{
                        result = solution.{function_name}(inputData);
                    }}
                    
                    // Format result
                    String output = result instanceof String ? "\\"" + result + "\\"" : String.valueOf(result);
                    Map<String, Object> testResult = new HashMap<>();
                    testResult.put("testCase", testCase);
                    testResult.put("output", output);
                    testResult.put("passed", true);
                    results.add(testResult);
                    
                }} catch (Exception e) {{
                    Map<String, Object> testResult = new HashMap<>();
                    testResult.put("testCase", testCase);
                    testResult.put("error", "Runtime Error: " + e.getMessage() + "\\n" + Arrays.toString(e.getStackTrace()));
                    testResult.put("passed", false);
                    results.add(testResult);
                }}
            }}
            
            System.out.println(gson.toJson(results));
            
        }} catch (Exception e) {{
            System.out.println(gson.toJson(Collections.singletonList(
                Map.of("error", "Fatal Error: " + e.getMessage() + "\\n" + Arrays.toString(e.getStackTrace()),
                       "passed", false)
            )));
        }}
    }}
}}
"""
            
            return code
            
        except Exception as e:
            logger.error(f"Error preparing test code: {str(e)}")
            raise 