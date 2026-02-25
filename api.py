import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from retrieval.query_embedder import QueryEmbedder
from retrieval.retriever import Retriever
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "storage", "faiss.index")
METADATA_PATH = os.path.join(BASE_DIR, "storage", "metadata.json")
EMBED_MODEL = "all-MiniLM-L6-v2"


# ── Lifespan (khởi tạo một lần khi server start) ───────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    if not os.path.exists(INDEX_PATH) or not os.path.exists(METADATA_PATH):
        raise RuntimeError(
            "Chưa có index. Hãy chạy ingestion trước: python -m ingestion.run_ingestion"
        )
    application.state.embedder = QueryEmbedder(model_name=EMBED_MODEL)
    application.state.retriever = Retriever(INDEX_PATH, METADATA_PATH)
    application.state.prompt_builder = PromptBuilder()
    application.state.llm = LLMService()
    yield


# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sale Chatbot API",
    description="RAG chatbot API – trả lời dựa trên tài liệu PDF nội bộ.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str


class SourceItem(BaseModel):
    content: str
    source: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


# ── Endpoints ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():

    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse, tags=["Chatbot"])
def chat(req: ChatRequest):
    """
    Nhận câu hỏi, tìm tài liệu liên quan, sinh câu trả lời bằng Gemini.
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống.")

    # 1. Embed câu hỏi
    query_vector = app.state.embedder.embed(req.question)

    # 2. Tìm các đoạn văn bản liên quan
    docs = app.state.retriever.search(query_vector, top_k=20)

    if not docs:
        return ChatResponse(
            answer="Không tìm thấy thông tin liên quan trong tài liệu.",
            sources=[],
        )

    # 3. Xây dựng prompt
    prompt = app.state.prompt_builder.build_prompt(req.question, docs)

    # 4. Gọi LLM
    answer = app.state.llm.generate(prompt)

    sources = [SourceItem(content=d.get("content", ""), source=d.get("source", "")) for d in docs]

    return ChatResponse(answer=answer, sources=sources)
