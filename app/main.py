# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from app.main_pipeline import run_pipeline  # now exists

app = FastAPI(title="HireSense AI", version="1.0.0")


class RequestModel(BaseModel):
    resume: str
    job_description: str


@app.get("/")
def root():
    return {"message": "HireSense AI is running 🚀"}


@app.post("/analyze")
def analyze(data: RequestModel):
    result = run_pipeline(data.resume, data.job_description)
    return result