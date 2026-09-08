from app.checks import diagnose_renewal


def test_payment_declined_is_detected():
    result = diagnose_renewal(customer_id="ACC-10391")
    assert result.diagnosis_code == "PAYMENT_DECLINED"


def test_healthy_renewal_has_no_diagnosis():
    result = diagnose_renewal(customer_id="ACC-10234")
    assert result.diagnosis_code == "OK"


def test_renewal_after_cancellation_is_detected():
    result = diagnose_renewal(customer_id="ACC-10528")
    assert result.diagnosis_code == "RENEWED_AFTER_CANCELLATION"


def test_missing_renewal_event_is_detected():
    result = diagnose_renewal(customer_id="ACC-10662")
    assert result.diagnosis_code == "RENEWAL_EVENT_MISSING"


def test_lapsed_entitlement_is_detected():
    result = diagnose_renewal(customer_id="ACC-10809")
    assert result.diagnosis_code == "ENTITLEMENT_NOT_ACTIVATED"


def test_missing_entitlement_record_is_also_not_activated():
    result = diagnose_renewal(customer_id="ACC-10945")
    assert result.diagnosis_code == "ENTITLEMENT_NOT_ACTIVATED"
    assert result.evidence["entitlement"] is None


def test_unknown_customer_has_no_subscription():
    result = diagnose_renewal(customer_id="ACC-99999")
    assert result.diagnosis_code == "NO_SUBSCRIPTION"
