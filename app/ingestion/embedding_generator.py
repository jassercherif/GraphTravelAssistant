# app/ingestion/embedding_generator.py

from typing import List

from app.brains import nomic_embedding

# Create the model once and reuse it
_embedding_model = nomic_embedding


def embed_query(text: str) -> List[float]:
    """
    Generate an embedding for a single query.
    Used during retrieval.
    """
    return _embedding_model.embed_query(text)


def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple document chunks.
    Used during ingestion.
    """
    return _embedding_model.embed_documents(texts)