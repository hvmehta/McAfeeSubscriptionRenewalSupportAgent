from app.checks import diagnose_renewal


def test_payment_declined_is_detected():
    result = diagnose_renewal(account_id="acct-payment-declined")
    assert result.diagnosis_code == "PAYMENT_DECLINED"


def test_healthy_renewal_has_no_diagnosis():
    result = diagnose_renewal(account_id="acct-healthy")
    assert result.diagnosis_code == "OK"
