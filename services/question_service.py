import requests
import json
import os
from dotenv import load_dotenv
import time
from functools import lru_cache

load_dotenv()

class QuestionService:
    def __init__(self):
        self.api_url = "https://leetcode.com/api/problems/all/"
        self.graphql_url = "https://leetcode.com/graphql"
        self.question_url = "https://leetcode.com/problems/{}/description/"
        self.cache_ttl = 3600  # 1 hour cache
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 second between requests
        self.max_retries = 3  # Maximum number of retries for API calls
        
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
                if attempt == self.max_retries - 1:
                    print(f"Failed after {self.max_retries} attempts: {str(e)}")
                    return None
                time.sleep(1)  # Wait before retrying
        return None

    def get_questions_by_difficulty(self, skills, experience_level):
        """
        Get questions from LeetCode based on skills and experience level
        Args:
            skills (list): List of programming skills
            experience_level (str): Experience level (beginner/intermediate/advanced)
        Returns:
            list: List of questions with different difficulty levels
        """
        try:
            # Get default questions first
            default_questions = self._get_default_questions()
            
            # Clean up and validate inputs
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split(',') if s.strip()]
            elif not skills:
                skills = []
                
            experience_level = experience_level.lower() if experience_level else 'beginner'
            
            # Map experience level to difficulty
            difficulty_map = {
                'beginner': ['Easy'],
                'intermediate': ['Easy', 'Medium'],
                'advanced': ['Medium', 'Hard']
            }
            
            # Get all problems from LeetCode
            response = self._make_request('GET', self.api_url)
            if not response:
                print("Failed to fetch problems from LeetCode API")
                return default_questions
                
            problems = response.json().get('stat_status_pairs', [])
            if not problems:
                print("No problems returned from LeetCode API")
                return default_questions
            
            # Filter problems based on difficulty and skills
            filtered_problems = []
            for problem in problems:
                try:
                    # Get problem details
                    stat = problem.get('stat', {})
                    difficulty = problem.get('difficulty', {}).get('level', 1)
                    difficulty_name = ['Easy', 'Medium', 'Hard'][difficulty - 1]
                    
                    # Check if difficulty matches experience level
                    if difficulty_name in difficulty_map.get(experience_level, ['Easy']):
                        # Get problem title and URL
                        title = stat.get('question__title')
                        slug = stat.get('question__title_slug')
                        
                        if title and slug:
                            url = self.question_url.format(slug)
                            
                            # Get problem content and metadata
                            problem_data = self._get_problem_data(slug)
                            
                            if problem_data:
                                filtered_problems.append({
                                    'id': stat.get('question_id', len(filtered_problems) + 1),
                                    'title': title,
                                    'difficulty': difficulty_name,
                                    'url': url,
                                    'content': problem_data['content'],
                                    'test_cases': problem_data['test_cases'],
                                    'starter_code': problem_data['starter_code'],
                                    'acceptance_rate': problem.get('ac_rate', 0),
                                    'total_submissions': stat.get('total_submitted', 0)
                                })
                                
                                # Break if we have enough questions
                                if len(filtered_problems) >= 3:
                                    break
                except Exception as e:
                    print(f"Error processing problem: {str(e)}")
                    continue
            
            # Return filtered problems if we have any, otherwise return default questions
            return filtered_problems if filtered_problems else default_questions
                
        except Exception as e:
            print(f"Error in get_questions_by_difficulty: {str(e)}")
            return self._get_default_questions()
    
    def _get_problem_data(self, slug):
        """Get problem content, test cases, and starter code using GraphQL API"""
        try:
            query = """
            query getQuestionData($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    content
                    sampleTestCase
                    exampleTestcases
                    codeSnippets {
                        langSlug
                        code
                    }
                }
            }
            """
            
            response = self._make_request(
                'POST',
                self.graphql_url,
                json={
                    'query': query,
                    'variables': {'titleSlug': slug}
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if not response:
                print(f"Failed to fetch data for question {slug}")
                return None
            
            data = response.json().get('data', {}).get('question', {})
            if not data:
                print(f"No data returned for question {slug}")
                return None
            
            # Log the response for debugging
            print(f"API response for {slug}: {response.json()}")
            
            # Get starter code for supported languages
            starter_code = {}
            for snippet in data.get('codeSnippets', []):
                if snippet.get('langSlug') in ['python3', 'javascript', 'java']:
                    lang_map = {'python3': 'python', 'javascript': 'javascript', 'java': 'java'}
                    starter_code[lang_map[snippet['langSlug']]] = snippet.get('code', '')
            
            # Parse test cases
            test_cases = []
            example_tests = data.get('exampleTestcases', '')
            if example_tests:
                test_cases = [case.strip() for case in example_tests.split('\n') if case.strip()]
            
            # If no test cases found, try sample test case
            if not test_cases and data.get('sampleTestCase'):
                test_cases = [data['sampleTestCase'].strip()]
            
            # Ensure we have at least one test case
            if not test_cases:
                test_cases = ['[1,2,3]\n5']  # Default test case
            
            # Ensure starter_code and test_cases are not None
            starter_code = starter_code or {}
            test_cases = test_cases or ['[1,2,3]\n5']  # Default test case if none found
            
            return {
                'content': data.get('content', 'Problem content not available'),
                'test_cases': test_cases,
                'starter_code': starter_code
            }
                
        except Exception as e:
            print(f"Error fetching problem data for {slug}: {str(e)}")
            return None

    def _get_default_questions(self):
        """Return default questions in case of API failure"""
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