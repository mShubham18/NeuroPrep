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

def question_generation_pipeline(path:str, progress_callback=None)->list:
    """
    Generate questions for all interview rounds
    
    Args:
        path (str): Path to the resume file
        progress_callback (callable, optional): Function to call with progress updates
        
    Returns:
        tuple: (introduction_questions, aptitude_questions, technical_questions, coding_questions, hr_questions)
    """
    def log_progress(message):
        if progress_callback:
            progress_callback(message)
        print(message, flush=True)

    log_progress("Resume and Metrics extraction Initiated")
    resume_content = parse_to_text(path)
    metrics_dict = extract_metrics(resume_content)
    log_progress("Resume and Metrics extraction Completed")
    
    log_progress("\nInitiating Question Generation")

    log_progress("Generating Introduction Questions...")
    introduction_questions_list = generate_Introduction(metrics_dict)
    log_progress("✓ Introduction questions generation completed")

    log_progress("Generating Aptitude Questions...")
    aptitude_questions_dict = generate_Aptitude(metrics_dict)
    log_progress("✓ Aptitude questions generation completed")

    log_progress("Generating Technical Questions...")
    technical_questions_dict = generate_Technical(metrics_dict)
    log_progress("✓ Technical questions generation completed")

    log_progress("Generating Coding Questions...")
    coding_questions_markdown_list = []
    for i in range(0,3):
        log_progress(f"  Generating coding question {i+1}/3...")
        question = generate_Coding(metrics_dict)
        coding_questions_markdown_list.append(question)
    log_progress("✓ Coding questions generation completed")

    log_progress("Generating HR Questions...")
    hr_questions_list = generate_HR(metrics_dict)
    log_progress("✓ HR questions generation completed")
    
    log_progress("\nAll questions generated successfully!")
    sys.stdout.flush()
    
    return introduction_questions_list, aptitude_questions_dict, technical_questions_dict, coding_questions_markdown_list, hr_questions_list