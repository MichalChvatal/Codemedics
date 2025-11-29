"""RAG engine utilities.

This is adapted from the standalone CLI implementation that was provided
and extended to offer a small local storage and an adapter hook for a
database-backed vector search like the one in the notebook.
"""
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import math


class RAGEngine:
    """Very small retrieval engine using sentence-transformers embeddings.

    - add_document(filename, content) stores a document and its vector
    - vector_search(query, top_k) returns the best matching (filename, content)
    """

    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.docs: List[Tuple[str, str, List[float]]] = []

    def add_document(self, filename: str, content: str):
        vec = self.embedding_model.encode(content, normalize_embeddings=True).tolist()
        self.docs.append((filename, content, vec))

    @staticmethod
    def _cosine(a, b):
        numerator = sum(x * y for x, y in zip(a, b))
        denom_a = math.sqrt(sum(x * x for x in a))
        denom_b = math.sqrt(sum(x * x for x in b))
        if denom_a == 0 or denom_b == 0:
            return 0.0
        return numerator / (denom_a * denom_b)

    def vector_search(self, query: str, top_k: int = 5):
        q_vec = self.embedding_model.encode(query, normalize_embeddings=True).tolist()
        scored = []
        for fn, content, vec in self.docs:
            score = self._cosine(q_vec, vec)
            scored.append((score, fn, content))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [(fn, content) for _, fn, content in scored[:top_k]]
