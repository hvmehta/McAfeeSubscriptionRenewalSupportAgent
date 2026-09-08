# Lessons

Notes from building this prototype, kept for interview prep and as a
record of *why* things are the way they are — not just what they are.

## CI/CD

- **CI (Continuous Integration)** means every push automatically runs
  your tests on a clean machine, so "works on my machine" can't hide a
  broken commit. **CD (Continuous Delivery/Deployment)** is the
  separate follow-on step that automatically ships passing code
  somewhere. This project has CI only — no CD — and that's an honest
  gap to state plainly if asked, not something to paper over.
- `.github/workflows/ci.yml`, piece by piece:
  - `on: push` / `pull_request` to `main` — two triggers, because a
    branch pushed elsewhere wouldn't fire the `push` rule, and PR
    checks need their own trigger.
  - `runs-on: ubuntu-latest` — a brand-new, empty VM per run. Proves
    the code works from a clean state, not just in an
    already-configured environment.
  - `actions/checkout@v4` — the VM starts with nothing on it, not even
    the repo. This clones it.
  - `actions/setup-python@v5` pinned to `3.11` — pinned so the
    pipeline can't silently drift from what was tested locally.
  - `pip install -r requirements.txt` — pinned dependency versions
    matter here for the same reason: an unpinned dependency could
    upgrade quietly and break something only in CI.
  - `pytest -v` — the actual gate. Non-zero exit fails the step, the
    job, and shows red on the commit.
- The pipeline was deliberately watched red *before* it was made
  green: the first commit pushed a test importing a module that didn't
  exist yet (`ModuleNotFoundError`), confirmed failing both locally
  and in the Actions tab, and only then was the real code written.
  That sequence is what makes "I built this" a true claim rather than
  a recited one.

## Git, from zero

Three commands, three separate jobs — not one atomic "save":

1. `git add <file>` — stage a file's current changes for the next
   snapshot. Nothing permanent yet.
2. `git commit -m "message"` — save everything staged as a permanent
   snapshot *locally*, with a message explaining why.
3. `git push` — upload local commits to GitHub. This is the step that
   actually triggers CI, since the workflow watches for pushes.

## Architecture: rules decide, the model explains

- The diagnosis is never made by an LLM. Deterministic SQL checks feed
  a plain rule-based classifier (`app/checks.py`) that returns a
  diagnosis code. This makes every diagnosis reproducible and testable
  with zero model involvement — you can run the whole suite with no
  API key and no network call.
- The LLM's only job (`app/explain.py`) is to turn an already-decided
  diagnosis into readable prose. It has no database handle — not as a
  policy, but structurally: the function's only input is a `Diagnosis`
  object (a code + an evidence dict), so there's nothing to write back
  to even if it wanted to. `test_explainer_module_has_no_database_access`
  enforces this by asserting the module's source never mentions
  `app.db`, `sqlite3`, or `get_connection` — a real, running test, not
  just a design claim.
- A third layer, `app/hints.py`, answers a different question for a
  different audience: not "what's wrong" (the diagnosis code, stable,
  customer/support-facing) but "where should an engineer look" — using
  finer-grained evidence the diagnosis code alone discards. It's
  rule-based too, for the same reason: deterministic, testable, no
  model needed to point at a root-cause category.
- The general shape, if asked to summarize the design in one sentence:
  **three layers, three audiences, and the only one touching a model
  has the smallest possible blast radius.**

## Why the schema looks the way it does

- Five (now six) tables, each representing a different subsystem's own
  version of the truth: `subscriptions` (customer intent),
  `payments` (billing), `renewal_events` (the renewal process's own
  log), `entitlements` (provisioning — does access actually work),
  `customers` (identity anchor).
- The interesting bugs are where two of these disagree. If "payment
  succeeded" and "renewal event succeeded" lived in the same table as
  one fact, a case like Riley Chen — subscription canceled but a
  renewal event still logged success — would be structurally
  impossible to represent. Splitting subsystems into separate tables
  that share a `customer_id` is what makes that class of bug
  detectable at all, not just a normalization nicety.
- **Entitlements matter specifically because they're the only table
  that reflects the customer's actual lived experience** — can they
  use the product right now — as opposed to every other table, which
  reflects internal bookkeeping. A customer can be fully "healthy"
  according to billing and renewal and still not be able to open the
  app. That gap is the single worst kind of support case: the customer
  is right, and every system the agent can see says they're wrong.

## "Paid but not provisioned" — real root causes

Real subscription/eCommerce systems hit this because billing and
provisioning are separate services talking over a network, not one
atomic operation:

1. **Dropped async messages** — billing publishes "provision this
   customer" to a queue; the consumer is down, crashes, or the message
   lands in an unmonitored dead-letter queue.
2. **Webhook failures from a payment processor** — the processor
   confirms the charge on its side, but the webhook telling the
   internal system never arrives (timeout, stale endpoint after a
   deploy, signature mismatch).
