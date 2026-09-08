from typing import Protocol

from app.checks import Diagnosis

SYSTEM_PROMPT = (
    "You explain subscription renewal failures to support agents. "
    "Use ONLY the evidence provided below. Never state a fact that is "
    "not present in the evidence, and never guess at a cause not "
    "implied by the diagnosis code."
)


class Explainer(Protocol):
    def complete(self, system: str, prompt: str) -> str: ...


def build_prompt(diagnosis: Diagnosis) -> str:
    lines = [
        f"Diagnosis code: {diagnosis.diagnosis_code}",
        "Evidence:",
    ]
    for key, value in diagnosis.evidence.items():
        lines.append(f"- {key}: {value}")
    lines.append(
        "Write a 2-3 sentence explanation a support agent can read to a "
        "customer, describing what went wrong and what happens next."
    )
    return "\n".join(lines)


def explain(diagnosis: Diagnosis, client: Explainer) -> str:
    prompt = build_prompt(diagnosis)
    return client.complete(SYSTEM_PROMPT, prompt)


class ClaudeExplainer:
    """Explainer backed by the Claude API.

    Takes only a Diagnosis (diagnosis code + evidence dict) — it has no
    database handle and cannot query or write account data. The prompt
    it sends the model is entirely built from build_prompt().
    """

    def __init__(self, model: str = "claude-sonnet-5", api_key: str | None = None):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, system: str, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
