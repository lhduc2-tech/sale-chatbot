from typing import List, Dict


class TextChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        if overlap >= chunk_size:
            raise ValueError(f"overlap ({overlap}) phải nhỏ hơn chunk_size ({chunk_size})")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        chunks = []

        for doc in documents:
            content = doc.get("content", "")
            source = doc.get("source", "")

            start = 0
            text_length = len(content)

            while start < text_length:
                end = start + self.chunk_size
                chunk_text = content[start:end]

                chunks.append({
                    "content": chunk_text,
                    "source": source
                })

                start += self.chunk_size - self.overlap

        return chunks