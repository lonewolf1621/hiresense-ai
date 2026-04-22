from fastapi import FastAPI
from pydantic import BaseModel
from app.main import run_pipeline

app = FastAPI()


class InputData(BaseModel):
    resume: str
    job_description: str


@app.get("/")
def root():
    return {"message": "HireSense API is running 🚀"}


@app.post("/analyze")
def analyze(data: InputData):
    result = run_pipeline(data.resume, data.job_description)
    return result