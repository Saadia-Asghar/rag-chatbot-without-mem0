import math
import re
import sqlite3
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


class KnowledgeBase:
    def __init__(self, path):
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS chunks(source TEXT, text TEXT, UNIQUE(source,text))")
        self.db.executemany("INSERT OR IGNORE INTO chunks VALUES(?,?)",POLICIES); self.db.commit()
    def add(self,source,text):
        clean=" ".join(text.split())
        if not source.strip() or not clean:return 0
        before=self.db.total_changes
        self.db.executemany("INSERT OR IGNORE INTO chunks VALUES(?,?)",[(source,clean[i:i+700]) for i in range(0,len(clean),700)])
        self.db.commit();return self.db.total_changes-before
    def search(self,query,top_k=3):
        q=Counter(_words(query)); hits=[]
        for name,text in self.db.execute("SELECT source,text FROM chunks"):
            d=Counter(_words(text)); dot=sum(q[x]*d[x] for x in q.keys()&d.keys()); score=dot/math.sqrt(sum(x*x for x in q.values())*sum(x*x for x in d.values())) if q and d else 0
            if score:hits.append((name,text,score))
        return sorted(hits,key=lambda x:x[2],reverse=True)[:top_k]
