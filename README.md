# 🤖 Sale Chatbot – RAG-based Chatbot

Chatbot hỗ trợ bán hàng sử dụng kiến trúc **RAG (Retrieval-Augmented Generation)**: đọc tài liệu PDF nội bộ, lập chỉ mục vector, và trả lời câu hỏi bằng **Google Gemini**.

---

## 📁 Cấu trúc project

```
sale-chatbot/
├── data/                   # Thư mục chứa file PDF nguồn
├── storage/                # Lưu FAISS index và metadata (tự động sinh ra)
├── ingestion/
│   ├── pdf_loader.py       # Đọc và trích xuất text từ PDF
│   ├── text_chunker.py     # Chia nhỏ văn bản thành chunks
│   ├── embedding_builder.py# Tạo vector embedding
│   ├── vector_store.py     # Lưu FAISS index
│   └── run_ingestion.py    # Script chạy toàn bộ pipeline ingestion
├── retrieval/
│   ├── query_embedder.py   # Embed câu hỏi người dùng
│   └── retriever.py        # Tìm kiếm vector trong FAISS
├── services/
│   ├── prompt_builder.py   # Xây dựng prompt gửi LLM
│   └── llm_service.py      # Gọi Gemini API
├── app.py                  # Giao diện Streamlit
├── api.py                  # REST API với FastAPI
├── requirements.txt
└── .env                    # Chứa API key (không commit lên git)
```

---

## ⚙️ Cài đặt

### 1. Clone project & tạo môi trường ảo

```bash
git clone <repo-url>
cd sale-chatbot

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 3. Cấu hình API Key

Tạo file `.env` ở thư mục gốc:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

> Lấy API key tại: https://aistudio.google.com/app/apikey

---

## 🚀 Chạy project

### Bước 1 – Đặt tài liệu PDF vào thư mục `data/`

```
sale-chatbot/
└── data/
    ├── san_pham_A.pdf
    └── bang_gia.pdf
```

### Bước 2 – Chạy ingestion (lập chỉ mục tài liệu)

```bash
python -m ingestion.run_ingestion
```

> Lệnh này sẽ đọc PDF → chia chunks → tạo embedding → lưu vào `storage/`.
> Chỉ cần chạy lại khi có tài liệu mới.

### Bước 3 – Chạy ứng dụng

**Giao diện Streamlit (khuyên dùng):**

```bash
streamlit run app.py
```

Truy cập: http://localhost:8501

---

**REST API với FastAPI:**

```bash
uvicorn api:app --reload
```

Truy cập docs: http://localhost:8000/docs

Gọi API:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Sản phẩm A có giá bao nhiêu?"}'
```

---

## 🧠 Luồng hoạt động

```
Người dùng đặt câu hỏi
        ↓
Embed câu hỏi → vector (sentence-transformers)
        ↓
Tìm kiếm top-K đoạn văn bản liên quan (FAISS)
        ↓
Xây dựng prompt từ ngữ cảnh tìm được
        ↓
Gọi Gemini API → sinh câu trả lời
        ↓
Hiển thị kết quả cho người dùng
```

---

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| PDF parsing | `pdfplumber` |
| Embedding model | `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Vector store | `FAISS` |
| LLM | Google Gemini (`gemini-2.5-flash`) |
| UI | `Streamlit` |
| API | `FastAPI` + `Uvicorn` |