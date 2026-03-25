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
            documents.extend(self._extract_pages(full_path, filename))
            #extend: add all the pages of the pdf to the documents list
            #apend: add one item to the documents list
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
                    documents.extend(self._extract_pages(local_path, filename, output_dir=output_dir))

        return documents

    # ── Shared ─────────────────────────────────────────────────────────────────

    def _extract_pages(self, full_path: str, filename: str, output_dir: Optional[str] = None) -> List[dict]:
        """
        Args:
            full_path  : Đường dẫn đầy đủ tới file PDF.
            filename   : Tên file (dùng cho metadata và tên file output).
            output_dir : Thư mục lưu markdown sau OCR.
                         Mặc định = cùng thư mục chứa PDF / output/.
                         Khi đọc từ S3, truyền vào data_path/output/ để tránh mất file.
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(full_path), "output")

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
                            # ── Tự động sửa lỗi OCR ──
                            print(f"[PDFLoader] Đang tự động sửa lỗi OCR...")
                            try:
                                processor = OCRPostProcessor()
                                markdown = processor.process(markdown)
                                print(f"[PDFLoader] ✅ Sửa OCR hoàn tất.")
                            except Exception as e:
                                print(f"[PDFLoader] ⚠️  Bỏ qua auto-correct: {e}")
                            self._save_output(filename, markdown, output_dir)

                    if docling_result:
                        text = self._get_page_text(docling_result, page_number)

                if text and text.strip():
                    #strip(): remove leading and trailing whitespace
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
        for element, _level in doc.iterate_items(): #iterate_items(): iterate over all the items in the document
            prov = getattr(element, "prov", None)
            if prov and any(p.page_no == page_number + 1 for p in prov):
                text = getattr(element, "text", None)
                if text:
                    page_texts.append(text)
        return "\n".join(page_texts)

    def _save_output(self, filename: str, markdown: str, output_dir: str) -> None:
        """Lưu toàn bộ markdown của file PDF ra output_dir/ để kiểm tra."""
        os.makedirs(output_dir, exist_ok=True)

        pdf_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_dir, f"{pdf_name}.md")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"[PDFLoader] Đã lưu Docling output → {output_file}")
