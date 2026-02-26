import json
import os
from typing import List, Dict

import faiss
import numpy as np

from storage.supabase_s3 import download_file

# Các object key cố định trên S3 (phải khớp với vector_store.py)
S3_INDEX_KEY = "storage/faiss.index"
S3_METADATA_KEY = "storage/metadata.json"


class Retriever:
    def __init__(self, index_path: str, metadata_path: str):
        # Nếu chưa có file local thì download từ S3
        if not os.path.exists(index_path):
            print("[Retriever] Không tìm thấy index cục bộ, đang tải từ S3...")
            download_file(S3_INDEX_KEY, index_path)

        if not os.path.exists(metadata_path):
            print("[Retriever] Không tìm thấy metadata cục bộ, đang tải từ S3...")
            download_file(S3_METADATA_KEY, metadata_path)

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