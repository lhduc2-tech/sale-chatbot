#extract text from pdf file

import os
import tempfile
from typing import List
import pdfplumber
import easyocr
from pdf2image import convert_from_path

from storage.supabase_s3 import list_pdf_files, download_file

# Khởi tạo EasyOCR reader một lần duy nhất (tránh load model nhiều lần)
_easyocr_reader = None

def _get_easyocr_reader() -> easyocr.Reader:
    global _easyocr_reader
    if _easyocr_reader is None:
        print("[PDFLoader] Đang khởi tạo EasyOCR reader (lần đầu sẽ tải model)...")
        _easyocr_reader = easyocr.Reader(["vi", "en"])
    return _easyocr_reader


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
        with pdfplumber.open(full_path) as pdf:  # mở file pdf
            for page_number, page in enumerate(pdf.pages):
                text = page.extract_text()

                # Nếu pdfplumber không ra text (PDF scan) → fallback sang EasyOCR
                if not text or not text.strip():
                    print(f"[PDFLoader] Trang {page_number + 1} của '{filename}' không có text layer → dùng EasyOCR")
                    text = self._ocr_with_easyocr(full_path, page_number)

                if text and text.strip():
                    pages.append({
                        "content": text.strip(),
                        "source": filename,
                        "page": page_number + 1,
                    })
        return pages

    def _ocr_with_easyocr(self, full_path: str, page_number: int) -> str:
        """Dùng EasyOCR để đọc text từ trang PDF scan (không có text layer)."""
        try:
            # Render trang PDF thành ảnh
            images = convert_from_path(
                full_path,
                first_page=page_number + 1,
                last_page=page_number + 1,
            )
            if not images:
                return ""

            reader = _get_easyocr_reader()
            import numpy as np
            result = reader.readtext(np.array(images[0]))

            # Ghép các đoạn text theo thứ tự
            extracted_text = "\n".join([item[1] for item in result])

            # Lưu output ra thư mục output/ để kiểm tra
            if extracted_text.strip():
                self._save_ocr_output(full_path, page_number, extracted_text)

            return extracted_text

        except Exception as e:
            print(f"[PDFLoader] EasyOCR thất bại ở trang {page_number + 1}: {e}")
            return ""

    def _save_ocr_output(self, full_path: str, page_number: int, text: str) -> None:
        """Lưu text OCR ra file .txt trong thư mục output/ để kiểm tra."""
        output_dir = os.path.join(os.path.dirname(full_path), "output")
        os.makedirs(output_dir, exist_ok=True)

        pdf_name = os.path.splitext(os.path.basename(full_path))[0]
        output_file = os.path.join(output_dir, f"{pdf_name}_page{page_number + 1}.md")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"[PDFLoader] Đã lưu OCR output → {output_file}")
