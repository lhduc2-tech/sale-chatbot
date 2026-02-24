from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class QueryEmbedder:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed(self, query: str) -> np.ndarray:
        embedding = self.model.encode(query)
        vector = np.array([embedding]).astype("float32")
        return vector

    def embed_batch(self, queries: List[str]) -> np.ndarray:
        embeddings = self.model.encode(queries)
        vectors = np.array(embeddings).astype("float32")
        return vectors