from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.checks import diagnose_renewal
from app.db import list_customers
from app.explain import ClaudeExplainer, explain
from app.hints import suggest_investigation

app = FastAPI(title="Subscription Renewal Support Agent")
app.mount("/ui", StaticFiles(directory="app/static", html=True), name="ui")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/customers")
def customers() -> list[dict]:
    return list_customers()


@app.get("/diagnose/{customer_id}")
def diagnose(customer_id: str) -> dict:
    result = diagnose_renewal(customer_id)
    return {
        "customer_id": customer_id,
        "diagnosis_code": result.diagnosis_code,
        "evidence": result.evidence,
        "investigation_hints": suggest_investigation(result),
    }


@app.get("/diagnose/{customer_id}/explain")
def diagnose_and_explain(customer_id: str) -> dict:
    result = diagnose_renewal(customer_id)
    try:
        explanation = explain(result, ClaudeExplainer())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"explainer unavailable: {exc}") from exc
    return {
        "customer_id": customer_id,
        "diagnosis_code": result.diagnosis_code,
        "explanation": explanation,
        "evidence": result.evidence,
        "investigation_hints": suggest_investigation(result),
    }
