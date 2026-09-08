from fastapi import FastAPI, HTTPException

from app.checks import diagnose_renewal
from app.explain import ClaudeExplainer, explain

app = FastAPI(title="Subscription Renewal Support Agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/diagnose/{account_id}")
def diagnose(account_id: str) -> dict:
    result = diagnose_renewal(account_id)
    return {
        "account_id": account_id,
        "diagnosis_code": result.diagnosis_code,
        "evidence": result.evidence,
    }


@app.get("/diagnose/{account_id}/explain")
def diagnose_and_explain(account_id: str) -> dict:
    result = diagnose_renewal(account_id)
    try:
        explanation = explain(result, ClaudeExplainer())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"explainer unavailable: {exc}") from exc
    return {
        "account_id": account_id,
        "diagnosis_code": result.diagnosis_code,
        "explanation": explanation,
        "evidence": result.evidence,
    }
