import json
from typing import List, Dict

import faiss
import numpy as np


class Retriever:
    def __init__(self, index_path: str, metadata_path: str):
        self.index = faiss.read_index(index_path)

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def search(self, query_vector: List[float], top_k: int = 20) -> List[Dict]:
        query_vector = np.array(query_vector).astype("float32")

        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)

        distances, indices = self.index.search(query_vector, top_k)

        results = []

        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["score"] = float(distances[0][i])
                results.append(result)

        return results