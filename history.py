import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class History:
    def __init__(self, path):
        self.db = sqlite3.connect(Path(path), check_same_thread=False)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS chats(id INTEGER PRIMARY KEY, user_id TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, chat_id INTEGER, role TEXT, text TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS session_evidence(
                chat_id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
                completed_at TEXT NOT NULL, handoff_summary TEXT NOT NULL, memory_status TEXT NOT NULL
            );
        """)
        self.db.commit()
    def start(self, user_id):
        cursor = self.db.execute("INSERT INTO chats(user_id,created) VALUES(?,?)", (user_id, datetime.now(timezone.utc).isoformat()))
        self.db.commit(); return cursor.lastrowid
    def add(self, chat_id, role, text):
        self.db.execute("INSERT INTO messages(chat_id,role,text,created) VALUES(?,?,?,?)", (chat_id, role, text, datetime.now(timezone.utc).isoformat()))
        self.db.commit()
    def messages(self, chat_id): return self.db.execute("SELECT role,text,created FROM messages WHERE chat_id=? ORDER BY id", (chat_id,)).fetchall()
    def handoff(self, chat_id, user_id):
        transcript = "\n".join(f"[{at}] {role.upper()}: {text}" for role,text,at in self.messages(chat_id))
        return f"HUMAN HANDOFF\nCustomer: {user_id}\nMode: RAG-only (no long-term user memory)\n\nFULL TRANSCRIPT\n{transcript}"
    def save_session_evidence(self, chat_id, user_id, workspace_id, handoff_summary):
        self.db.execute("""
            INSERT INTO session_evidence(chat_id,user_id,workspace_id,completed_at,handoff_summary,memory_status)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(chat_id) DO UPDATE SET completed_at=excluded.completed_at,handoff_summary=excluded.handoff_summary
        """, (chat_id, user_id, workspace_id, datetime.now(timezone.utc).isoformat(), handoff_summary,
              "No Mem0: packet and transcript retained in SQLite."))
        self.db.commit()
    def recent_evidence(self, limit=10):
        return self.db.execute("SELECT chat_id,workspace_id,user_id,completed_at,memory_status FROM session_evidence ORDER BY completed_at DESC LIMIT ?",(limit,)).fetchall()
