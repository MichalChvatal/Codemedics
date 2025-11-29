"""RAG engine utilities.

This is adapted from the standalone CLI implementation that was provided
and extended to offer a small local storage and an adapter hook for a
database-backed vector search like the one in the notebook.
"""
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import iris
class RAGEngine:
    """Very small retrieval engine using sentence-transformers embeddings.

    - add_document(filename, content) stores a document and its vector
    - vector_search(query, top_k) returns the best matching (filename, content)
    """

    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.docs: List[Tuple[str, str, List[float]]] = []
        self.cursor = iris.connect("localhost", 32782, "DEMO", "_SYSTEM", "ISCDEMO").cursor()
    
    def vector_search(self, query: str, top_k: int = 5):
        # Create embedding
        search_vector = self.embedding_model.encode(
            query,
            normalize_embeddings=False,  # SQL vector_cosine expects raw
            show_progress_bar=False
        ).tolist()

        # SQL vector search
        sql = f"""
            SELECT TOP {top_k} filename, content
            FROM VectorSearch.ORGstruct
            ORDER BY VECTOR_COSINE(vector, TO_VECTOR(?, DOUBLE)) DESC
        """

        self.cursor.execute(sql, [str(search_vector)])
        rows = self.cursor.fetchall()

        # Return tuples compatible with your existing RAG pipeline
        return [(filename, content) for filename, content in rows]