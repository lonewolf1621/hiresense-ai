import numpy as np
from app.services.embedding import embed_text


def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (
        np.linalg.norm(vec1) * np.linalg.norm(vec2)
    )


def compute_match_score(resume_text, jd_text):
    embeddings = embed_text([resume_text, jd_text])

    resume_vec = embeddings[0]
    jd_vec = embeddings[1]

    score = cosine_similarity(resume_vec, jd_vec)

    return round(score * 100, 2)