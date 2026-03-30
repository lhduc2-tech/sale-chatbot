#extract markdown from pdf using docling

import os
import tempfile
from typing import List, Optional, Tuple
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import PdfFormatOption

from storage.supabase_s3 import list_pdf_files, download_file
from ingestion.ocr_post_processor import OCRPostProcessor


class PDFLoader:
    def __init__(self, data_path: str, use_s3: bool = False):
        """
        Args:
            data_path: Thư mục local chứa PDF (dùng khi use_s3=False).
            use_s3: Nếu True, download PDF từ Supabase S3 thay vì đọc local.
        """
        self.data_path = data_path
        self.use_s3 = use_s3

    def load_pdfs(self) -> List[dict]:
        if self.use_s3:
            documents = self._load_from_s3()
            if documents:
                return documents
            print("[PDFLoader] ⚠️  S3 không trả về tài liệu nào → fallback về local...")
            return self._load_from_local()
        return self._load_from_local()

    # ── Local ──────────────────────────────────────────────────────────────────

    def _load_from_local(self) -> List[dict]:
        documents = []
        for filename in os.listdir(self.data_path):
            if not filename.lower().endswith(".pdf"):
                continue
            full_path = os.path.join(self.data_path, filename)
            documents.extend(self._extract_document(full_path, filename))
        return documents

    # ── S3 ─────────────────────────────────────────────────────────────────────

    def _load_from_s3(self) -> List[dict]:
        """Download toàn bộ PDF từ S3 vào thư mục tạm rồi đọc."""
        documents = []
        s3_keys = list_pdf_files()

        if not s3_keys:
            print("[PDFLoader] Không tìm thấy PDF nào trên S3.")
            return documents

        # Luôn lưu markdown ra data/output/ (không phải thư mục tạm)
        output_dir = os.path.join(self.data_path, "output")

        with tempfile.TemporaryDirectory() as tmp_dir:
            for s3_key in s3_keys:
                filename = os.path.basename(s3_key)
                local_path = os.path.join(tmp_dir, filename)
                if download_file(s3_key, local_path):
                    documents.extend(self._extract_document(local_path, filename, output_dir=output_dir))

        return documents

    # ── Shared ─────────────────────────────────────────────────────────────────

    def _extract_document(self, full_path: str, filename: str, output_dir: Optional[str] = None) -> List[dict]:
        """
        Trích xuất toàn bộ văn bản của định dạng Markdown từ PDF bằng Docling
        Args:
            full_path  : Đường dẫn đầy đủ tới file PDF.
            filename   : Tên file (dùng cho metadata cấu trúc).
            output_dir : Thư mục lưu file `.md` sau quá trình OCR.
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(full_path), "output")

        print(f"\n[PDFLoader] Đang trích xuất Markdown từ '{filename}' bằng Docling...")
        docling_result, markdown = self._convert_with_docling(full_path, filename)
        
        if markdown:
            print(f"[PDFLoader] Đang tự động chuẩn hóa và chỉnh sửa lỗi ký tự OCR...")
            try:
                processor = OCRPostProcessor()
                markdown = processor.process(markdown)
                print(f"[PDFLoader] ✅ Chỉnh sửa OCR hoàn tất.")
            except Exception as e:
                print(f"[PDFLoader] ⚠️ Bỏ qua trình sửa lỗi tự động: {e}")
                
            self._save_output(filename, markdown, output_dir)
            
            # Trả về toàn bộ nội dung trong 1 cục chunk khổng lồ
            # TextChunker sẽ có nhiệm vụ băm cắt theo các thẻ # Tiêu đề về sau
            return [{
                "content": markdown.strip(),
                "source": filename
            }]
            
        return []

    def _convert_with_docling(self, full_path: str, filename: str) -> Tuple[Optional[object], str]:
        """Convert toàn bộ file PDF bằng Docling + Tesseract, trả về (result, markdown text)."""
        try:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = TesseractCliOcrOptions(lang=["vie", "eng"])

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            result = converter.convert(full_path)
            markdown = result.document.export_to_markdown()  
            return result, markdown

        except Exception as e:
            print(f"[PDFLoader] ❌ Lỗi khi đọc file '{filename}' với Docling: {e}")
            return None, ""

    def _save_output(self, filename: str, markdown: str, output_dir: str) -> None:
        """Lưu file Markdown sau khi đọc đề kiểm tra chéo."""
        os.makedirs(output_dir, exist_ok=True)

        pdf_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_dir, f"{pdf_name}.md")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"[PDFLoader] Đã xuất bản kết quả trích xuất ra {output_file}")
