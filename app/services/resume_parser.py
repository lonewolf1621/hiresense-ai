import re
from io import BytesIO

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None


def parse_pdf(file_bytes):
    """Extract text from PDF"""
    if not pdfplumber:
        return ""
    
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"PDF parsing error: {e}")
        return ""


def parse_docx(file_bytes):
    """Extract text from DOCX"""
    if not Document:
        return ""
    
    try:
        doc = Document(BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"DOCX parsing error: {e}")
        return ""


def extract_email(text):
    """Extract email from resume"""
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text):
    """Extract phone number from resume (Indian format)"""
    pattern = r"\+?91?\s?[6-9]\d{9}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def parse_resume(file_content, file_type):
    """Parse resume based on file type"""
    if file_type == "pdf":
        return parse_pdf(file_content)
    elif file_type == "docx":
        return parse_docx(file_content)
    else:
        return file_content.decode("utf-8")