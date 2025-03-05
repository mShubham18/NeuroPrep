import concurrent.futures
from components.parse_resume import parse_to_text
from components.extract_metrics import extract_metrics
from components.generating_questions import (
    generate_Introduction,
    generate_Aptitude,
    generate_Technical,
    generate_HR
)
from services.question_service import QuestionService
import sys
import logging

logger = logging.getLogger(__name__)

def question_generation_pipeline(path: str, progress_callback=None) -> list:
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
        logger.info(message)

    try:
        log_progress("Resume and Metrics extraction Initiated")
        
        # Parse resume
        try:
            resume_content = parse_to_text(path)
            if not resume_content:
                raise ValueError("Failed to extract text from resume")
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise ValueError(f"Failed to parse resume: {str(e)}")
            
        # Extract metrics
        try:
            metrics_dict = extract_metrics(resume_content)
            if not metrics_dict:
                raise ValueError("Failed to extract metrics from resume")
        except Exception as e:
            logger.error(f"Error extracting metrics: {str(e)}")
            raise ValueError(f"Failed to extract metrics: {str(e)}")
            
        log_progress("Resume and Metrics extraction Completed")
        
        log_progress("\nInitiating Question Generation")
        
        # Initialize question service for LeetCode integration
        question_service = QuestionService()
        
        # Create a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            try:
                # Submit all tasks
                intro_future = executor.submit(generate_Introduction, metrics_dict)
                aptitude_future = executor.submit(generate_Aptitude, metrics_dict)
                technical_future = executor.submit(generate_Technical, metrics_dict)
                hr_future = executor.submit(generate_HR, metrics_dict)
                
                # Get coding questions from LeetCode
                coding_future = executor.submit(
                    question_service.get_questions_by_difficulty,
                    metrics_dict.get('technical_skill_emphasis', '').split(','),
                    metrics_dict.get('experience_level_categorization', 'beginner').split(':')[0].lower()
                )
                
                # Wait for all tasks to complete with timeout
                introduction_questions_list = intro_future.result(timeout=60)
                log_progress("✓ Introduction questions generation completed")
                
                aptitude_questions_dict = aptitude_future.result(timeout=60)
                log_progress("✓ Aptitude questions generation completed")
                
                technical_questions_dict = technical_future.result(timeout=60)
                log_progress("✓ Technical questions generation completed")
                
                coding_questions = coding_future.result(timeout=60)
                log_progress("✓ Coding questions fetched from LeetCode")
                
                hr_questions_list = hr_future.result(timeout=60)
                log_progress("✓ HR questions generation completed")
                
            except concurrent.futures.TimeoutError as e:
                logger.error("Question generation timed out")
                raise ValueError("Question generation timed out. Please try again.")
            except Exception as e:
                logger.error(f"Error in question generation: {str(e)}")
                raise ValueError(f"Failed to generate questions: {str(e)}")
        
        # Validate results
        if not all([introduction_questions_list, aptitude_questions_dict, 
                   technical_questions_dict, coding_questions, hr_questions_list]):
            raise ValueError("Some questions failed to generate")
            
        log_progress("\nAll questions generated successfully!")
        sys.stdout.flush()
        
        return introduction_questions_list, aptitude_questions_dict, technical_questions_dict, coding_questions, hr_questions_list
        
    except Exception as e:
        logger.error(f"Error in question generation pipeline: {str(e)}")
        raise