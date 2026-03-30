import os
from typing import Iterator
from dotenv import load_dotenv
import google.generativeai as genai
from tools.database_tools import check_product_stock


class LLMService:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY chưa được cấu hình trong file .env")

        genai.configure(api_key=api_key)
        # Truyền danh sách công cụ vào bộ não của mô hình
        self.model = genai.GenerativeModel(model_name, tools=[check_product_stock])
        self.generation_config = genai.GenerationConfig(
            temperature=0.2,       # Thấp --> bám sát tài liệu, ít hallucination
            max_output_tokens=4096,
        )

    def generate(self, prompt: str) -> str:
        # Tự động hóa quá trình kích hoạt Tool bằng class ChatSession
        chat = self.model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(
            prompt,
            generation_config=self.generation_config,
        )

        if response and response.text:
            return response.text.strip()

        return "Không nhận được phản hồi từ mô hình."

    def generate_stream(self, prompt: str) -> Iterator[str]:
        """Trả về từng chunk text.
        Do Google SDK không hỗ trợ dùng stream=True cugnf lúc với enable_automatic_function_calling=True,
        ta giả lập stream bằng cách lấy toàn bộ text rồi yield từng từ.
        """
        chat = self.model.start_chat(enable_automatic_function_calling=True)
        
        # Bắt buộc gọi stream=False để Tool Calling có thể hoạt động ngầm tự động
        import time
        response = chat.send_message(
            prompt,
            generation_config=self.generation_config,
            stream=False,
        )
        
        if response and response.text:
            text = response.text
            # Giả lập luồng stream từng chữ để giao diện Streamlit không bị lỗi
            # và vẫn giữ được hiệu ứng gõ chữ đẹp mắt
            words = text.split(" ")
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                time.sleep(0.02)
        else:
            yield "Không nhận được phản hồi từ mô hình."
