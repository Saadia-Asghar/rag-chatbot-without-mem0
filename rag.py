"""Tenant-isolated hybrid RAG using free, local Ollama embeddings."""

import json
import math
import os
import re
import sqlite3
from collections import Counter
from functools import lru_cache


POLICIES = [
    ("billing", "For duplicate charges, collect the invoice reference, charge date, and amount. Never request a full card number."),
    ("account", "For account access, ask for the exact error message. Never request a password or one-time code."),
    ("handoff", "Escalate when the customer requests a human or the bot cannot safely resolve the issue."),
]


def _words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _keyword_score(query, document):
    q, d = Counter(_words(query)), Counter(_words(document))
    if not q or not d:
        return 0.0
    dot = sum(q[x] * d[x] for x in q.keys() & d.keys())
    return dot / math.sqrt(sum(x * x for x in q.values()) * sum(x * x for x in d.values()))


def _cosine(left, right):
    if not left or not right or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
    return sum(x * y for x, y in zip(left, right)) / denominator if denominator else 0.0


def _embed(texts):
    if not texts:
        return []
    try:
        from ollama import Client
        response = Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).embed(
            model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"), input=texts
        )
        return [[float(value) for value in vector] for vector in response["embeddings"]]
    except Exception:
        return []


@lru_cache(maxsize=256)
def _cached_query_embedding(query):
    vectors = _embed([query])
    return tuple(vectors[0]) if len(vectors) == 1 else ()


def retrieve(query, top_k=3):
    ranked = [(name, text, _keyword_score(query, text)) for name, text in POLICIES]
    return [row for row in sorted(ranked, key=lambda row: row[2], reverse=True) if row[2] > 0][:top_k]


class KnowledgeBase:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS chunks(source TEXT, text TEXT, tenant_id TEXT NOT NULL DEFAULT 'shared', embedding_json TEXT, UNIQUE(source,text,tenant_id))")
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(chunks)")}
        if "tenant_id" not in columns:
            self.db.execute("ALTER TABLE chunks ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'shared'")
        if "embedding_json" not in columns:
            self.db.execute("ALTER TABLE chunks ADD COLUMN embedding_json TEXT")
        self.db.executemany("INSERT OR IGNORE INTO chunks(source,text,tenant_id) VALUES(?,?,'shared')", POLICIES)
        self.db.commit()
        self._backfill()

    def _backfill(self):
        rows = self.db.execute("SELECT rowid,text FROM chunks WHERE embedding_json IS NULL").fetchall()
        vectors = _embed([text for _, text in rows])
        if len(vectors) == len(rows):
            self.db.executemany("UPDATE chunks SET embedding_json=? WHERE rowid=?", [(json.dumps(vector), rowid) for (rowid, _), vector in zip(rows, vectors)])
            self.db.commit()

    def add(self, source, text, tenant_id="shared"):
        clean = " ".join(text.split())
        if not source.strip() or not clean:
            return 0
        pieces = [clean[i:i + 700] for i in range(0, len(clean), 700)]
        vectors = _embed(pieces)
        values = [(source, piece, tenant_id, json.dumps(vector) if len(vectors) == len(pieces) else None) for piece, vector in zip(pieces, vectors)]
        if len(values) != len(pieces):
            values = [(source, piece, tenant_id, None) for piece in pieces]
        before = self.db.total_changes
        self.db.executemany("INSERT OR IGNORE INTO chunks(source,text,tenant_id,embedding_json) VALUES(?,?,?,?)", values)
        self.db.commit()
        return self.db.total_changes - before

    def search(self, query, top_k=3, tenant_id="shared"):
        if not query.strip() or top_k <= 0:
            return []
        self._backfill()
        rows = self.db.execute("SELECT source,text,embedding_json FROM chunks WHERE tenant_id IN (?, 'shared')", (tenant_id,)).fetchall()
        keyword_hits = [(name, text, _keyword_score(query, text)) for name, text, _ in rows]
        if keyword_hits and max(hit[2] for hit in keyword_hits) >= .05:
            return [hit for hit in sorted(keyword_hits, key=lambda item: item[2], reverse=True) if hit[2] > 0][:top_k]
        query_vector = list(_cached_query_embedding(query))
        hits = []
        for name, text, raw_vector in rows:
            keyword = _keyword_score(query, text)
            try:
                semantic = _cosine(query_vector, json.loads(raw_vector)) if query_vector and raw_vector else 0.0
            except (TypeError, ValueError):
                semantic = 0.0
            score = .75 * semantic + .25 * keyword if query_vector and raw_vector else keyword
            if score > 0:
                hits.append((name, text, score))
        return sorted(hits, key=lambda item: item[2], reverse=True)[:top_k]
