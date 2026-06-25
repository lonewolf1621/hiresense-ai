from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.main_pipeline import run_pipeline
import json

app = FastAPI(
    title="HireSense AI API",
    description="Smart Job-Resume Matcher",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "🚀 HireSense AI is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze(request: dict):
    try:
        resume = request.get("resume", "")
        job_description = request.get("job_description", "")
        
        if not resume or not job_description:
            raise HTTPException(status_code=400, detail="Resume and JD required")
        
        result = run_pipeline(resume, job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.services.comparison_service import compare_resume_with_jobs

@app.post("/compare")
async def compare(request: dict):
    """
    Compare resume against multiple job descriptions.
    
    Request format:
    {
        "resume": "...",
        "jobs": [
            "Job Description 1",
            "Job Description 2",
            "Job Description 3"
        ]
    }
    """
    try:
        resume = request.get("resume", "")
        jobs = request.get("jobs", [])
        
        if not resume or not jobs:
            raise HTTPException(status_code=400, detail="Resume and jobs required")
        
        if len(jobs) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 jobs allowed for comparison")
        
        result = compare_resume_with_jobs(resume, jobs)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))