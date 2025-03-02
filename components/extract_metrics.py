from components.model_configuration import model_config
from components.parse_resume import parse_to_text
model = model_config()
def extract_metrics(path:str)->dict:
    resume_content=parse_to_text(path)
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
    metrics_titles = [
    "difficulty",
    "experience",
    "skillset",
    "aptitude_focus",
    "technical_focus",
    "hr_focus",
    "experience_level_categorization",
    "technical_skill_emphasis",
    "domain_knowledge_emphasis",
    "aptitude_test_skill_split",
    "technical_test_skill_split",
    "question_format_diversity",
    "skill_proficiency_levels",
    "skill_importance_weights",
    "contextual_question_scenarios",
    "test_time_allocation",
    "code_writing_emphasis",
    "programming_language_prioritization",
    "hr_round_focus_areas",
    "behavioral_competencies_tested",
    "situational_judgment_scenarios"
    ]

    metrics_dict = {title:metric for title,metric in zip(metrics_titles,metrics_info)}
    return metrics_dict

