from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.main_pipeline import run_pipeline

app = FastAPI(
    title="HireSense AI API",
    description="Smart Job-Resume Matcher for Indian Job Seekers",
    version="1.0.0"
)

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    resume: str
    job_description: str


@app.get("/")
def root():
    return {
        "message": "🚀 HireSense AI is running",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze",
            "health": "GET /health"
        }
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze")
def analyze(data: AnalysisRequest):
    try:
        if not data.resume.strip() or not data.job_description.strip():
            raise HTTPException(status_code=400, detail="Resume and job description required")
        
        result = run_pipeline(data.resume, data.job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))