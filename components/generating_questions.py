from components.model_configuration import model_config
import markdown

def generate_Introduction(metrics_dict:dict)->list:
    prompt = f"""You are an AI interviewer generating introduction questions for a job interview.

    ### STRICT OUTPUT FORMAT RULES:
    1. Generate EXACTLY 5 questions (no more, no less)
    2. Each question must be separated by exactly "||"
    3. First question MUST be a greeting
    4. NO explanations, NO comments, NO numbering
    5. NO empty questions or extra spaces
    6. NO quotation marks around questions

    ### QUESTION GUIDELINES:
    - Start with "Hello, how are you?"
    - Keep questions professional and progressive
    - Focus on making the candidate comfortable
    - Avoid technical topics
    - Treat this as a real interview (don't mention it being a mock interview)

    ### EXAMPLE OUTPUT FORMAT:
    Hello, how are you? || Could you briefly introduce yourself? || What made you interested in this position? || What are your career goals? || Why do you think you would be a good fit for this role?

    ### CONTEXT:
    {metrics_dict}

    Generate exactly 5 questions following the format strictly:"""
    
    model = model_config()
    response = model.generate_content(prompt)
    questions_list = response.text.strip().split("||")
    questions_list = [question.strip() for question in questions_list]
    
    # Ensure exactly 5 questions
    if len(questions_list) < 5:
        default_questions = [
            "Hello, how are you?",
            "Could you briefly introduce yourself?",
            "What made you interested in this position?",
            "What are your career goals?",
            "Why do you think you would be a good fit for this role?"
        ]
        questions_list = default_questions[:5]
    elif len(questions_list) > 5:
        questions_list = questions_list[:5]
    
    return questions_list

def generate_Aptitude(metrics_dict:dict)->dict:
    prompt = f"""You are an AI generating MCQ-based aptitude questions for a mock interview exam.  

    **Instructions:**  
    - Use only the provided **metrics** to create **30 MCQ aptitude questions**.  
    - Questions MUST be from these categories ONLY:
        * Numerical Ability (arithmetic, percentages, ratios)
        * Logical Reasoning (patterns, sequences, analogies)
        * Verbal Ability (vocabulary, grammar, comprehension)
        * Data Interpretation (graphs, tables, charts)
    - NO programming or technical questions
    - Format the output **exactly** as shown below, with `||` separating each question.  
    - Each question **must** follow this structure:  
      **Question text // option1, option2, option3, option4&answer**  
    - No explanations, no extra text, just the formatted questions.  

    **Example Output:**  
    If 2 workers can complete a task in 6 days, how many days will it take 3 workers? // 2 days, 3 days, 4 days, 5 days&4 days || What comes next in the sequence: 2,4,8,16,? // 24, 32, 36, 40&32  

    **Metrics for generating questions:**  
    {metrics_dict}  

    **Output the questions now:**"""
    model = model_config()
    response = model.generate_content(prompt)
    questions = response.text.strip().split("||")
    aptitude_questions_dict = {}
    for line in questions:
        try:
            question_list = line.strip().split("//")
            if len(question_list) == 2:
                question = question_list[0].strip()
                options_and_answer = question_list[1].strip()
                options = options_and_answer.split("&")[0].strip()
                answer = options_and_answer.split("&")[1].strip()
                aptitude_questions_dict[question] = [options, answer]
        except:
            continue
    return aptitude_questions_dict

