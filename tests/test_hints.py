from app.checks import diagnose_renewal
from app.hints import suggest_investigation


def test_missing_entitlement_record_suggests_provisioning_never_triggered():
    result = diagnose_renewal(customer_id="ACC-10945")
    assert result.diagnosis_code == "ENTITLEMENT_NOT_ACTIVATED"

    hints = suggest_investigation(result)
    assert len(hints) == 1
    assert "never triggered" in hints[0]


def test_inactive_entitlement_record_suggests_provisioning_failed():
    result = diagnose_renewal(customer_id="ACC-10809")
    assert result.diagnosis_code == "ENTITLEMENT_NOT_ACTIVATED"

    hints = suggest_investigation(result)
    assert len(hints) == 2
    assert "attempted but did not complete" in hints[0]
    assert "partial failure" in hints[1]


def test_renewal_event_missing_points_at_billing_to_orchestrator_gap():
    result = diagnose_renewal(customer_id="ACC-10662")
    hints = suggest_investigation(result)
    assert any("dropped message" in h or "failed webhook" in h for h in hints)


def test_renewed_after_cancellation_points_at_race_condition():
    result = diagnose_renewal(customer_id="ACC-10528")
    hints = suggest_investigation(result)
    assert any("race condition" in h for h in hints)


def test_payment_declined_is_flagged_as_customer_facing_not_a_bug():
    result = diagnose_renewal(customer_id="ACC-10391")
    hints = suggest_investigation(result)
    assert any("not a system bug" in h for h in hints)


def test_healthy_renewal_has_no_hints():
    result = diagnose_renewal(customer_id="ACC-10234")
    assert suggest_investigation(result) == []
