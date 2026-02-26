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

        prompt = f"""You are a helpful sales assistant. Your job is to answer user questions based strictly on the provided reference documents.

Instructions:
- Answer ONLY using the information found in the reference context below.
- If the context does not contain enough information to answer, respond with: "I'm sorry, I couldn't find relevant information in the available documents."
- Always respond in the same language the user used to ask the question.
- Format your response using Markdown (use bullet points, headers, bold text where appropriate).
- Be concise and accurate. Do not fabricate or assume information beyond what is provided.

Reference Context:
---------------------
{context}
---------------------

User Question:
{question}

Answer:"""
        return prompt.strip()