---
title: Sale Chatbot
emoji: 💬
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

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
│   ├── vector_store.py     # Lưu FAISS index + upload S3
│   └── run_ingestion.py    # Script chạy toàn bộ pipeline ingestion
├── retrieval/
│   ├── query_embedder.py   # Embed câu hỏi người dùng
│   └── retriever.py        # Tìm kiếm vector trong FAISS (auto-download S3)
├── services/
│   ├── prompt_builder.py   # Xây dựng prompt gửi LLM
│   └── llm_service.py      # Gọi Gemini API
├── storage/
│   └── supabase_s3.py      # Module kết nối Supabase S3
├── app.py                  # Giao diện Streamlit
├── api.py                  # REST API với FastAPI
├── upload_pdfs.py          # Script upload PDF lên Supabase S3
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

### 3. Cấu hình biến môi trường

Tạo file `.env` ở thư mục gốc:

```env
# Google Gemini
GEMINI_API_KEY=your_google_gemini_api_key_here

# Supabase S3-compatible Storage
S3_ENDPOINT=https://<project-id>.storage.supabase.co/storage/v1/s3
S3_REGION=ap-northeast-1
S3_KEY_ID=your_s3_key_id
S3_ACCESS_KEY=your_s3_access_key
S3_BUCKET_NAME=data-chatbot
```

> - Lấy Gemini API key tại: https://aistudio.google.com/app/apikey
> - Lấy Supabase S3 credentials tại: **Supabase Dashboard → Project Settings → S3 Connection**

---

## ☁️ Supabase S3 Storage

Project sử dụng **Supabase Storage** (tương thích S3) để lưu trữ dữ liệu trên cloud, đảm bảo hoạt động ổn định khi deploy.

### Cấu trúc bucket `data-chatbot`

```
data-chatbot/
├── data/              ← File PDF nguồn (upload thủ công)
│   ├── san_pham.pdf
│   └── chinh_sach.pdf
└── storage/           ← Index vector (tự động sau ingestion)
    ├── faiss.index
    └── metadata.json
```

### Upload PDF lên S3

```bash
# Upload toàn bộ PDF trong thư mục data/
python upload_pdfs.py

# Upload một file cụ thể
python upload_pdfs.py san_pham.pdf

# Xem danh sách PDF đang có trên S3
python upload_pdfs.py --list
```

---

## 🚀 Chạy project

### Bước 1 – Chuẩn bị tài liệu PDF

**Option A – Đọc từ local** (phát triển/test):

```
sale-chatbot/
└── data/
    ├── san_pham_A.pdf
    └── bang_gia.pdf
```

**Option B – Đọc từ Supabase S3** (khuyên dùng cho production):

```bash
python upload_pdfs.py   # upload PDF lên S3 trước
```

### Bước 2 – Chạy ingestion (lập chỉ mục tài liệu)

```bash
# Đọc PDF từ local (mặc định)
python -m ingestion.run_ingestion

# Hoặc đọc PDF từ Supabase S3
python -m ingestion.run_ingestion --source s3
```

> Lệnh này sẽ: đọc PDF → chia chunks → tạo embedding → lưu FAISS index → **upload lên S3**.
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

### Ingestion Pipeline

```
PDF (local hoặc S3)
        ↓
Trích xuất text (pdfplumber)
        ↓
Chia chunks (TextChunker)
        ↓
Tạo vector embedding (sentence-transformers)
        ↓
Lưu FAISS index → Upload lên Supabase S3
```

### Chat Pipeline

```
Người dùng đặt câu hỏi
        ↓
Embed câu hỏi → vector (sentence-transformers)
        ↓
Tải FAISS index từ S3 (nếu chưa có local)
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
| Cloud storage | `Supabase S3` + `boto3` |
| UI | `Streamlit` |
| API | `FastAPI` + `Uvicorn` |