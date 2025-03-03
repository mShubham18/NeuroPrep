import pdfplumber
from docx import Document
import os

def parse_to_text(file_path: str) -> str:
    """Parse resume file to text."""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                text = '\n'.join(page.extract_text() for page in pdf.pages)
        elif file_ext in ['.doc', '.docx']:
            doc = Document(file_path)
            text = '\n'.join(paragraph.text for paragraph in doc.paragraphs)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        return text
    except Exception as e:
        print(f"Error parsing resume: {str(e)}")
        return ""