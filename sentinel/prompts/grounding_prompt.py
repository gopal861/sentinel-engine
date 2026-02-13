def build_grounding_prompt(query: str, context: str) -> str:
    return f"""
You are operating in strict governance mode.

Rules:
- You must answer strictly using the provided context.
- If the context does not contain the answer, respond with: "I do not know based on the provided context."
- Do not fabricate.
- Do not infer beyond the text.
- Do not use prior knowledge.

Context:
{context}

Question:
{query}
""".strip()
