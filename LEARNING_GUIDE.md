# RAG-Only Demo: Beginner Learning Note

This repository is the comparison version of the project. It deliberately has **no Mem0 long-term customer memory**.

Read the complete beginner guide in the companion Mem0 repository: [RAG, Agents, Mem0, and Human Handoff Guide](https://github.com/Saadia-Asghar/rag-chatbot/blob/main/LEARNING_GUIDE.md).

## What this version teaches

1. **Knowledge base ingestion**: add text, PDFs, or public web pages to a workspace.
2. **Embeddings**: local `nomic-embed-text` converts chunks and questions into vectors.
3. **RAG retrieval**: only relevant chunks from the active workspace are retrieved.
4. **Local LLM answer**: `llama3.2:1b` writes an answer based on the retrieved support material.
5. **Current-session handoff**: SQLite retains the transcript and creates a specific packet for the human agent.

This repository answers: “Can RAG answer from the right tenant knowledge and hand off the current conversation?”

The Mem0 repository adds the separate question: “Can a returning customer safely carry an approved case summary into a new session?”

Run this comparison demo with:

```powershell
cd C:\Users\HP\Documents\Codex\2026-07-14\bu\work\rag-chatbot-without-mem0
streamlit run app.py --server.port 8504
```
