import os


def generate_answer(question, rag_hits):
    context = "\n".join(f"- {text}" for _, text, _ in rag_hits) or "- No matching policy was retrieved."
    try:
        from ollama import Client
        response = Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).chat(
            model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b"),
            messages=[{"role": "system", "content": "You are a careful support bot. Answer only from this RAG policy context. Never request passwords, OTPs, or full card numbers. Offer human handoff when unsure.\nRAG CONTEXT:\n" + context}, {"role": "user", "content": question}],
            options={"temperature": 0.2, "num_predict": 180},
        )
        return response["message"]["content"].strip()
    except Exception:
        return "The local model is unavailable. I can escalate this chat to a human agent with the full transcript."
