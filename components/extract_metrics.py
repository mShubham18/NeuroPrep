#from components.parse_resume import parse_to_text
from utils.main_utils import metrics_titles
import re
from typing import Dict

def extract_metrics(resume_text: str) -> Dict:
    """Extract key metrics from resume text."""
    metrics = {
        'skills': [],
        'experience_years': 0,
        'education': [],
        'languages': [],
        'tools': []
    }
    
    # Extract skills (looking for common programming languages and technologies)
    skill_patterns = [
        r'Python|Java|JavaScript|C\+\+|SQL|HTML|CSS|React|Node\.js|Docker|AWS',
        r'Machine Learning|AI|Data Science|Web Development|DevOps|Cloud Computing'
    ]
    
    for pattern in skill_patterns:
        skills = re.findall(pattern, resume_text, re.IGNORECASE)
        metrics['skills'].extend(skills)
    
    # Extract years of experience
    exp_pattern = r'(\d+)[\+]?\s*(?:years?|yrs?)'
    exp_matches = re.findall(exp_pattern, resume_text, re.IGNORECASE)
    if exp_matches:
        metrics['experience_years'] = max(map(int, exp_matches))
    
    # Extract education
    edu_pattern = r'(?:B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc|Ph\.?D|MBA)'
    education = re.findall(edu_pattern, resume_text)
    metrics['education'] = education
    
    # Extract programming languages
    lang_pattern = r'(?:Python|Java|C\+\+|JavaScript|Ruby|Go|Rust|Swift|Kotlin)'
    languages = re.findall(lang_pattern, resume_text, re.IGNORECASE)
    metrics['languages'] = list(set(languages))
    
    # Extract tools and frameworks
    tools_pattern = r'(?:Git|Docker|Kubernetes|AWS|Azure|React|Angular|Vue|Django|Flask|Spring)'
    tools = re.findall(tools_pattern, resume_text, re.IGNORECASE)
    metrics['tools'] = list(set(tools))
    
    return metrics

