from app.checks import diagnose_renewal


def test_payment_declined_is_detected():
    result = diagnose_renewal(account_id="acct-payment-declined")
    assert result.diagnosis_code == "PAYMENT_DECLINED"


def test_healthy_renewal_has_no_diagnosis():
    result = diagnose_renewal(account_id="acct-healthy")
    assert result.diagnosis_code == "WRONG"


def test_renewal_after_cancellation_is_detected():
    result = diagnose_renewal(account_id="acct-canceled-renewed")
    assert result.diagnosis_code == "RENEWED_AFTER_CANCELLATION"


def test_missing_renewal_event_is_detected():
    result = diagnose_renewal(account_id="acct-missing-renewal-event")
    assert result.diagnosis_code == "RENEWAL_EVENT_MISSING"


def test_lapsed_entitlement_is_detected():
    result = diagnose_renewal(account_id="acct-lapsed-entitlement")
    assert result.diagnosis_code == "ENTITLEMENT_NOT_ACTIVATED"


def test_unknown_account_has_no_subscription():
    result = diagnose_renewal(account_id="acct-does-not-exist")
    assert result.diagnosis_code == "NO_SUBSCRIPTION"
