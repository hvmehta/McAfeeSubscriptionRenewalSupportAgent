# McAfee Subscription Renewal Support Agent

A prototype support-diagnosis tool for subscription renewal failures.
Given an account ID, it produces a diagnosis, the evidence behind it,
and (optionally) a plain-English explanation for a support agent.

## Design principle: rules decide, the model explains

The diagnosis is never made by an LLM. A set of deterministic SQL
checks reads payment, subscription, renewal, and entitlement records,
and a plain rule-based classifier turns that evidence into a diagnosis
code. This means every diagnosis is reproducible and testable with no
model involved at all.

The LLM's only job is to turn an already-decided diagnosis and its
evidence into readable prose for a human. It has no database handle —
enforced by [tests/test_explain.py](tests/test_explain.py), which
fails if `app/explain.py` ever imports `app.db` or `sqlite3`.

```
HTTP request → FastAPI → SQL evidence checks → rule-based classifier → diagnosis code
                                                                              │
                                                     (optional) → LLM explainer → prose
```

## What it diagnoses

| Diagnosis code             | Meaning                                                |
|-----------------------------|---------------------------------------------------------|
| `OK`                        | Renewal succeeded, nothing wrong                        |
| `PAYMENT_DECLINED`          | Latest payment attempt was declined                     |
| `RENEWAL_EVENT_MISSING`     | Payment succeeded but no renewal event was ever recorded|
| `RENEWAL_EVENT_FAILED`      | A renewal event exists and recorded failure             |
| `RENEWED_AFTER_CANCELLATION`| Renewal fired despite the subscription being canceled   |
| `ENTITLEMENT_NOT_ACTIVATED` | Renewal succeeded but entitlement never went active      |
| `NO_SUBSCRIPTION`           | No subscription record for this account                 |

## Running it

```bash
pip install -r requirements.txt
pytest -v                        # 12 tests, no external services required

uvicorn app.main:app --reload
# then open http://127.0.0.1:8000/docs
```

`GET /diagnose/{account_id}` runs the deterministic path only.
`GET /diagnose/{account_id}/explain` also calls Claude and requires
`ANTHROPIC_API_KEY` to be set.

Seeded account IDs to try: `acct-healthy`, `acct-payment-declined`,
`acct-canceled-renewed`, `acct-missing-renewal-event`,
`acct-lapsed-entitlement`.

## What this is (and isn't)

This is a working prototype demonstrating an architecture decision,
built test-first with CI enforcing correctness on every commit — not
a production system. Data is in-memory SQLite reseeded per call; there
is no persistence, auth, or deployment target yet.

## CI

Every push runs the full test suite via GitHub Actions
([.github/workflows/ci.yml](.github/workflows/ci.yml)). Check the
[Actions tab](../../actions) for history.
