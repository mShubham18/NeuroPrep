from components.parse_resume import parse_to_text
from components.extract_metrics import extract_metrics
from components.generating_questions import (
    generate_Introduction,
    generate_Aptitude,
    generate_Technical,
    generate_Coding,
    generate_HR
)
import sys

def question_generation_pipeline(path:str)->list:
    print("Resume and Metrics extraction Initiated", flush=True)
    resume_content = parse_to_text(path)
    metrics_dict = extract_metrics(resume_content)
    print("Resume and Metrics extraction Completed", flush=True)
    print("\nInitiating Question Generation", flush=True)

    print("Generating Introduction Questions...", flush=True)
    introduction_questions_list = generate_Introduction(metrics_dict)
    print("✓ Introduction questions generation completed", flush=True)

    print("Generating Aptitude Questions...", flush=True)
    aptitude_questions_dict = generate_Aptitude(metrics_dict)
    print("✓ Aptitude questions generation completed", flush=True)

    print("Generating Technical Questions...", flush=True)
    technical_questions_dict = generate_Technical(metrics_dict)
    print("✓ Technical questions generation completed", flush=True)

    print("Generating HR Questions...", flush=True)
    hr_questions_list = generate_HR(metrics_dict)
    print("✓ HR questions generation completed", flush=True)

    print("Generating Coding Questions...", flush=True)
    coding_questions_markdown_list = []
    for i in range(0,3):
        print(f"  Generating coding question {i+1}/3...", flush=True)
        question = generate_Coding(metrics_dict)
        coding_questions_markdown_list.append(question)
    print("✓ Coding questions generation completed", flush=True)
    
    print("\nAll questions generated successfully!", flush=True)
    sys.stdout.flush()
    
    return introduction_questions_list, aptitude_questions_dict, technical_questions_dict, coding_questions_markdown_list, hr_questions_list