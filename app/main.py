from fastapi import FastAPI
from pydantic import BaseModel
from app.main_pipeline import run_pipeline  # adjust import

app = FastAPI()

class RequestModel(BaseModel):
    resume: str
    job_description: str

@app.post("/analyze")
def analyze(data: RequestModel):
    result = run_pipeline(data.resume, data.job_description)
    return result