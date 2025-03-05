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
import traceback
from typing import List, Any

{user_code}

def run_tests():
    test_cases = {json.dumps(test_cases)}
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # Parse input
            inputs = test_case.split('\\n')[0]
            inputs = ast.literal_eval(inputs)
            
            # Convert inputs to proper format
            if isinstance(inputs, list):
                result = {func_name}(inputs)
            elif isinstance(inputs, tuple):
                result = {func_name}(*inputs)
            else:
                result = {func_name}(inputs)
            
            # Format result for comparison
            result_str = str(result)
            print(f"Test case {{i}}: {{result_str}}")
            results.append({{'passed': True, 'output': result_str}})
            
        except Exception as e:
            error_msg = f"{{str(e)}}\\n{{''.join(traceback.format_tb(e.__traceback__))}}"
            print(f"Error in test case {{i}}: {{error_msg}}", file=sys.stderr)
            results.append({{'passed': False, 'error': error_msg}})
    
    print("\\nTest Results:")
    print(json.dumps(results))

if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(f"Fatal error: {{str(e)}}", file=sys.stderr)
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
            # Set up process with resource limits
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

                # Create process with resource limits
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=lambda: self._set_resource_limits()
                )

                # Monitor process
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
                    results_line = next(line for line in reversed(output_lines) if line.startswith('['))
                    test_results = json.loads(results_line)
                    return {
                        'success': True,
                        'results': test_results
                    }
                else:
                    return {
                        'success': False,
                        'error': stderr
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