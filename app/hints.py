"""Investigation hints: root-cause hypotheses for engineers, not customers.

This is a second, separate layer from app.explain. The diagnosis code
answers "what's wrong" and is stable and customer/support-facing. This
module answers "where should an engineer look" using finer-grained
evidence that the diagnosis code alone discards - still fully
rule-based, so it's deterministic and testable with no model involved.
"""

from app.checks import Diagnosis


def suggest_investigation(diagnosis: Diagnosis) -> list[str]:
    code = diagnosis.diagnosis_code
    evidence = diagnosis.evidence

    if code == "ENTITLEMENT_NOT_ACTIVATED":
        entitlement = evidence.get("entitlement")
        if entitlement is None:
            return [
                "No entitlement record exists for this product at all - "
                "provisioning was likely never triggered. Check whether "
                "the renewal event's fan-out actually published a "
                "provisioning message for this product."
            ]
        return [
            "An entitlement record exists but is inactive - provisioning "
            "was attempted but did not complete. Check the provisioning "
            "service's logs around the renewal event time for errors or "
            "timeouts.",
            "If this customer's plan bundles multiple products, check "
            "whether other products activated correctly - one inactive "
            "product alongside working ones suggests a partial failure "
            "in a fan-out call rather than a total outage.",
        ]

    if code == "RENEWAL_EVENT_MISSING":
        return [
            "Payment succeeded but no renewal event was ever recorded - "
            "check for a dropped message or a failed webhook between the "
            "billing service and the renewal orchestrator."
        ]

    if code == "RENEWED_AFTER_CANCELLATION":
        return [
            "A renewal succeeded after the subscription was already "
            "canceled - check for a race condition between the "
            "cancellation request and the renewal job, e.g. the renewal "
            "job reading a stale subscription record."
        ]

    if code == "PAYMENT_DECLINED":
        return [
            "This is a customer-facing issue, not a system bug - the "
            "next step is the customer updating their payment method, "
            "not an engineering investigation."
        ]

    return []
