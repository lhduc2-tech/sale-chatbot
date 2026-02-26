import os
import argparse
from dotenv import load_dotenv

from ingestion.pdf_loader import PDFLoader
from ingestion.text_chunker import TextChunker
from ingestion.embedding_builder import EmbeddingBuilder
from ingestion.vector_store import VectorStore


def run(use_s3: bool = False):
    load_dotenv()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    data_folder = os.path.join(base_dir, "data")
    index_path = os.path.join(base_dir, "storage/faiss.index")
    metadata_path = os.path.join(base_dir, "storage/metadata.json")

    source_label = "Supabase S3" if use_s3 else "local"
    print(f"[Ingestion] Nguồn PDF: {source_label}")

    pdf_loader = PDFLoader(data_folder, use_s3=use_s3)
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
    parser = argparse.ArgumentParser(description="Chạy ingestion pipeline")
    parser.add_argument(
        "--source",
        choices=["local", "s3"],
        default="local",
        help="Nguồn PDF: 'local' (mặc định) hoặc 's3' (download từ Supabase)",
    )
    args = parser.parse_args()
    run(use_s3=(args.source == "s3"))
