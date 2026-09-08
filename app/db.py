import sqlite3

SCHEMA = """
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE subscriptions (
    account_id TEXT PRIMARY KEY,
    plan TEXT NOT NULL,
    status TEXT NOT NULL,
    renewal_date TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id)
);

CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    status TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id)
);

CREATE TABLE renewal_events (
    event_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    result TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id)
);

CREATE TABLE entitlements (
    account_id TEXT NOT NULL,
    product TEXT NOT NULL,
    active INTEGER NOT NULL,
    PRIMARY KEY (account_id, product),
    FOREIGN KEY (account_id) REFERENCES accounts (account_id)
);
"""

SEED = """
INSERT INTO accounts (account_id, email, status) VALUES
    ('acct-healthy', 'healthy@example.com', 'active'),
    ('acct-payment-declined', 'declined@example.com', 'active');

INSERT INTO subscriptions (account_id, plan, status, renewal_date) VALUES
    ('acct-healthy', 'total_protection', 'active', '2026-09-01'),
    ('acct-payment-declined', 'total_protection', 'active', '2026-09-01');

INSERT INTO payments (payment_id, account_id, status, occurred_at) VALUES
    ('pay-1', 'acct-healthy', 'succeeded', '2026-09-01T00:00:00'),
    ('pay-2', 'acct-payment-declined', 'declined', '2026-09-01T00:00:00');

INSERT INTO renewal_events (event_id, account_id, result, occurred_at) VALUES
    ('evt-1', 'acct-healthy', 'success', '2026-09-01T00:05:00'),
    ('evt-2', 'acct-payment-declined', 'failure', '2026-09-01T00:05:00');

INSERT INTO entitlements (account_id, product, active) VALUES
    ('acct-healthy', 'total_protection', 1),
    ('acct-payment-declined', 'total_protection', 1);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.executescript(SEED)
    return conn
