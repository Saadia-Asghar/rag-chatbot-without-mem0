# RAG-only support bot (no Mem0)

This is the baseline for comparing against [rag-chatbot](https://github.com/Saadia-Asghar/rag-chatbot).

| Capability | This repository | With-Mem0 repository |
|---|---:|---:|
| Policy-document RAG | Yes | Yes |
| Local Ollama answer model | Yes | Yes |
| Long-term user memory | No | Yes, Mem0 OSS + Chroma |
| Returning-user welcome | No | Yes |
| Full human handoff transcript | Yes | Yes |

## Run

Use the already-running local Ollama service and model:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Comparison test

1. Sign in as `alice`, report a duplicate charge, then open a new session as `alice`.
2. In this RAG-only app, the bot cannot know her earlier issue.
3. Repeat in the with-Mem0 app. It can retrieve Alice's prior memory and give a return-user welcome.
4. In both apps, request a human agent and compare the complete handoff transcript.
