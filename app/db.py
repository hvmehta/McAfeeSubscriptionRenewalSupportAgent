import sqlite3

SCHEMA = """
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE subscriptions (
    customer_id TEXT PRIMARY KEY,
    plan TEXT NOT NULL,
    status TEXT NOT NULL,
    renewal_date TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    status TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE renewal_events (
    event_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    result TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE entitlements (
    customer_id TEXT NOT NULL,
    product TEXT NOT NULL,
    active INTEGER NOT NULL,
    PRIMARY KEY (customer_id, product),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);
"""

# Fictional demo customers. IDs are arbitrary customer numbers and carry
# no meaning of their own - the failure each one demonstrates lives in
# the subscriptions/payments/renewal_events/entitlements rows below, not
# in the ID string. This mirrors a real support tool, where a customer
# number never hints at what's wrong with the customer.
SEED = """
INSERT INTO customers (customer_id, name, email, status) VALUES
    ('ACC-10234', 'Sam Taylor', 'sam.taylor@example.com', 'active'),
    ('ACC-10391', 'Jordan Lee', 'jordan.lee@example.com', 'active'),
    ('ACC-10528', 'Riley Chen', 'riley.chen@example.com', 'active'),
    ('ACC-10662', 'Morgan Patel', 'morgan.patel@example.com', 'active'),
    ('ACC-10809', 'Casey Nguyen', 'casey.nguyen@example.com', 'active'),
    ('ACC-10945', 'Avery Brooks', 'avery.brooks@example.com', 'active');

INSERT INTO subscriptions (customer_id, plan, status, renewal_date) VALUES
    ('ACC-10234', 'total_protection', 'active', '2026-09-01'),
    ('ACC-10391', 'total_protection', 'active', '2026-09-01'),
    ('ACC-10528', 'total_protection', 'canceled', '2026-09-01'),
    ('ACC-10662', 'total_protection', 'active', '2026-09-01'),
    ('ACC-10809', 'total_protection', 'active', '2026-09-01'),
    ('ACC-10945', 'total_protection', 'active', '2026-09-01');

INSERT INTO payments (payment_id, customer_id, status, occurred_at) VALUES
    ('PAY-88201', 'ACC-10234', 'succeeded', '2026-09-01T00:00:00'),
    ('PAY-88202', 'ACC-10391', 'declined', '2026-09-01T00:00:00'),
    ('PAY-88203', 'ACC-10528', 'succeeded', '2026-09-01T00:00:00'),
    ('PAY-88204', 'ACC-10662', 'succeeded', '2026-09-01T00:00:00'),
    ('PAY-88205', 'ACC-10809', 'succeeded', '2026-09-01T00:00:00'),
    ('PAY-88206', 'ACC-10945', 'succeeded', '2026-09-01T00:00:00');

INSERT INTO renewal_events (event_id, customer_id, result, occurred_at) VALUES
    ('EVT-55101', 'ACC-10234', 'success', '2026-09-01T00:05:00'),
    ('EVT-55102', 'ACC-10391', 'failure', '2026-09-01T00:05:00'),
    ('EVT-55103', 'ACC-10528', 'success', '2026-09-01T00:05:00'),
    ('EVT-55105', 'ACC-10809', 'success', '2026-09-01T00:05:00'),
    ('EVT-55106', 'ACC-10945', 'success', '2026-09-01T00:05:00');

-- Note: ACC-10945 has no entitlement row at all - provisioning was
-- never triggered, as opposed to ACC-10809 below, whose entitlement
-- row exists but is inactive - provisioning was attempted and failed.
-- Both reach the same ENTITLEMENT_NOT_ACTIVATED diagnosis; the
-- investigation-hints layer (app/hints.py) is what tells them apart.
INSERT INTO entitlements (customer_id, product, active) VALUES
    ('ACC-10234', 'total_protection', 1),
    ('ACC-10391', 'total_protection', 1),
    ('ACC-10528', 'total_protection', 1),
    ('ACC-10662', 'total_protection', 1),
    ('ACC-10809', 'total_protection', 0);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.executescript(SEED)
    return conn


def list_customers() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT customer_id, name FROM customers ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
