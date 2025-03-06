import subprocess
import tempfile
import os
import re
import json
import ast
# import resource  # Removed for Windows compatibility
import signal
import psutil
import logging
from typing import Dict, List, Any, Optional

class CodeValidationService:
    def __init__(self):
        self.supported_languages = ['python', 'javascript', 'java']
        self.test_timeout = 5  # seconds
        self.memory_limit = 512 * 1024 * 1024  # 512MB
        self.max_output_size = 1024 * 1024  # 1MB
        self.forbidden_imports = {
            'python': ['os', 'subprocess', 'sys', 'socket', 'threading', 'multiprocessing'],
            'javascript': ['child_process', 'fs', 'net', 'http', 'https'],
            'java': ['java.io', 'java.net', 'java.lang.reflect', 'java.lang.management']
        }
        self.logger = logging.getLogger(__name__)
        
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
            test_cases = question_data['test_cases']
            
            # Prepare code with test cases
            test_code = self._prepare_code_with_tests(code, language, test_cases, question_data['starter_code'][language])
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=self._get_file_extension(language), mode='w', delete=False) as f:
                f.write(test_code)
                temp_file = f.name
                
            try:
                # Run the code with resource limits
                results = self._run_code(temp_file, language)
                return results
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
    
    def _is_code_safe(self, code: str, language: str) -> bool:
        """Check if code contains potentially unsafe operations"""
        try:
            if language == 'python':
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            if name.name in self.forbidden_imports['python']:
                                return False
                    elif isinstance(node, ast.ImportFrom):
                        if node.module in self.forbidden_imports['python']:
                            return False
            elif language == 'javascript':
                for forbidden in self.forbidden_imports['javascript']:
                    if f"require('{forbidden}')" in code or f"import {forbidden}" in code:
                        return False
            elif language == 'java':
                for forbidden in self.forbidden_imports['java']:
                    if f"import {forbidden}" in code:
                        return False
            return True
        except Exception as e:
            self.logger.error(f"Error in safety check: {str(e)}")
            return False
    
    def _prepare_code_with_tests(self, user_code: str, language: str, test_cases: List[str], starter_code: str) -> str:
        """Prepare code with test cases based on language"""
        if language == 'python':
            return self._prepare_python_tests(user_code, test_cases, starter_code)
        elif language == 'javascript':
            return self._prepare_javascript_tests(user_code, test_cases, starter_code)
        elif language == 'java':
            return self._prepare_java_tests(user_code, test_cases, starter_code)
        else:
            raise ValueError(f'Language {language} is not supported')
    
    def _prepare_python_tests(self, user_code: str, test_cases: List[str], starter_code: str) -> str:
        """Prepare Python code with test cases"""
        try:
            # Extract function name from starter code
            func_name = re.search(r'def\s+(\w+)\s*\(', starter_code).group(1)
            
            # Prepare test code with enhanced error handling
            test_code = f"""
import sys
import json
import traceback
import ast

{user_code}

def run_tests():
    test_cases = {json.dumps(test_cases)}
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # Parse input
            try:
                input_data = json.loads(test_case)
                if isinstance(input_data, (list, tuple)):
                    args = input_data
                else:
                    args = [input_data]
            except json.JSONDecodeError:
                # If not JSON, try ast.literal_eval
                try:
                    input_data = ast.literal_eval(test_case)
                    if isinstance(input_data, (list, tuple)):
                        args = input_data
                    else:
                        args = [input_data]
                except:
                    # If all else fails, use as string
                    args = [test_case.strip('"\'')]
            
            # Run test
            try:
                result = {func_name}(*args)
                results.append({{'passed': True, 'output': str(result)}})
            except TypeError as e:
                # If too many arguments, try with the first argument only
                if "takes" in str(e) and "positional argument" in str(e):
                    try:
                        result = {func_name}(args[0])
                        results.append({{'passed': True, 'output': str(result)}})
                    except Exception as e:
                        error_msg = f"Runtime Error: {{str(e)}}\\n{{traceback.format_exc()}}"
                        results.append({{'passed': False, 'error': error_msg}})
                else:
                    error_msg = f"Runtime Error: {{str(e)}}\\n{{traceback.format_exc()}}"
                    results.append({{'passed': False, 'error': error_msg}})
            except Exception as e:
                error_msg = f"Runtime Error: {{str(e)}}\\n{{traceback.format_exc()}}"
                results.append({{'passed': False, 'error': error_msg}})
                
        except Exception as e:
            error_msg = f"Test Case Error: {{str(e)}}\\n{{traceback.format_exc()}}"
            results.append({{'passed': False, 'error': error_msg}})
    
    # Print results as JSON
    print(json.dumps(results))

if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(json.dumps([{{'passed': False, 'error': f"Fatal error: {{str(e)}}\\n{{traceback.format_exc()}}"}}]))
        sys.exit(1)
"""
            return test_code
        except Exception as e:
            self.logger.error(f"Error preparing Python tests: {str(e)}")
            raise
    
    def _prepare_javascript_tests(self, user_code: str, test_cases: List[str], starter_code: str) -> str:
        """Prepare JavaScript code with test cases"""
        try:
            # Extract function name from starter code
            func_name = re.search(r'function\s+(\w+)\s*\(', starter_code).group(1)
            
            test_code = f"""
{user_code}

function runTests() {{
    const testCases = {json.dumps(test_cases)};
    const results = [];
    
    testCases.forEach((testCase, i) => {{
        try {{
            // Parse input
            const inputs = JSON.parse(testCase.split('\\n')[0]);
            
            // Run test
            let result;
            if (Array.isArray(inputs)) {{
                result = {func_name}(...inputs);
            }} else {{
                result = {func_name}(inputs);
            }}
            
            // Format result
            const resultStr = JSON.stringify(result);
            console.log(`Test case ${{i + 1}}: ${{resultStr}}`);
            results.push({{ passed: true, output: resultStr }});
            
        }} catch (e) {{
            console.error(`Error in test case ${{i + 1}}: ${{e.message}}\\n${{e.stack}}`);
            results.push({{ passed: false, error: e.message }});
        }}
    }});
    
    console.log('\\nTest Results:');
    console.log(JSON.stringify(results));
}}

try {{
    runTests();
}} catch (e) {{
    console.error(`Fatal error: ${{e.message}}\\n${{e.stack}}`);
    process.exit(1);
}}
"""
            return test_code
        except Exception as e:
            self.logger.error(f"Error preparing JavaScript tests: {str(e)}")
            raise
    
    def _prepare_java_tests(self, user_code: str, test_cases: List[str], starter_code: str) -> str:
        """Prepare Java code with test cases"""
        try:
            # Extract class name from user code
            class_name = re.search(r'class\s+(\w+)\s*\{', user_code).group(1)
            
            # Extract method name from starter code
            method_name = re.search(r'public\s+\w+\s+(\w+)\s*\(', starter_code).group(1)
            
            test_code = f"""
import java.util.*;
import com.google.gson.Gson;
import java.io.PrintWriter;
import java.io.StringWriter;

{user_code}

public class Main {{
    public static void main(String[] args) {{
        try {{
            String[] testCases = {json.dumps(test_cases)};
            List<Map<String, Object>> results = new ArrayList<>();
            {class_name} solution = new {class_name}();
            Gson gson = new Gson();
            
            for (int i = 0; i < testCases.length; i++) {{
                try {{
                    // Parse input
                    String input = testCases[i].split("\\n")[0];
                    Object[] inputs = gson.fromJson(input, Object[].class);
                    
                    // Run test
                    Object result = solution.{method_name}(inputs);
                    
                    // Format result
                    String resultStr = gson.toJson(result);
                    System.out.println("Test case " + (i + 1) + ": " + resultStr);
                    
                    Map<String, Object> testResult = new HashMap<>();
                    testResult.put("passed", true);
                    testResult.put("output", resultStr);
                    results.add(testResult);
                    
                }} catch (Exception e) {{
                    StringWriter sw = new StringWriter();
                    e.printStackTrace(new PrintWriter(sw));
                    String stackTrace = sw.toString();
                    
                    System.err.println("Error in test case " + (i + 1) + ": " + e.getMessage());
                    System.err.println(stackTrace);
                    
                    Map<String, Object> testResult = new HashMap<>();
                    testResult.put("passed", false);
                    testResult.put("error", e.getMessage());
                    results.add(testResult);
                }}
            }}
            
            System.out.println("\\nTest Results:");
            System.out.println(gson.toJson(results));
            
        }} catch (Exception e) {{
            StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            String stackTrace = sw.toString();
            
            System.err.println("Fatal error: " + e.getMessage());
            System.err.println(stackTrace);
            System.exit(1);
        }}
    }}
}}
"""
            return test_code
        except Exception as e:
            self.logger.error(f"Error preparing Java tests: {str(e)}")
            raise
    
    def _run_code(self, file_path: str, language: str) -> Dict[str, Any]:
        """Run code with resource limits and timeout"""
        try:
            process = None
            try:
                if language == 'python':
                    cmd = ['python', file_path]
                elif language == 'javascript':
                    cmd = ['node', file_path]
                elif language == 'java':
                    # Compile first
                    class_name = os.path.splitext(os.path.basename(file_path))[0]
                    subprocess.run(['javac', '-cp', '.:gson.jar', file_path], check=True)
                    cmd = ['java', '-cp', '.:gson.jar', class_name]

                # Create process with timeout
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                try:
                    stdout, stderr = process.communicate(timeout=self.test_timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    return {
                        'success': False,
                        'error': 'Code execution timed out'
                    }

                # Check memory usage
                if process.returncode == 0:
                    try:
                        proc = psutil.Process(process.pid)
                        if proc.memory_info().rss > self.memory_limit:
                            return {
                                'success': False,
                                'error': 'Code exceeded memory limit'
                            }
                    except psutil.NoSuchProcess:
                        pass

                # Check output size
                if len(stdout) > self.max_output_size:
                    return {
                        'success': False,
                        'error': 'Output exceeded size limit'
                    }

                # Parse output
                if process.returncode == 0:
                    output_lines = stdout.strip().split('\n')
                    try:
                        # Find the last line that looks like a JSON array
                        results_line = None
                        for line in reversed(output_lines):
                            if line.strip().startswith('[') and line.strip().endswith(']'):
                                results_line = line
                                break
                        
                        if results_line:
                            test_results = json.loads(results_line)
                            return {
                                'success': True,
                                'results': test_results
                            }
                        else:
                            return {
                                'success': False,
                                'error': 'No test results found in output'
                            }
                    except json.JSONDecodeError:
                        return {
                            'success': False,
                            'error': 'Failed to parse test results'
                        }
                else:
                    return {
                        'success': False,
                        'error': stderr or 'Code execution failed'
                    }

            finally:
                if process:
                    try:
                        process.kill()
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"Error running code: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _set_resource_limits(self):
        """Set resource limits for the process"""
        try:
            # Set memory limit
            # resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
            # Set CPU time limit
            # resource.setrlimit(resource.RLIMIT_CPU, (self.test_timeout, self.test_timeout))
            pass  # Windows does not support resource module
        except Exception as e:
            logging.error(f"Error setting resource limits: {str(e)}")

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for the given language"""
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'java': '.java'
        }
        return extensions.get(language, '.txt')

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
            # If not JSON, try to convert to int for sqrt problem
            try:
                input_data = int(test_input.strip('"\''))
            except ValueError:
                # If not an int, use as is (for strings, etc)
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
                else:
                    raise ValueError("Could not extract function name from starter code")
            elif language == 'javascript':
                match = re.search(r'function\s+(\w+)\s*\(', starter_code)
                if match:
                    function_name = match.group(1)
                    test_code = f"""
{code}

try {{
    // Parse input
    let input;
    try {{
        input = JSON.parse('{test_case}');
    }} catch (e) {{
        // If not JSON, try to convert to number for sqrt problem
        input = Number('{test_case}'.trim());
        if (isNaN(input)) {{
            // If not a number, use as is
            input = '{test_case}'.trim();
        }}
    }}
    
    // Run test
    const result = {function_name}(input);
    console.log(JSON.stringify(result));
}} catch (e) {{
    console.error(`Runtime error: ${{e.message}}\\n${{e.stack}}`);
}}
"""
                    return test_code
                else:
                    raise ValueError("Could not extract function name from starter code")
            elif language == 'java':
                class_match = re.search(r'class\s+(\w+)\s*\{', code)
                method_match = re.search(r'public\s+\w+\s+(\w+)\s*\(', starter_code)
                if class_match and method_match:
                    class_name = class_match.group(1)
                    method_name = method_match.group(1)
                    test_code = f"""
{code}

public class Main {{
    public static void main(String[] args) {{
        try {{
            {class_name} solution = new {class_name}();
            
            // Parse input
            String input = "{test_case}";
            Object result;
            try {{
                // Try to parse as JSON
                com.google.gson.JsonParser parser = new com.google.gson.JsonParser();
                com.google.gson.JsonElement element = parser.parse(input);
                if (element.isJsonPrimitive()) {{
                    if (element.getAsJsonPrimitive().isNumber()) {{
                        result = solution.{method_name}(element.getAsInt());
                    }} else {{
                        result = solution.{method_name}(input);
                    }}
                }} else {{
                    result = solution.{method_name}(input);
                }}
            }} catch (Exception e) {{
                // If not JSON, try to convert to int for sqrt problem
                try {{
                    int intInput = Integer.parseInt(input.trim());
                    result = solution.{method_name}(intInput);
                }} catch (NumberFormatException ne) {{
                    // If not an int, use as is
                    result = solution.{method_name}(input.trim());
                }}
            }}
            
            // Print result
            System.out.println(new com.google.gson.Gson().toJson(result));
            
        }} catch (Exception e) {{
            System.err.println("Runtime error: " + e.getMessage());
            e.printStackTrace();
        }}
    }}
}}
"""
                    return test_code
                else:
                    raise ValueError("Could not extract class/method name from code")
            else:
                raise ValueError(f"Language {language} is not supported")
        except Exception as e:
            self.logger.error(f"Error preparing code with test: {str(e)}")
            raise 