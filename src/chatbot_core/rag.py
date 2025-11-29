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

    def vector_search(self, user_prompt: str):
        search_vector = self.embedding_model.encode(
            user_prompt,
            normalize_embeddings=False,
            show_progress_bar=False,
        ).tolist()

        search_sql = """
            SELECT TOP 5 filename, content 
            FROM VectorSearch.ORGstruct
            ORDER BY VECTOR_COSINE(vector, TO_VECTOR(?,DOUBLE)) DESC
        """
        self.cursor.execute(search_sql, [str(search_vector)])
        results = self.cursor.fetchall()
        return [f"Text z dokumentu {x} -> {y}" for x, y in results]