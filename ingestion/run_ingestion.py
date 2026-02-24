import os
from dotenv import load_dotenv

from ingestion.pdf_loader import PDFLoader
from ingestion.text_chunker import TextChunker
from ingestion.embedding_builder import EmbeddingBuilder
from ingestion.vector_store import VectorStore


def run():
    load_dotenv()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    data_folder = os.path.join(base_dir, "data")
    index_path = os.path.join(base_dir, "storage/faiss.index")
    metadata_path = os.path.join(base_dir, "storage/metadata.json")

    pdf_loader = PDFLoader(data_folder)
    chunker = TextChunker()
    embedder = EmbeddingBuilder()
    vector_store = VectorStore(index_path, metadata_path)

    documents = pdf_loader.load_pdfs()

    if not documents:
        print("Không tìm thấy tài liệu.")
        return

    chunks = chunker.chunk_documents(documents)

    embedded_chunks = embedder.build_embeddings(chunks)

    vector_store.build_and_save(embedded_chunks)

    print("Ingestion hoàn tất.")


if __name__ == "__main__":
    run()