def generate_Technical(metrics_dict:dict)->dict:
    prompt = f"""You are an AI assistant generating **30 multiple-choice questions (MCQs)** for a **mock technical interview**.

    ### **Important Instructions:**
    - Only generate questions related to **System Design, OS, DBMS, and Computer Networks**.
    - **Strictly follow the output format** with **no extra explanations, no numbering, and no missing values**.
    - Each question **must have exactly four answer options**.
    - Separate each question using `||` (double pipe).
    - Each question must follow this format: Question text // option1, option2, option3, option4&answer
    - Use `//` (double forward slashes) to separate the question text from the choices.

    ---

    ### **Output Format Example:**
    What is the primary key in a database? // A unique identifier, A duplicate record, A null value, A foreign key&A unique identifier||
    What does an operating system do? // Manages hardware, Compiles code, Runs JavaScript, Controls database records&Manages hardware

    ### **Here are the question generation metrics:**
    {metrics_dict}

    Now, generate exactly **30 MCQs** following the format strictly. Ensure all questions and answers are complete and correctly formatted."""
    model = model_config()
    response = model.generate_content(prompt)
    questions = response.text.strip().split("||")
    technical_questions_dict = {}
    for line in questions:
        try:
            question_list = line.strip().split("//")
            if len(question_list) == 2:
                question = question_list[0].strip()
                options_and_answer = question_list[1].strip()
                options = options_and_answer.split("&")[0].strip()
                answer = options_and_answer.split("&")[1].strip()
                technical_questions_dict[question] = [options, answer]
        except:
            continue
    return technical_questions_dict

def generate_Coding(metrics_dict:dict)->str:
    prompt = f"""You are an AI generating a coding question in LeetCode format.

    ### STRICT OUTPUT FORMAT:
    1. Question must be in Markdown format
    2. Include: Title, Difficulty, Problem Statement, Examples, Constraints
    3. NO solutions, NO hints, NO explanations
    4. NO comments or additional formatting

    ### EXAMPLE FORMAT:
    # Two Sum
    **Difficulty**: Easy

    Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

    **Examples:**
    Input: nums = [2,7,11,15], target = 9
    Output: [0,1]
    Explanation: Because nums[0] + nums[1] == 9, we return [0, 1]

    **Constraints:**
    - 2 <= nums.length <= 104
    - -109 <= nums[i] <= 109
    - -109 <= target <= 109

    ### CONTEXT:
    {metrics_dict}

    Generate one unique coding question following the format strictly:"""
    
    model = model_config()
    response = model.generate_content(prompt)
    markdown_text = response.text
    html_content = markdown.markdown(markdown_text)
    return html_content

def generate_HR(metrics_dict:dict)->list:
    prompt = f"""You are an AI interviewer generating HR questions for the final round of a job interview.

    ### STRICT OUTPUT FORMAT RULES:
    1. Generate EXACTLY 7 questions (no more, no less)
    2. Each question must be separated by exactly "||"
    3. NO explanations, NO comments, NO numbering
    4. NO empty questions or extra spaces
    5. NO quotation marks around questions

    ### QUESTION GUIDELINES:
    - Focus on behavioral and situational questions
    - Include questions about:
      * Past experiences
      * Problem-solving abilities
      * Team collaboration
      * Conflict resolution
      * Future aspirations
    - Keep questions professional and relevant to the candidate's experience

    ### EXAMPLE OUTPUT FORMAT:
    Tell me about a challenging project you worked on. || How do you handle conflicts in a team? || Describe a situation where you demonstrated leadership. || What are your salary expectations? || Where do you see yourself in five years? || How do you handle work pressure? || What questions do you have for us?

    ### CONTEXT:
    {metrics_dict}

    Generate exactly 7 questions following the format strictly:"""
    
    model = model_config()
    response = model.generate_content(prompt)
    questions_list = response.text.strip().split("||")
    questions_list = [question.strip() for question in questions_list]
    
    # Ensure exactly 7 questions
    if len(questions_list) < 7:
        default_questions = [
            "Tell me about a challenging project you worked on.",
            "How do you handle conflicts in a team?",
            "Describe a situation where you demonstrated leadership.",
            "What are your salary expectations?",
            "Where do you see yourself in five years?",
            "How do you handle work pressure?",
            "What questions do you have for us?"
        ]
        questions_list = default_questions[:7]
    elif len(questions_list) > 7:
        questions_list = questions_list[:7]
    
    return questions_list