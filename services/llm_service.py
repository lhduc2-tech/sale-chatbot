import os
from dotenv import load_dotenv
import google.generativeai as genai


class LLMService:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY chưa được cấu hình trong file .env")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()

        return "Không nhận được phản hồi từ mô hình."