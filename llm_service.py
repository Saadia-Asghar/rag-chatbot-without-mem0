import os


def fast_policy_answer(question):
    """Avoid a slow generation call for common high-risk billing questions."""
    lower = question.lower()
    if ("duplicate charge" in lower or "charged twice" in lower or "payment appeared twice" in lower
            or "double charge" in lower):
        return (
            "I can help investigate a possible duplicate charge. Please share the invoice reference, "
            "charge date, and amount; do not send your password, OTP, CVV, or full card number. "
            "If the charge needs manual review, I can transfer the case to a human agent."
        )
    return None


def generate_answer(question, rag_hits):
    fast_answer = fast_policy_answer(question)
    if fast_answer:
        return fast_answer
    if not rag_hits:
        return "I do not have matching approved support-policy context for that request. I can transfer this case to a human agent with the full transcript."
    context = "\n".join(f"- {text[:900]}" for _, text, _ in rag_hits[:2])
    try:
        from ollama import Client
        response = Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).chat(
            model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b"),
            messages=[{"role": "system", "content": "You are a careful support bot. Answer only from this RAG policy context. Never request passwords, OTPs, CVVs, or full card numbers. Reply in at most three short sentences. Offer human handoff when unsure.\nRAG CONTEXT:\n" + context}, {"role": "user", "content": question}],
            options={"temperature": 0.1, "num_predict": 80, "num_ctx": 2048},
            keep_alive=os.getenv("OLLAMA_KEEP_ALIVE", "20m"),
        )
        return response["message"]["content"].strip()
    except Exception:
        return "The local model is unavailable. I can escalate this chat to a human agent with the full transcript."
