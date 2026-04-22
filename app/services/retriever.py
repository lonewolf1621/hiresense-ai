from app.services.chunking import chunk_text
from app.services.embedding import embed_text
from app.services.vector_store import VectorStore


def retrieve_relevant_chunks(resume_text, jd_text):
    resume_chunks = chunk_text(resume_text)
    jd_chunks = chunk_text(jd_text)

    resume_embeddings = embed_text(resume_chunks)
    jd_embeddings = embed_text(jd_chunks)

    vector_store = VectorStore(dimension=resume_embeddings.shape[1])
    vector_store.add_embeddings(resume_embeddings)

    scores, indices = vector_store.search(jd_embeddings, k=2)

    results = []

    for i, idx_list in enumerate(indices):
        for j, idx in enumerate(idx_list):
            results.append((scores[i][j], resume_chunks[idx]))

    # sort + remove duplicates
    results = sorted(results, key=lambda x: x[0], reverse=True)

    seen = set()
    final = []

    for score, chunk in results:
        if chunk not in seen:
            seen.add(chunk)
            final.append((score, chunk))

    return final