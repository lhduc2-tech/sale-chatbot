import os
import streamlit as st
from dotenv import load_dotenv

from retrieval.query_embedder import QueryEmbedder
from retrieval.retriever import Retriever
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "storage", "faiss.index")
METADATA_PATH = os.path.join(BASE_DIR, "storage", "metadata.json")
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

st.set_page_config(page_title="Sale Chatbot", page_icon="🤖", layout="centered")


@st.cache_resource(hash_funcs={str: lambda x: x})
def load_pipeline(embed_model: str = EMBED_MODEL):
    # Nếu chưa có file local, thử download từ S3
    if not os.path.exists(INDEX_PATH) or not os.path.exists(METADATA_PATH):
        try:
            from storage.supabase_s3 import download_file
            download_file("storage/faiss.index", INDEX_PATH)
            download_file("storage/metadata.json", METADATA_PATH)
        except Exception as e:
            st.warning(f"Không thể tải index từ S3: {e}")

    # Nếu vẫn không có sau khi thử download thì dừng
    if not os.path.exists(INDEX_PATH) or not os.path.exists(METADATA_PATH):
        return None, None, None, None

    return (
        QueryEmbedder(model_name=EMBED_MODEL),
        Retriever(INDEX_PATH, METADATA_PATH),
        PromptBuilder(),
        LLMService(),
    )


embedder, retriever, prompt_builder, llm = load_pipeline(EMBED_MODEL)

st.title("🤖 Sale Chatbot")

if embedder is None:
    st.error("⚠️ Chưa có index. Hãy chạy: `python -m ingestion.run_ingestion`")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Nhập câu hỏi của bạn..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Đang trả lời..."):
            query_vector = embedder.embed(question)
            docs = retriever.search(query_vector, top_k=5)

            if not docs:
                answer = "❌ Không tìm thấy thông tin liên quan trong tài liệu."
            else:
                prompt = prompt_builder.build_prompt(question, docs)
                answer = llm.generate(prompt)

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
