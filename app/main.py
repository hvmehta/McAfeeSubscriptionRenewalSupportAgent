from fastapi import FastAPI

from app.checks import diagnose_renewal

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
