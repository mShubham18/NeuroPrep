#from components.parse_resume import parse_to_text
from utils.main_utils import metrics_titles
import re
from typing import Dict
import logging

logger = logging.getLogger(__name__)

def extract_metrics(resume_text: str) -> Dict:
    """Extract key metrics from resume text."""
    if not resume_text or not resume_text.strip():
        logger.error("Empty resume text provided")
        raise ValueError("Empty resume text provided")
        
    metrics = {
        'skills': [],
        'experience_years': 0,
        'education': [],
        'languages': [],
        'tools': [],
        'technical_skill_emphasis': '',
        'experience_level_categorization': 'beginner:0-2'
    }
    
    try:
        # Extract skills with more comprehensive patterns
        skill_patterns = [
            # Programming Languages
            r'(?:Python|Java|JavaScript|C\+\+|C#|SQL|HTML|CSS|TypeScript|Ruby|Go|Rust|Swift|Kotlin|PHP|Perl|Shell|Bash)',
            # Frameworks and Libraries
            r'(?:React|Angular|Vue|Node\.js|Express|Django|Flask|Spring|Laravel|Symfony|ASP\.NET|jQuery|Bootstrap|Tailwind)',
            # Tools and Technologies
            r'(?:Git|Docker|Kubernetes|AWS|Azure|GCP|Jenkins|Ansible|Terraform|ELK|Prometheus|Grafana|Selenium|JUnit)',
            # Domains
            r'(?:Machine Learning|AI|Data Science|Web Development|DevOps|Cloud Computing|Mobile Development|UI/UX|Security|Testing)'
        ]
        
        for pattern in skill_patterns:
            skills = re.findall(pattern, resume_text, re.IGNORECASE)
            metrics['skills'].extend(skills)
        
        # Remove duplicates and sort
        metrics['skills'] = sorted(list(set(metrics['skills'])))
        
        # Extract years of experience with more flexible patterns
        exp_patterns = [
            r'(\d+)[\+]?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience)',
            r'experience\s*(?:of)?\s*(\d+)[\+]?\s*(?:years?|yrs?)',
            r'(\d+)[\+]?\s*(?:years?|yrs?)\s*(?:in)?\s*(?:software|development|engineering)'
        ]
        
        for pattern in exp_patterns:
            exp_matches = re.findall(pattern, resume_text, re.IGNORECASE)
            if exp_matches:
                metrics['experience_years'] = max(map(int, exp_matches))
                break
        
        # Extract education with more comprehensive patterns
        edu_patterns = [
            r'(?:B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc|Ph\.?D|MBA|B\.?Com|M\.?Com|B\.?A|M\.?A)',
            r'(?:Bachelor|Master|Doctorate|PhD|MBA)\s*(?:of|in)?\s*(?:Science|Engineering|Technology|Arts|Commerce)',
            r'(?:Computer Science|Information Technology|Software Engineering|Data Science|Business Administration)'
        ]
        
        for pattern in edu_patterns:
            education = re.findall(pattern, resume_text, re.IGNORECASE)
            metrics['education'].extend(education)
        
        # Remove duplicates and sort
        metrics['education'] = sorted(list(set(metrics['education'])))
        
        # Extract programming languages with more comprehensive patterns
        lang_patterns = [
            r'(?:Python|Java|C\+\+|C#|JavaScript|TypeScript|Ruby|Go|Rust|Swift|Kotlin|PHP|Perl|Shell|Bash)',
            r'(?:programming|development|coding)\s*(?:in|with)?\s*(?:Python|Java|C\+\+|JavaScript|Ruby|Go)'
        ]
        
        for pattern in lang_patterns:
            languages = re.findall(pattern, resume_text, re.IGNORECASE)
            metrics['languages'].extend(languages)
        
        # Remove duplicates and sort
        metrics['languages'] = sorted(list(set(metrics['languages'])))
        
        # Extract tools and frameworks with more comprehensive patterns
        tools_patterns = [
            r'(?:Git|Docker|Kubernetes|AWS|Azure|GCP|Jenkins|Ansible|Terraform|ELK|Prometheus|Grafana|Selenium|JUnit)',
            r'(?:using|working with|experience in)\s*(?:Git|Docker|AWS|Azure|Jenkins|Ansible)'
        ]
        
        for pattern in tools_patterns:
            tools = re.findall(pattern, resume_text, re.IGNORECASE)
            metrics['tools'].extend(tools)
        
        # Remove duplicates and sort
        metrics['tools'] = sorted(list(set(metrics['tools'])))
        
        # Set technical skill emphasis based on skills found
        if metrics['languages']:
            metrics['technical_skill_emphasis'] = ','.join(metrics['languages'])
        
        # Set experience level based on years of experience
        if metrics['experience_years'] <= 2:
            metrics['experience_level_categorization'] = 'beginner:0-2'
        elif metrics['experience_years'] <= 5:
            metrics['experience_level_categorization'] = 'intermediate:3-5'
        else:
            metrics['experience_level_categorization'] = 'advanced:5+'
        
        logger.info(f"Successfully extracted metrics from resume")
        return metrics
        
    except Exception as e:
        logger.error(f"Error extracting metrics: {str(e)}")
        raise

