# app/ingestion/embedding_generator.py

import os
import sys
from typing import List

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
)

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