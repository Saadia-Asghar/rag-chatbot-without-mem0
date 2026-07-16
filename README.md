# RAG-only support bot (no Mem0)

**New to RAG?** Read [LEARNING_GUIDE.md](LEARNING_GUIDE.md), then use this repository as the no-long-term-memory comparison demo.

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

## Hybrid RAG embeddings (local, free)

This is not a keyword-only baseline. It tests hybrid semantic RAG locally, the closest free comparison to a Pinecone-based RAG setup:

1. A PDF, pasted document, or public website page is split into approximately 700-character chunks.
2. Local Ollama `nomic-embed-text` creates an embedding vector for every new chunk once.
3. SQLite stores each vector with its chunk and workspace/tenant ID.
4. For each customer question, the app creates one query embedding and combines semantic similarity (75%) with keyword similarity (25%).
5. Only the selected tenant’s chunks and approved shared chunks are eligible for retrieval.
6. The top three chunks and the question go to local `llama3.2:1b` to produce the answer.

This repository never retrieves personal customer history; that distinction lets it show the benefit of semantic company-knowledge retrieval without Mem0. If Ollama is unavailable, it falls back to keyword matching and preserves the handoff flow.

## Production mapping to Pinecone/GCP

| This demo | QuickTalk/GCP-style production service |
|---|---|
| SQLite vectors | Pinecone index/namespace with mandatory `tenant_id` metadata filter |
| `nomic-embed-text` | Approved production embedding endpoint/model |
| `llama3.2:1b` via local Ollama | Approved GCP-hosted answer LLM |
| SQLite chat and handoff packet | Managed case/audit database |

Do not use one unfiltered Pinecone index for every enterprise client’s documents. Customer identity must come from authentication, and tenant filters must be applied before retrieval results are returned.

## Cost-aware workflow

- Embed a knowledge chunk only when it is indexed or changed.
- Embed a customer question once per retrieval.
- Send only the top three chunks to the answer LLM.
- Build the human handoff deterministically from SQLite; it requires no additional LLM call.

### Local performance behaviour

On a CPU-only laptop, local embeddings can take several seconds for a new semantic query. The demo therefore uses a keyword-first cascade: clear policy-term matches return immediately; only weak/ambiguous wording uses a cached semantic embedding lookup. Duplicate-charge questions use a deterministic safe workflow and skip both the embedding and answer-LLM call. Open-ended answers are limited to two context chunks and 80 generated tokens, and Ollama keeps the answer model warm for 20 minutes.

## Grounded answers

Whenever the RAG pipeline retrieves knowledge chunks, the answer displays `Sources used:` with the document names/URLs. This is deliberate: a support answer should be auditable, and a missing source should lead to clarification or human handoff rather than an invented policy.

## Three public tenant test sources

The sidebar button **Load 3 public tenant demo sources** loads these single, public pages into separate workspaces:

| Workspace | Public source | Safe test questions |
|---|---|---|
| `nayatel-demo` | https://nayatel.com/faqs | “How can I pay my bill?” / “My Wi-Fi is slow.” |
| `shifa-demo` | https://www.shifa.com.pk/city/islamabad | “What patient guide information is available?” |
| `general-demo` | https://support.mozilla.org/en-US/kb/what-firefox-account | “What is a Firefox account?” |

Use the same customer wording in each workspace, then open **Last RAG retrieval (test evidence)**. The retrieved sources must belong only to the active workspace. The Shifa source is only a public information/tenant-isolation test: this demo must not diagnose, triage, or make medical decisions.
