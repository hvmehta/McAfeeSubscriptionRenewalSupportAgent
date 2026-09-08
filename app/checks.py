from dataclasses import dataclass, field

from app.db import get_connection


@dataclass
class Diagnosis:
    diagnosis_code: str
    evidence: dict = field(default_factory=dict)


def verify_payment(conn, account_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT payment_id, status, occurred_at
        FROM payments
        WHERE account_id = ?
        ORDER BY occurred_at DESC
        LIMIT 1
        """,
        (account_id,),
    ).fetchone()
    return dict(row) if row else None


def read_subscription_state(conn, account_id: str) -> dict | None:
    row = conn.execute(
        "SELECT plan, status, renewal_date FROM subscriptions WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    return dict(row) if row else None


def read_renewal_event(conn, account_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT event_id, result, occurred_at
        FROM renewal_events
        WHERE account_id = ?
        ORDER BY occurred_at DESC
        LIMIT 1
        """,
        (account_id,),
    ).fetchone()
    return dict(row) if row else None


def classify(payment: dict | None, subscription: dict | None, renewal_event: dict | None) -> str:
    if subscription is None:
        return "NO_SUBSCRIPTION"
    if payment is None:
        return "NO_PAYMENT_RECORD"
    if payment["status"] == "declined":
        return "PAYMENT_DECLINED"
    if renewal_event is not None and renewal_event["result"] == "failure":
        return "RENEWAL_EVENT_FAILED"
    return "OK"


def diagnose_renewal(account_id: str) -> Diagnosis:
    conn = get_connection()
    try:
        payment = verify_payment(conn, account_id)
        subscription = read_subscription_state(conn, account_id)
        renewal_event = read_renewal_event(conn, account_id)
    finally:
        conn.close()

    diagnosis_code = classify(payment, subscription, renewal_event)
    return Diagnosis(
        diagnosis_code=diagnosis_code,
        evidence={
            "payment": payment,
            "subscription": subscription,
            "renewal_event": renewal_event,
        },
    )
