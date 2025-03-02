from components.model_configuration import model_config
#from components.parse_resume import parse_to_text
from utils.main_utils import metrics_titles
model = model_config()
def extract_metrics(resume_content:str)->dict:
    prompt = f"""I am creating a web app platform that fetches user resumes and provides a mock interview consisting of Aptitude & Reasoning, Technical, and HR rounds. I need you to generate detailed insights that I can feed into an LLM to create question content for the exam.

    Provide structured insights such as experience level, test difficulty, skill set, and other relevant factors that will help structure the exam. Be as detailed and numeric as possible (e.g., use "5/10" instead of "five out of ten").

    Format the response as a comma-separated list, using "||" to separate different metrics. Do not include any titles, introductions, or salutations—just the insights in the format below:

    Metrics:

    Difficulty
    Experience
    Skillset
    Aptitude Focus
    Technical Focus
    HR Focus
    Experience Level Categorization
    Technical Skill Emphasis
    Domain Knowledge Emphasis
    Aptitude Test Skill Split
    Technical Test Skill Split
    Question Format Diversity
    Skill Proficiency Levels
    Skill Importance Weights
    Contextual Question Scenarios
    Test Time Allocation
    Code Writing Emphasis
    Programming Language Prioritization
    HR Round Focus Areas
    Behavioral Competencies Tested
    Situational Judgment Scenarios
    Instructions:

    Do not include any question types.
    Do not use any special symbols beyond commas and "||" as separators.
    Keep the response concise and structured.
    Here is the resume content: {resume_content}"""
    response = model.generate_content(prompt)
    metrics_info=list((response.text).split("||"))

    metrics_dict = {title:metric.split("\n")[0] for title,metric in zip(metrics_titles,metrics_info)}
    return metrics_dict

