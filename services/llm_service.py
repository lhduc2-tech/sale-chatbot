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
        self.generation_config = genai.GenerationConfig(
            temperature=0.2,       # Thấp --> bám sát tài liệu, ít hallucination
            max_output_tokens=1024,
        )

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config=self.generation_config,
        )

        if response and response.text:
            return response.text.strip()

        return "Không nhận được phản hồi từ mô hình."