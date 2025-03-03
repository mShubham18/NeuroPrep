from components.parse_resume import parse_to_text
from components.extract_metrics import extract_metrics
from components.generating_questions import (
    generate_Introduction,
    generate_Aptitude,
    generate_Technical,
    generate_Coding,
    generate_HR
)

def question_generation_pipeline(path:str)->list:
    print("Resume and Metrics extraction Initiated")
    resume_content = parse_to_text(path)
    metrics_dict = extract_metrics(resume_content)
    print("Resume and Metrics extraction Completed")
    print("\n Initiating Question Generation")

    introduction_questions_list = generate_Introduction(metrics_dict)
    print("introduction_questions_list generation completed")

    aptitude_questions_dict = generate_Aptitude(metrics_dict)
    print("aptitude_questions_dict generation completed")

    technical_questions_dict = generate_Technical(metrics_dict)
    print("technical_questions_dict generation completed")

    hr_questions_list = generate_HR(metrics_dict)
    print("hr_questions_list generation completed")

    coding_questions_markdown_list = []
    for _ in range(0,3):
        question = generate_Coding(metrics_dict)
        coding_questions_markdown_list.append(question)
    if coding_questions_markdown_list:
        print("coding_questions_markdown_list generation completed")
    
    return introduction_questions_list,aptitude_questions_dict,technical_questions_dict,coding_questions_markdown_list,hr_questions_list