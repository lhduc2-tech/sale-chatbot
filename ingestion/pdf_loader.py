#extract text from pdf file

import os #library to work with file or folder
from typing import List, Dict
import pdfplumber #read pdf file

class PDFLoader:
    def __init__(self, data_path: str):
        self.data_path = data_path
    def load_pdfs(self) -> List[dict]: #trả về List[Dict]
        documents = []
        for filename in os.listdir(self.data_path):
            if not filename.lower().endswith(".pdf"):
                continue
            full_path = os.path.join(self.data_path, filename)

            with pdfplumber.open(full_path) as pdf: #open pdf
                for page_number, page in enumerate(pdf.pages):
                    #page: content of a page
                    text = page.extract_text()

                    if text and text.strip():
                        #text.strip() --> xoá khoảng trắng đầu/cuối
                        documents.append({
                            "content": text.strip(),
                            "source": filename,
                            "page": page_number + 1,
                        })
        return documents