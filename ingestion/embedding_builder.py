from typing import List, Dict
from sentence_transformers import SentenceTransformer


class EmbeddingBuilder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def build_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        texts = [chunk.get("content", "") for chunk in chunks]

        embeddings = self.model.encode(texts, show_progress_bar=True)

        results = []

        for chunk, embedding in zip(chunks, embeddings):
            results.append({
                "content": chunk.get("content", ""),
                "source": chunk.get("source", ""),
                "embedding": embedding.tolist()
            })

        return results