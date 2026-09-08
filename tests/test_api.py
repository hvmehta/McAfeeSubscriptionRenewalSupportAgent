from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_diagnose_payment_declined():
    response = client.get("/diagnose/acct-payment-declined")
    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis_code"] == "PAYMENT_DECLINED"
    assert body["evidence"]["payment"]["status"] == "declined"


def test_diagnose_healthy_account():
    response = client.get("/diagnose/acct-healthy")
    assert response.status_code == 200
    assert response.json()["diagnosis_code"] == "OK"
