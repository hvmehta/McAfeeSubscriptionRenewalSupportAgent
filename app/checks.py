from dataclasses import dataclass, field

from app.db import get_connection


@dataclass
class Diagnosis:
    diagnosis_code: str
    evidence: dict = field(default_factory=dict)


def read_customer(conn, customer_id: str) -> dict | None:
    row = conn.execute(
        "SELECT customer_id, name, email, status FROM customers WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()
    return dict(row) if row else None


def verify_payment(conn, customer_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT payment_id, status, occurred_at
        FROM payments
        WHERE customer_id = ?
        ORDER BY occurred_at DESC
        LIMIT 1
        """,
        (customer_id,),
    ).fetchone()
    return dict(row) if row else None


def read_subscription_state(conn, customer_id: str) -> dict | None:
    row = conn.execute(
        "SELECT plan, status, renewal_date FROM subscriptions WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()
    return dict(row) if row else None


def read_renewal_event(conn, customer_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT event_id, result, occurred_at
        FROM renewal_events
        WHERE customer_id = ?
        ORDER BY occurred_at DESC
        LIMIT 1
        """,
        (customer_id,),
    ).fetchone()
    return dict(row) if row else None


def read_entitlement(conn, customer_id: str) -> dict | None:
    row = conn.execute(
        "SELECT product, active FROM entitlements WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()
    return dict(row) if row else None


def classify(
    payment: dict | None,
    subscription: dict | None,
    renewal_event: dict | None,
    entitlement: dict | None,
) -> str:
    if subscription is None:
        return "NO_SUBSCRIPTION"
    if payment is None:
        return "NO_PAYMENT_RECORD"
    if subscription["status"] == "canceled" and renewal_event is not None and renewal_event["result"] == "success":
        return "RENEWED_AFTER_CANCELLATION"
    if payment["status"] == "declined":
        return "PAYMENT_DECLINED"
    if renewal_event is None:
        return "RENEWAL_EVENT_MISSING"
    if renewal_event["result"] == "failure":
        return "RENEWAL_EVENT_FAILED"
    if entitlement is None or not entitlement["active"]:
        return "ENTITLEMENT_NOT_ACTIVATED"
    return "OK"


def diagnose_renewal(customer_id: str) -> Diagnosis:
    conn = get_connection()
    try:
        customer = read_customer(conn, customer_id)
        payment = verify_payment(conn, customer_id)
        subscription = read_subscription_state(conn, customer_id)
        renewal_event = read_renewal_event(conn, customer_id)
        entitlement = read_entitlement(conn, customer_id)
    finally:
        conn.close()

    diagnosis_code = classify(payment, subscription, renewal_event, entitlement)
    return Diagnosis(
        diagnosis_code=diagnosis_code,
        evidence={
            "customer": customer,
            "payment": payment,
            "subscription": subscription,
            "renewal_event": renewal_event,
            "entitlement": entitlement,
        },
    )
