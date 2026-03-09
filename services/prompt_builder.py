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

        prompt = f"""You are a helpful sales assistant. Your job is to answer customer questions based strictly on the provided reference documents.

Instructions:
- Answer ONLY using information found in the reference context below.
- If the context does not contain enough information, let the user know that no relevant information was found.
- IMPORTANT: Always respond in the SAME LANGUAGE as the user's question (e.g. Vietnamese question → Vietnamese answer, English question → English answer). This rule also applies to the "no information found" message.
- Format your response using Markdown (use bullet points, bold text where appropriate).
- Be concise and accurate. Do not fabricate information beyond what is provided.

Reference Context:
---------------------
{context}
---------------------

User Question:
{question}

Answer:"""
        return prompt.strip()
