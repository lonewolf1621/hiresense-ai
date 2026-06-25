import re
from io import BytesIO

try:
    import PyPDF2
except:
    PyPDF2 = None

try:
    from docx import Document
except:
    Document = None


def parse_pdf(file_bytes):
    """Extract text from PDF"""
    if not PyPDF2:
        return ""
    
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
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
    """Extract phone number (Indian format)"""
    pattern = r"\+?91?\s?[6-9]\d{9}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def parse_resume(file_bytes, file_type):
    """Parse resume based on file type"""
    if file_type.lower() == "pdf":
        return parse_pdf(file_bytes)
    elif file_type.lower() in ["docx", "doc"]:
        return parse_docx(file_bytes)
    else:
        try:
            return file_bytes.decode("utf-8")
        except:
            return ""