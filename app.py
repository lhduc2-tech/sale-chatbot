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

st.set_page_config(page_title="Chatbot Nhí Nhảnh", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
        /* === TOÀN BỘ NỀN TRẮNG === */
        html, body {
            background-color: #ffffff !important;
            color: #111111 !important;
        }

        /* Mọi container chính của Streamlit */
        [data-testid="stApp"],
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="block-container"],
        .main, .block-container {
            background-color: #ffffff !important;
            color: #111111 !important;
        }

        /* Xóa khoảng trắng thừa trên đầu */
        [data-testid="stMainBlockContainer"],
        [data-testid="block-container"],
        .block-container {
            padding-top: 3.5rem !important;
        }

        /* Header & toolbar */
        [data-testid="stHeader"],
        [data-testid="stToolbar"] {
            background-color: #ffffff !important;
        }

        /* Ẩn nút Deploy và menu 3 chấm */
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        #MainMenu,
        header [data-testid="stToolbarActions"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #f5f5f5 !important;
        }

        /* ===  THANH NHẬP PHÍA DƯỚI === */
        [data-testid="stBottom"],
        [data-testid="stBottom"] > div,
        [data-testid="stChatInputContainer"],
        [data-testid="stBottomBlockContainer"],
        .stBottom,
        footer {
            background-color: #ffffff !important;
        }
        [data-testid="stBottom"] {
            border-top: 1px solid #e0e0e0 !important;
        }

        /* Ô textarea bên trong thanh nhập */
        [data-testid="stChatInput"],
        [data-testid="stChatInput"] > div,
        [data-testid="stChatInput"] textarea {
            background-color: #f2f2f2 !important;
            color: #111111 !important;
        }

        /* Xóa nền trắng của các element con bên trong textarea */
        [data-testid="stChatInput"] span,
        [data-testid="stChatInput"] p,
        [data-testid="stChatInput"] label {
            background-color: transparent !important;
            color: #111111 !important;
        }

        /* Chữ placeholder đậm hơn */
        [data-testid="stChatInput"] textarea::placeholder {
            color: #555555 !important;
            opacity: 1 !important;
        }

        /* Nút gửi */
        [data-testid="stChatInputSubmitButton"] button {
            background-color: #e0e0e0 !important;
            color: #111111 !important;
        }

        /* Chữ trong bubble chat */
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] div,
        [data-testid="stChatMessage"] {
            color: #111111 !important;
        }
    </style>
""", unsafe_allow_html=True)


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

if embedder is None:
    st.error("⚠️ Chưa có index. Hãy chạy: `python -m ingestion.run_ingestion`")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị tin nhắn chào mở đầu nếu chưa có hội thoại
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("👋 Xin chào! Tôi là Trợ lý bán hàng. Bạn muốn tôi giúp gì hôm nay?")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Nhập câu hỏi của bạn..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        query_vector = embedder.embed(question)
        docs = retriever.search(query_vector, top_k=5)

        if not docs:
            answer = "❌ Không tìm thấy thông tin liên quan trong tài liệu."
            st.markdown(answer)
        else:
            prompt = prompt_builder.build_prompt(question, docs)
            # st.write_stream tự hiển thị từng chunk khi Gemini sinh ra
            answer = st.write_stream(llm.generate_stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": answer})

