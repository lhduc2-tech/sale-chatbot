#extract text from pdf file

import os
import tempfile
from typing import List
import pdfplumber

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
        with pdfplumber.open(full_path) as pdf:
            for page_number, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        "content": text.strip(),
                        "source": filename,
                        "page": page_number + 1,
                    })
        return pages
