PRAGMA journal_mode=wal;
PRAGMA auto_vacuum=FULL;
PRAGMA synchronuous=NORMAL;

CREATE TABLE IF NOT EXISTS users (
    username TEXT NOT NULL,
    pt TEXT NOT NULL,
    token TEXT NOT NULL,
    salted_secret_hash TEXT NOT NULL,
    -- timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- key
    UNIQUE(username, token)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_token ON users (token);