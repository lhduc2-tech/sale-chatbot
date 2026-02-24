import os
import json
import faiss
import numpy as np
from typing import List, Dict


class VectorStore:
    def __init__(self, index_path: str, metadata_path: str):
        self.index_path = index_path
        self.metadata_path = metadata_path

    def build_and_save(self, embedded_chunks: List[Dict]) -> None:
        embeddings = [item["embedding"] for item in embedded_chunks]
        vectors = np.array(embeddings).astype("float32")

        dimension = vectors.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(vectors)

        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(index, self.index_path)

        metadata = [
            {
                "content": item["content"],
                "source": item["source"]
            }
            for item in embedded_chunks
        ]

        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)