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
    def handoff(self, chat_id, user_id, workspace_id="unknown"):
        """Create the agent-facing case packet from the current conversation only."""
        messages = self.messages(chat_id)
        customer_messages = [text for role, text, _ in messages if role == "user"]
        bot_messages = [text for role, text, _ in messages if role == "assistant"]
        latest_customer = customer_messages[-1] if customer_messages else "No customer request captured."
        facts = " | ".join(customer_messages[-3:]) or "No facts captured."
        bot_attempt = bot_messages[-1] if bot_messages else "No bot response captured."
        transcript = "\n".join(f"[{at}] {role.upper()}: {text}" for role, text, at in messages)
        return (
            "HUMAN HANDOFF SUMMARY\n"
            f"Workspace: {workspace_id}\n"
            f"Customer: {user_id}\n"
            "Mode: RAG-only baseline (no long-term customer memory)\n"
            "Unresolved: Needs human review\n"
            f"Customer goal / latest need: {latest_customer}\n"
            f"Facts supplied by customer: {facts}\n"
            f"What the bot last tried: {bot_attempt}\n"
            "Relevant prior memory: None — this baseline starts each new session without personal history.\n"
            "Escalation reason: The request needs human review or the customer asked for an agent.\n\n"
            "FULL TRANSCRIPT\n" + transcript
        )
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
