from pathlib import Path

import streamlit as st

from history import History
from llm_service import generate_answer
from rag import KnowledgeBase

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

st.set_page_config(page_title="QuickTalk-style RAG-only demo", layout="wide")
st.title("QuickTalk-style support demo — RAG only")
st.caption("Local Ollama + workspace knowledge base + current-session handoff. No long-term customer memory.")

if "history" not in st.session_state:
    st.session_state.history = History(DATA / "history.sqlite3")
if "kb" not in st.session_state:
    st.session_state.kb = KnowledgeBase(DATA / "knowledge.sqlite3")
if "chat" not in st.session_state:
    st.session_state.chat = None

with st.sidebar:
    st.header("Workspace setup")
    tenant = st.selectbox("Client workspace", ["nayatel-demo", "shifa-demo", "general-demo"])
    department = st.selectbox("Department", ["Billing", "Account support", "General support"])
    user = st.text_input("Customer ID (demo sign-in)", st.session_state.get("user", "customer-001"))
    if st.button("Sign in and start support", type="primary") and user.strip():
        st.session_state.user = user.strip()
        st.session_state.tenant = tenant
        st.session_state.department = department
        st.session_state.chat = st.session_state.history.start(f"{tenant}:{user.strip()}")
        st.session_state.escalated = False
        st.rerun()
    st.divider()
    st.subheader("Knowledge base setup")
    source = st.text_input("Document name", "support-policy")
    text = st.text_area("Paste support policy / FAQ text")
    if st.button("Index knowledge document"):
        added = st.session_state.kb.add(source, text, tenant)
        st.success(f"Indexed {added} new chunks for {tenant}.")
    st.caption("The KB is filtered by workspace. This demo has no personal-memory lookup.")

if not st.session_state.chat:
    st.info("Choose a workspace, customer, and department, then start a RAG-only support session.")
    st.stop()

history, chat, user = st.session_state.history, st.session_state.chat, st.session_state.user
st.info(f"Workspace: **{st.session_state.tenant}**  |  Department: **{st.session_state.department}**  |  Customer: **{user}**")

for role, text, _ in history.messages(chat):
    with st.chat_message(role):
        st.write(text)

question = st.chat_input("Example: I was charged twice for my bill")
if question:
    hits = st.session_state.kb.search(question, tenant_id=st.session_state.tenant)
    answer = generate_answer(question, hits)
    history.add(chat, "user", question)
    history.add(chat, "assistant", answer)
    st.rerun()

col1, col2 = st.columns(2)
if col1.button("Escalate to human agent", type="primary"):
    st.session_state.escalated = True
if col2.button("End session and prepare context"):
    st.session_state.escalated = True
if st.session_state.get("escalated"):
    st.warning("Current-session handoff packet ready. It is not saved as long-term memory.")
    packet = history.handoff(chat, user)
    history.save_session_evidence(chat, user, st.session_state.tenant, packet)
    st.text_area("Human-agent context", packet, height=320)

with st.expander("Persistent demo evidence (SQLite)"):
    st.caption("Each completed session retains its full transcript in messages and its final handoff packet in session_evidence.")
    evidence = history.recent_evidence()
    if evidence:
        st.dataframe(evidence, column_config={
            0: "Conversation", 1: "Workspace", 2: "Customer", 3: "Completed at", 4: "Memory result"
        }, hide_index=True, use_container_width=True)
    else:
        st.info("End or escalate one session to create evidence for your comparison.")

with st.expander("What this proves"):
    st.write("This baseline retrieves only workspace policy documents. Returning customers receive no personal-history context; each new chat starts without Mem0 memory.")
