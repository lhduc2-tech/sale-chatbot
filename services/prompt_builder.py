from typing import List, Dict


class PromptBuilder:
    def __init__(self):
        pass

    def build_context(self, documents: List[Dict]) -> str:
        context_parts = []

        for doc in documents:
            text = doc.get("text") or doc.get("content") or ""
            source = doc.get("source", "")
            context_parts.append(f"Source: {source}\n{text}")

        return "\n\n".join(context_parts)

    def build_prompt(self, question: str, documents: List[Dict]) -> str:
        context = self.build_context(documents)

        prompt = f"""
                Bạn là một trợ lý AI.
                Luôn xưng "tôi" khi trả lời.
                Không sử dụng từ "bạn".
                Chỉ trả lời dựa trên thông tin được cung cấp.
                Nếu không đủ thông tin, hãy nói: "Tôi không tìm thấy dữ liệu phù hợp.
                Trả lời bằng markdown"
                
                
                Thông tin tham khảo:
                ---------------------
                {context}
                ---------------------
                
                Câu hỏi:
                {question}
                
                Trả lời:
                """
        return prompt.strip()