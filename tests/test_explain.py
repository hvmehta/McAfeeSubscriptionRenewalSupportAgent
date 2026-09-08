import inspect

import app.explain as explain_module
from app.checks import Diagnosis
from app.explain import build_prompt, explain


class FakeClient:
    def __init__(self, response: str = "canned response"):
        self.response = response
        self.calls = []

    def complete(self, system: str, prompt: str) -> str:
        self.calls.append((system, prompt))
        return self.response


def test_build_prompt_includes_diagnosis_code_and_evidence():
    diagnosis = Diagnosis(
        diagnosis_code="PAYMENT_DECLINED",
        evidence={"payment": {"status": "declined"}},
    )
    prompt = build_prompt(diagnosis)
    assert "PAYMENT_DECLINED" in prompt
    assert "declined" in prompt


def test_explain_delegates_to_client_with_evidence_grounded_prompt():
    diagnosis = Diagnosis(
        diagnosis_code="ENTITLEMENT_NOT_ACTIVATED",
        evidence={"entitlement": {"active": 0}},
    )
    client = FakeClient(response="Your entitlement was never activated.")

    result = explain(diagnosis, client)

    assert result == "Your entitlement was never activated."
    assert len(client.calls) == 1
    system, prompt = client.calls[0]
    assert "ONLY the evidence" in system
    assert "ENTITLEMENT_NOT_ACTIVATED" in prompt


def test_explainer_module_has_no_database_access():
    source = inspect.getsource(explain_module)
    assert "app.db" not in source
    assert "sqlite3" not in source
    assert "get_connection" not in source
