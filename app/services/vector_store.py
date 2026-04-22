import faiss
import numpy as np


class VectorStore:
    def __init__(self, dimension):
        self.index = faiss.IndexFlatIP(dimension)

    def add_embeddings(self, embeddings):
        embeddings = np.array(embeddings).astype("float32")
        self.index.add(embeddings)

    def search(self, query_embeddings, k=3):
        query_embeddings = np.array(query_embeddings).astype("float32")
        scores, indices = self.index.search(query_embeddings, k)
        return scores, indices