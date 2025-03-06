import requests
import json
import os
from dotenv import load_dotenv
import time
from functools import lru_cache
import re
import logging
import random
from typing import List, Dict, Any

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionService:
    def __init__(self):
        self.api_url = "https://leetcode.com/api/problems/all/"
        self.graphql_url = "https://leetcode.com/graphql"
        self.question_url = "https://leetcode.com/problems/{}/description/"
        self.cache_ttl = 3600  # 1 hour cache
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 second between requests
        self.max_retries = 3  # Maximum number of retries for API calls
        self.used_question_ids = set()  # Track used questions to avoid duplicates
        
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def _make_request(self, method, url, **kwargs):
        """Make an HTTP request with retries"""
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                response = requests.request(method, url, timeout=10, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed after {self.max_retries} attempts")
                    return None
                time.sleep(1)  # Wait before retrying
        return None

    def get_questions_by_difficulty(self, skills: List[str], experience_level: str) -> List[Dict[str, Any]]:
        """
        Get coding questions from LeetCode with proper randomization and difficulty distribution
        """
        try:
            # Map experience level to difficulty distribution
            difficulty_distribution = {
                'beginner': {'Easy': 0.7, 'Medium': 0.3, 'Hard': 0.0},
                'intermediate': {'Easy': 0.3, 'Medium': 0.5, 'Hard': 0.2},
                'advanced': {'Easy': 0.1, 'Medium': 0.4, 'Hard': 0.5}
            }
            
            # Get distribution for the experience level
            distribution = difficulty_distribution.get(experience_level.lower(), difficulty_distribution['beginner'])
            
            # Fetch all problems
            response = requests.get(self.api_url)
            if response.status_code != 200:
                logger.error("Failed to fetch problems from LeetCode API")
                return self._get_default_questions()
                
            problems = response.json().get('stat_status_pairs', [])
            logger.info(f"Found {len(problems)} total problems")
            
            # Filter and categorize problems
            categorized_problems = {
                'Easy': [],
                'Medium': [],
                'Hard': []
            }
            
            for problem in problems:
                stat = problem.get('stat', {})
                question_id = stat.get('question_id')
                title = stat.get('question__title')
                difficulty = self._get_difficulty(problem.get('difficulty', {}).get('level', 1))
                
                if (question_id and title and 
                    question_id not in self.used_question_ids and
                    difficulty in categorized_problems):
                    categorized_problems[difficulty].append({
                        'id': question_id,
                        'title': title,
                        'difficulty': difficulty
                    })
            
            # Select questions based on distribution
            selected_questions = []
            total_questions = 5  # Number of questions to fetch
            
            for difficulty, percentage in distribution.items():
                num_questions = int(total_questions * percentage)
                if num_questions > 0 and categorized_problems[difficulty]:
                    # Randomly select questions
                    selected = random.sample(categorized_problems[difficulty], 
                                          min(num_questions, len(categorized_problems[difficulty])))
                    selected_questions.extend(selected)
            
            # Fetch detailed data for selected questions
            final_questions = []
            for question in selected_questions:
                try:
                    # Get problem data
                    problem_data = self._get_problem_data(question['id'])
                    if not problem_data:
                        continue
                        
                    # Extract test cases and starter code
                    test_cases = problem_data.get('test_cases', [])
                    starter_code = problem_data.get('starter_code', {})
                    
                    if not test_cases:
                        logger.warning(f"No test cases found for {question['title']}")
                        continue
                        
                    if not starter_code:
                        logger.warning(f"No starter code found for {question['title']}")
                        continue
                    
                    # Add to final questions
                    question.update({
                        'content': problem_data.get('content', ''),
                        'test_cases': test_cases,
                        'starter_code': starter_code
                    })
                    final_questions.append(question)
                    self.used_question_ids.add(question['id'])
                    
                    logger.info(f"Added problem: {question['title']} ({question['difficulty']})")
                    
                except Exception as e:
                    logger.error(f"Error processing question {question['title']}: {str(e)}")
                    continue
            
            if not final_questions:
                logger.warning("No questions were successfully processed, using default questions")
                return self._get_default_questions()
                
            logger.info(f"Successfully processed {len(final_questions)} problems")
            return final_questions
            
        except Exception as e:
            logger.error(f"Error fetching questions: {str(e)}")
            return self._get_default_questions()
    
    def _get_difficulty(self, level: int) -> str:
        """Convert numeric difficulty to string"""
        difficulties = {1: 'Easy', 2: 'Medium', 3: 'Hard'}
        return difficulties.get(level, 'Easy')
    
    def _get_problem_data(self, question_id: int) -> Dict[str, Any]:
        """Fetch detailed problem data from LeetCode GraphQL API"""
        try:
            query = """
            query getQuestionDetail($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    questionId
                    title
                    content
                    difficulty
                    codeSnippets {
                        langSlug
                        code
                    }
                    exampleTestcases
                    sampleTestCase
                    metaData
                    hints
                }
            }
            """
            
            # Get title slug from question ID
            response = requests.get(self.api_url)
            if response.status_code != 200:
                logger.error("Failed to fetch problems list")
                return None
                
            problems = response.json().get('stat_status_pairs', [])
            for problem in problems:
                if problem.get('stat', {}).get('question_id') == question_id:
                    title_slug = problem.get('stat', {}).get('question__title_slug')
                    if not title_slug:
                        logger.error(f"No title slug found for question {question_id}")
                        continue
                        
                    # Make GraphQL request
                    variables = {'titleSlug': title_slug}
                    headers = {
                        'Content-Type': 'application/json',
                        'Referer': f'https://leetcode.com/problems/{title_slug}'
                    }
                    
                    response = requests.post(
                        self.graphql_url,
                        json={'query': query, 'variables': variables},
                        headers=headers
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to fetch question data for {title_slug}")
                        return None
                        
                    data = response.json()
                    question_data = data.get('data', {}).get('question', {})
                    
                    if not question_data:
                        logger.error(f"Empty question data for {title_slug}")
                        return None
                        
                    # Process content
                    content = question_data.get('content', '')
                    if not content:
                        logger.error(f"No content found for {title_slug}")
                        return None
                        
                    # Clean and format content
                    content = self._clean_html_content(content)
                    
                    # Process code snippets
                    code_snippets = question_data.get('codeSnippets', [])
                    starter_code = {}
                    for snippet in code_snippets:
                        lang = snippet.get('langSlug', '').lower()
                        code = snippet.get('code', '')
                        if lang and code:
                            # Map LeetCode language slugs to our supported languages
                            lang_map = {
                                'python3': 'python',
                                'python': 'python',
                                'javascript': 'javascript',
                                'java': 'java',
                                'cpp': 'cpp',
                                'c': 'c'
                            }
                            if lang in lang_map:
                                starter_code[lang_map[lang]] = code.strip()
                    
                    # Process test cases
                    test_cases = []
                    example_test_cases = question_data.get('exampleTestcases', '')
                    sample_test_case = question_data.get('sampleTestCase', '')
                    
                    # Try to get test cases from multiple sources
                    if example_test_cases:
                        test_cases.extend(example_test_cases.strip().split('\n'))
                    if sample_test_case and sample_test_case not in test_cases:
                        test_cases.append(sample_test_case.strip())
                    
                    # Extract test cases from content if needed
                    if not test_cases:
                        test_cases = self._extract_test_cases(content)
                    
                    # Get metadata
                    try:
                        metadata = json.loads(question_data.get('metaData', '{}'))
                    except:
                        metadata = {}
                    
                    return {
                        'id': question_id,
                        'title': question_data.get('title', ''),
                        'content': content,
                        'difficulty': question_data.get('difficulty', 'Easy'),
                        'starter_code': starter_code,
                        'test_cases': test_cases,
                        'hints': question_data.get('hints', []),
                        'metadata': metadata
                    }
            
            logger.error(f"Question {question_id} not found in problems list")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching problem data: {str(e)}")
            return None
    
    def _clean_html_content(self, content: str) -> str:
        """Clean and format HTML content from LeetCode"""
        try:
            # Remove unnecessary HTML tags but keep formatting
            content = re.sub(r'<pre>', '', content)
            content = re.sub(r'</pre>', '', content)
            content = re.sub(r'<strong>', '**', content)
            content = re.sub(r'</strong>', '**', content)
            content = re.sub(r'<em>', '*', content)
            content = re.sub(r'</em>', '*', content)
            content = re.sub(r'<code>', '`', content)
            content = re.sub(r'</code>', '`', content)
            content = re.sub(r'<sup>', '^', content)
            content = re.sub(r'</sup>', '', content)
            content = re.sub(r'<sub>', '_', content)
            content = re.sub(r'</sub>', '', content)
            content = re.sub(r'<[^>]+>', '', content)  # Remove any other HTML tags
            
            # Fix common formatting issues
            content = content.replace('&nbsp;', ' ')
            content = content.replace('&lt;', '<')
            content = content.replace('&gt;', '>')
            content = content.replace('&quot;', '"')
            content = content.replace('&apos;', "'")
            content = content.replace('&amp;', '&')
            
            # Normalize whitespace
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error cleaning content: {str(e)}")
            return content  # Return original content if cleaning fails
    
    def _extract_test_cases(self, content: str) -> List[str]:
        """Extract test cases from problem content"""
        try:
            if not content:
                logger.warning("Empty content provided for test case extraction")
                return ["[1, 2, 3]\n6"]
                
            test_cases = []
            
            # Pattern for example input/output pairs
            patterns = [
                r'Example \d+:?\s*Input:?\s*(.*?)\s*Output:?\s*(.*?)(?=Example|$)',
                r'Input:?\s*(.*?)\s*Output:?\s*(.*?)(?=Input:|$)',
                r'Sample Input:?\s*(.*?)\s*Sample Output:?\s*(.*?)(?=\n\n|$)',
                r'Input =\s*(.*?)\s*Output =\s*(.*?)(?=\n\n|$)',
                r'Input:\s*`(.*?)`\s*Output:\s*`(.*?)`'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.DOTALL)
                for match in matches:
                    input_data = match.group(1).strip()
                    output_data = match.group(2).strip()
                    if input_data and output_data:
                        # Clean the test case data
                        input_data = re.sub(r'`|\[|\]|\(|\)|\{|\}', '', input_data)
                        output_data = re.sub(r'`|\[|\]|\(|\)|\{|\}', '', output_data)
                        test_case = f"{input_data}\n{output_data}"
                        if test_case not in test_cases:
                            test_cases.append(test_case)
            
            if not test_cases:
                logger.warning("No test cases found in content")
                return ["[1, 2, 3]\n6"]
                
            return test_cases
            
        except Exception as e:
            logger.error(f"Error extracting test cases: {str(e)}")
            return ["[1, 2, 3]\n6"]
    
    def _extract_starter_code(self, code_definitions: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract starter code for different languages"""
        try:
            starter_code = {}
            for definition in code_definitions:
                language = definition.get('value', '').lower()
                code = definition.get('defaultCode', '')
                if language and code:
                    starter_code[language] = code
            return starter_code
        except Exception as e:
            logger.error(f"Error extracting starter code: {str(e)}")
            return {}
    
    def _get_default_questions(self):
        """Return default questions in case of API failure"""
        logger.info("Using default questions")
        return [
            {
                'id': 1,
                'title': 'Two Sum',
                'difficulty': 'Easy',
                'url': 'https://leetcode.com/problems/two-sum/description/',
                'content': '# Two Sum\n\nGiven an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.\n\n**Example 1:**\nInput: nums = [2,7,11,15], target = 9\nOutput: [0,1]\nExplanation: Because nums[0] + nums[1] == 9, we return [0, 1].\n\n**Constraints:**\n- 2 <= nums.length <= 104\n- -109 <= nums[i] <= 109\n- -109 <= target <= 109\n- Only one valid answer exists.',
                'test_cases': ['[2,7,11,15]\n9', '[3,2,4]\n6', '[3,3]\n6'],
                'starter_code': {
                    'python': 'def twoSum(nums: List[int], target: int) -> List[int]:\n    pass',
                    'javascript': 'function twoSum(nums, target) {\n    \n}',
                    'java': 'class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        \n    }\n}'
                }
            },
            {
                'id': 2,
                'title': 'Add Two Numbers',
                'difficulty': 'Medium',
                'url': 'https://leetcode.com/problems/add-two-numbers/description/',
                'content': '# Add Two Numbers\n\nYou are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit. Add the two numbers and return the sum as a linked list.\n\n**Example 1:**\nInput: l1 = [2,4,3], l2 = [5,6,4]\nOutput: [7,0,8]\nExplanation: 342 + 465 = 807.\n\n**Constraints:**\n- The number of nodes in each linked list is in the range [1, 100].\n- 0 <= Node.val <= 9\n- It is guaranteed that the list represents a number that does not have leading zeros.',
                'test_cases': ['[2,4,3]\n[5,6,4]', '[0]\n[0]', '[9,9,9,9]\n[9,9,9,9,9,9,9]'],
                'starter_code': {
                    'python': 'def addTwoNumbers(l1: ListNode, l2: ListNode) -> ListNode:\n    pass',
                    'javascript': 'function addTwoNumbers(l1, l2) {\n    \n}',
                    'java': 'class Solution {\n    public ListNode addTwoNumbers(ListNode l1, ListNode l2) {\n        \n    }\n}'
                }
            },
            {
                'id': 3,
                'title': 'Longest Substring Without Repeating Characters',
                'difficulty': 'Medium',
                'url': 'https://leetcode.com/problems/longest-substring-without-repeating-characters/description/',
                'content': '# Longest Substring Without Repeating Characters\n\nGiven a string s, find the length of the longest substring without repeating characters.\n\n**Example 1:**\nInput: s = "abcabcbb"\nOutput: 3\nExplanation: The answer is "abc", with the length of 3.\n\n**Constraints:**\n- 0 <= s.length <= 5 * 104\n- s consists of English letters, digits, symbols and spaces.',
                'test_cases': ['"abcabcbb"', '"bbbbb"', '"pwwkew"'],
                'starter_code': {
                    'python': 'def lengthOfLongestSubstring(s: str) -> int:\n    pass',
                    'javascript': 'function lengthOfLongestSubstring(s) {\n    \n}',
                    'java': 'class Solution {\n    public int lengthOfLongestSubstring(String s) {\n        \n    }\n}'
                }
            }
        ] 