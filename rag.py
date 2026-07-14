import math
import re
from collections import Counter

POLICIES = [
    ("billing", "For duplicate charges, collect the invoice reference, charge date, and amount. Never request a full card number."),
    ("account", "For account access, ask for the exact error message. Never request a password or one-time code."),
    ("handoff", "Escalate when the customer requests a human or the bot cannot safely resolve the issue."),
]


def _words(text): return re.findall(r"[a-z0-9]+", text.lower())


def retrieve(query, top_k=3):
    q = Counter(_words(query))
    ranked = []
    for name, text in POLICIES:
        d = Counter(_words(text))
        dot = sum(q[x] * d[x] for x in q.keys() & d.keys())
        score = dot / math.sqrt(sum(x*x for x in q.values()) * sum(x*x for x in d.values())) if q and d else 0
        if score: ranked.append((name, text, score))
    return sorted(ranked, key=lambda row: row[2], reverse=True)[:top_k]
