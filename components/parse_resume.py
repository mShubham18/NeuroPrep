import pdfplumber
import docx
import google.generativeai as genai
import re
import os
from dotenv import load_dotenv
load_dotenv()
from components.model_configuration import model_config
model = model_config()
# Extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

# Extract text from a DOCX file
def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs]).strip()

def parse_to_text(path:str):
    if path[-3:]=="pdf":
        resume_text = extract_text_from_pdf(path)
    if path[-3:]=="doc":
        resume_text = extract_text_from_docx(path)
    
    resume_text = re.sub(r"[^a-zA-Z0-9\s@.]","",resume_text)
    return resume_text