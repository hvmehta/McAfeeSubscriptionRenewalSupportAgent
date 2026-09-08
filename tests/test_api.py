from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_diagnose_payment_declined():
    response = client.get("/diagnose/ACC-10391")
    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis_code"] == "PAYMENT_DECLINED"
    assert body["evidence"]["payment"]["status"] == "declined"
    assert len(body["investigation_hints"]) == 1


def test_diagnose_healthy_customer():
    response = client.get("/diagnose/ACC-10234")
    assert response.status_code == 200
    assert response.json()["diagnosis_code"] == "OK"


def test_list_customers_returns_seeded_customers():
    response = client.get("/customers")
    assert response.status_code == 200
    body = response.json()
    customer_ids = {row["customer_id"] for row in body}
    assert "ACC-10234" in customer_ids
    assert all("name" in row for row in body)
