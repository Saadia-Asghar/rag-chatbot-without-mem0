from history import History


def test_history_and_handoff_evidence_survive_reopen(tmp_path):
    path = tmp_path / "history.sqlite3"
    history = History(path)
    chat = history.start("nayatel-demo:demo-billing-001")
    history.add(chat, "user", "My duplicate charge is still unresolved")
    history.add(chat, "assistant", "Please share the invoice reference and amount.")
    packet = history.handoff(chat, "demo-billing-001", "nayatel-demo")
    history.save_session_evidence(chat, "demo-billing-001", "nayatel-demo", packet)

    reopened = History(path)
    assert "duplicate charge" in reopened.messages(chat)[0][1]
    evidence = reopened.recent_evidence()
    assert evidence[0][1:3] == ("nayatel-demo", "demo-billing-001")
