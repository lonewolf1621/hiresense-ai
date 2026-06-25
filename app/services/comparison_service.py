from app.main_pipeline import run_pipeline


def compare_resume_with_jobs(resume: str, job_descriptions: list) -> dict:
    """
    Compare a resume against multiple job descriptions.
    Returns scores for each job and best match recommendation.
    """
    
    results = []
    
    for idx, job_desc in enumerate(job_descriptions, 1):
        try:
            analysis = run_pipeline(resume, job_desc)
            analysis["job_number"] = idx
            results.append(analysis)
        except Exception as e:
            print(f"Error processing job {idx}: {e}")
            results.append({
                "job_number": idx,
                "match_score_percent": 0,
                "error": str(e)
            })
    
    # Find best match
    best_match = max(results, key=lambda x: x.get('match_score_percent', 0))
    best_match_idx = best_match['job_number']
    
    # Find worst match
    worst_match = min(results, key=lambda x: x.get('match_score_percent', 100))
    worst_match_idx = worst_match['job_number']
    
    # Calculate average
    avg_score = sum(r.get('match_score_percent', 0) for r in results) / len(results)
    
    return {
        "results": results,
        "best_match_job": best_match_idx,
        "best_match_score": best_match['match_score_percent'],
        "worst_match_job": worst_match_idx,
        "worst_match_score": worst_match['match_score_percent'],
        "average_score": round(avg_score, 2),
        "total_jobs": len(results)
    }