from typing import List, Dict


class PromptBuilder:
    def __init__(self):
        pass

    def build_context(self, documents: List[Dict]) -> str:
        context_parts = []

        for doc in documents:
            text = doc.get("text") or doc.get("content") or ""
            source = doc.get("source", "")
            context_parts.append(f"Nguồn: {source}\n{text}")

        return "\n\n".join(context_parts)

    def build_prompt(self, question: str, documents: List[Dict]) -> str:
        context = self.build_context(documents)

        prompt = f"""You are a helpful sales assistant. Your job is to answer customer questions based on the provided reference documents and available tools.

Instructions:
- Use the provided reference context to answer general questions about the store or guidelines.
- CRITICAL: If the user asks about product inventory, quantity, stock, or availability (e.g. "còn bao nhiêu", "số lượng", "tồn kho"), you MUST use the provided tool `check_product_stock` to get real-time data.
- Do NOT say you cannot find the information about stock until you have successfully executed the `check_product_stock` tool.
- Always respond in the SAME LANGUAGE as the user's question.
- Format your response using Markdown (use bullet points, bold text where appropriate).
- Be concise. Do not fabricate information.

Reference Context:
---------------------
{context}
---------------------

User Question:
{question}

Answer:"""
        return prompt.strip()
