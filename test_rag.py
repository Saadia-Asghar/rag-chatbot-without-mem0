from rag import retrieve

def test_billing_policy_retrieves():
    assert retrieve("I have a duplicate charge")[0][0] == "billing"
