import pdfplumber
from docx import Document
import os
import logging

logger = logging.getLogger(__name__)

def parse_to_text(file_path: str) -> str:
    """Parse resume file to text."""
    if not os.path.exists(file_path):
        logger.error(f"Resume file not found: {file_path}")
        raise FileNotFoundError(f"Resume file not found: {file_path}")
        
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.pdf':
            logger.info(f"Parsing PDF resume: {file_path}")
            with pdfplumber.open(file_path) as pdf:
                text = '\n'.join(page.extract_text() for page in pdf.pages)
                if not text.strip():
                    logger.warning("PDF parsing resulted in empty text")
        elif file_ext in ['.doc', '.docx']:
            logger.info(f"Parsing DOCX resume: {file_path}")
            doc = Document(file_path)
            text = '\n'.join(paragraph.text for paragraph in doc.paragraphs)
            if not text.strip():
                logger.warning("DOCX parsing resulted in empty text")
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        if not text.strip():
            logger.error("No text content extracted from resume")
            raise ValueError("No text content could be extracted from the resume")
            
        logger.info(f"Successfully parsed resume with {len(text)} characters")
        return text
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        raise