3. **Partial bundle failures** — a plan maps to several entitlement
   flags; a fan-out loop provisions two of three and the third silently
   fails without retry.
4. **Race conditions / non-idempotent retries** — a timeout marks a
   call "failed" when it actually succeeded downstream, or a retry
   creates a duplicate that gets deduplicated in a way that drops the
   real write.
5. **Load spikes at renewal time** — large batch renewals (e.g. the
   1st of the month) hit a rate limiter or circuit breaker, and
   requests get shed rather than queued durably.
6. **Migration/legacy edge cases** — customer ID mapping breaks
   between an old and new system during a migration or acquisition, so
   a valid payment matches no record on the provisioning side.

The honest limit of this prototype: `ENTITLEMENT_NOT_ACTIVATED` tells
you *that* one of these happened; distinguishing *which one* needs
real telemetry (queue depth, service logs, distributed traces) — the
JD's "observability" bullet, not something a demo schema can fake
convincingly.

## Data hygiene lessons (the ones that came from direct feedback)

- **Never encode the outcome into the ID.** `acct-payment-declined` as
  a seeded ID is a tell that the demo is scripted — a real support
  tool's account number never hints at what's wrong with the account.
  Fixed by moving to arbitrary IDs (`ACC-10391`) with the actual
  failure living only in the row data.
- **Use terminology consistently, and use the term a human would say.**
  Renamed `account` → `customer` everywhere (schema, code, API, UI,
  docs) because "account" is overloaded/internal-sounding, while
  "customer" is what a support agent actually says.
- **Give demo data a face.** Adding real-sounding names (Sam Taylor,
  Jordan Lee, etc.) and a "Select demo customer" UI label makes the
  demo readable to a human glancing at it, not just to someone who
  already knows the seed data by heart.

## Security lesson

A live Anthropic API key was pasted directly into this chat. It was
never written to a file or committed — used only as a transient
env var for one local test call — but pasting a real secret into a
chat transcript should be treated as exposure regardless of how
carefully it's handled afterward. Lesson: set secrets directly in your
own terminal (`$env:ANTHROPIC_API_KEY = "..."`) and never paste them
into a conversation, then rotate any key that was pasted anyway.

## Framing lesson: how to describe this project honestly

- It's **correctly simple** where it should be (the rule engine is
  five `if` statements — that's a feature, not a shortcut) and
  **genuinely a prototype** in scope (in-memory SQLite reseeded per
  call, no persistence, no auth, no deployment).
- The right sentence for the interview: *"a working prototype that
  demonstrates the architecture decision, built test-first with CI
  enforcing correctness — not a production system."* Overclaiming
  ("production-grade") invites a follow-up that exposes the gap;
  underselling ("just a toy") throws away the real signal in the
  testing discipline and the architecture's safety boundary.
- The actual complexity in this problem was never the rule engine —
  it's (1) proving the LLM explainer stays faithful to evidence, (2)
  handling multiple simultaneous faults on one customer, and (3)
  orchestrating which check to run next instead of running all of them
  unconditionally. None of that is built yet; naming the gap
  accurately is itself a signal of seniority.

## The meta-lesson

Watching someone else run `git push` and glancing at a green checkmark
is not the same as being able to defend the pipeline in a room. The
turning point in this project was insisting on typing the `git add` /
`git commit` / `git push` sequence personally and reading
`test_checks.py` line by line rather than accepting "it works" — that's
the difference between "I read about this" and "I did this."

---

# Future improvements

Roughly in order of what would matter most if this became a real
system, not a demo:

1. **Persistence.** Replace the in-memory SQLite reseeded on every
   call with a real database (even file-based SQLite, or Postgres) so
   state actually survives between requests.
2. **An evaluation harness for the explainer.** Automated checks that
   the LLM's prose never states a fact absent from the evidence bundle
   — this is the hardest and most valuable piece of the GenAI half of
   the role, and it's currently untested beyond "does it call the
   client correctly."
3. **Multi-fault evidence.** Right now `classify()` returns the first
   matching rule and stops. A real customer can have two things wrong
   at once (e.g. payment declined *and* entitlement lapsed from a
   previous cycle) — worth deciding whether to return a primary
   diagnosis, a ranked list, or all matches.
4. **Real observability.** Structured logs / traces across a billing →
   queue → provisioning path so `investigation_hints` could eventually
   point at an actual failed span instead of a generic hypothesis.
5. **An actual CD pipeline.** Extend `ci.yml` (or a second workflow)
   to deploy on a green `main` build — the natural next step now that
   CI is solid, and the one most directly tied to the JD's "CI/CD
   pipelines" bullet.
6. **Auth.** Nothing today restricts who can call `/diagnose/{id}` —
   fine for a local demo, not fine for anything with real customer
   data behind it.
7. **Orchestration over unconditional checks.** The four SQL checks
   always all run. A more agentic version would decide which check to
   run next based on prior results — closer to the JD's "autonomous
   agents with tool orchestration."
8. **Rate/cost controls on the explainer endpoint**, since it's the
   one path in the system that costs money per call.
