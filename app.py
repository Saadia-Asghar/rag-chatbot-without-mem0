from pathlib import Path
import streamlit as st
from history import History
from llm_service import generate_answer
from rag import KnowledgeBase, retrieve

ROOT = Path(__file__).parent; DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
st.set_page_config(page_title="RAG-only support bot", layout="wide")
st.title("RAG-only support bot — no Mem0")
st.caption("Local Ollama answer model + local policy RAG + full human handoff. No long-term user memory.")
if "history" not in st.session_state: st.session_state.history = History(DATA / "history.sqlite3")
if "kb" not in st.session_state: st.session_state.kb = KnowledgeBase(DATA / "knowledge.sqlite3")
if "chat" not in st.session_state: st.session_state.chat = None
with st.sidebar:
    user = st.text_input("Customer ID (demo sign-in)", st.session_state.get("user", "customer-001"))
    if st.button("Sign in and start support", type="primary") and user.strip():
        st.session_state.user=user.strip(); st.session_state.chat=st.session_state.history.start(user.strip()); st.session_state.escalated=False; st.rerun()
    st.divider(); st.subheader("Knowledge base setup")
    source=st.text_input("Document name","support-policy")
    text=st.text_area("Paste support policy / FAQ text")
    if st.button("Index knowledge document"): st.success(f"Indexed {st.session_state.kb.add(source,text)} new chunks.")
if not st.session_state.chat:
    st.info("Sign in to start a RAG-only support session."); st.stop()
history, chat, user = st.session_state.history, st.session_state.chat, st.session_state.user
for role,text,_ in history.messages(chat):
    with st.chat_message(role): st.write(text)
question = st.chat_input("Example: I was charged twice for my bill")
if question:
    hits = st.session_state.kb.search(question); answer = generate_answer(question, hits)
    history.add(chat,"user",question); history.add(chat,"assistant",answer); st.rerun()
if st.button("Escalate to human agent", type="primary"): st.session_state.escalated=True
if st.session_state.get("escalated"): st.text_area("Human-agent context",history.handoff(chat,user),height=320)
with st.expander("What this proves"):
    st.write("This baseline retrieves only policy documents. Returning customers receive no personal-history context; each new chat starts without Mem0 memory.")
