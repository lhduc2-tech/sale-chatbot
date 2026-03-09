#extract text from pdf file

import os
import tempfile
from typing import List, Optional, Tuple
import pdfplumber
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import PdfFormatOption

from storage.supabase_s3 import list_pdf_files, download_file


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
            return self._load_from_s3()
        return self._load_from_local()

    # ── Local ──────────────────────────────────────────────────────────────────

    def _load_from_local(self) -> List[dict]:
        documents = []
        for filename in os.listdir(self.data_path):
            if not filename.lower().endswith(".pdf"):
                continue
            full_path = os.path.join(self.data_path, filename)
            documents.extend(self._extract_pages(full_path, filename))
        return documents

    # ── S3 ─────────────────────────────────────────────────────────────────────

    def _load_from_s3(self) -> List[dict]:
        """Download toàn bộ PDF từ S3 vào thư mục tạm rồi đọc."""
        documents = []
        s3_keys = list_pdf_files()

        if not s3_keys:
            print("[PDFLoader] Không tìm thấy PDF nào trên S3.")
            return documents

        with tempfile.TemporaryDirectory() as tmp_dir:
            for s3_key in s3_keys:
                filename = os.path.basename(s3_key)
                local_path = os.path.join(tmp_dir, filename)
                if download_file(s3_key, local_path):
                    documents.extend(self._extract_pages(local_path, filename))

        return documents

    # ── Shared ─────────────────────────────────────────────────────────────────

    def _extract_pages(self, full_path: str, filename: str) -> List[dict]:
        pages = []
        docling_result = None  # cache kết quả Docling cho file này (chỉ convert 1 lần)

        with pdfplumber.open(full_path) as pdf:
            for page_number, page in enumerate(pdf.pages):
                text = page.extract_text()

                # Nếu pdfplumber không ra text (PDF scan) → fallback sang Docling + Tesseract
                if not text or not text.strip():
                    if docling_result is None:
                        print(f"[PDFLoader] '{filename}' có trang scan → dùng Docling + Tesseract OCR")
                        docling_result, markdown = self._convert_with_docling(full_path, filename)
                        if markdown:
                            self._save_output(full_path, filename, markdown)

                    if docling_result:
                        text = self._get_page_text(docling_result, page_number)

                if text and text.strip():
                    pages.append({
                        "content": text.strip(),
                        "source": filename,
                        "page": page_number + 1,
                    })
        return pages

    def _convert_with_docling(self, full_path: str, filename: str) -> Tuple[Optional[object], str]:
        """Convert toàn bộ file PDF bằng Docling + Tesseract, trả về (result, markdown)."""
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
            markdown = result.document.export_to_markdown()  # dùng hàm có sẵn của Docling
            return result, markdown

        except Exception as e:
            print(f"[PDFLoader] Docling thất bại cho '{filename}': {e}")
            return None, ""

    def _get_page_text(self, result, page_number: int) -> str:
        """Lấy text của một trang cụ thể từ kết quả Docling."""
        doc = result.document
        page_texts = []
        for element, _level in doc.iterate_items():
            prov = getattr(element, "prov", None)
            if prov and any(p.page_no == page_number + 1 for p in prov):
                text = getattr(element, "text", None)
                if text:
                    page_texts.append(text)
        return "\n".join(page_texts)

    def _save_output(self, full_path: str, filename: str, markdown: str) -> None:
        """Lưu toàn bộ markdown của file PDF ra output/ để kiểm tra."""
        output_dir = os.path.join(os.path.dirname(full_path), "output")
        os.makedirs(output_dir, exist_ok=True)

        pdf_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_dir, f"{pdf_name}.md")
 
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"[PDFLoader] Đã lưu Docling output → {output_file}")
