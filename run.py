from app.main import run_pipeline
import json

print(" Starting pipeline...")

if __name__ == "__main__":
    resume_path = "data/resume.txt"
    jd_path = "data/jd.txt"

    result = run_pipeline(resume_path, jd_path)

    print("Pipeline finished")

    print("\n=== AI ANALYSIS (JSON) ===\n")
    print(json.dumps(result, indent=4))