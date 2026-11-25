"""SQLite schema. Integrity rules that the storage can guarantee live here as
constraints, so they hold even for writes that bypass the service."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS rounds (
    id         TEXT PRIMARY KEY,
    status     TEXT NOT NULL CHECK (status IN ('open', 'closed')),
    closed_at  TEXT,
    CHECK ((status = 'open' AND closed_at IS NULL)
        OR (status = 'closed' AND closed_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS items (
    id    TEXT PRIMARY KEY,
    name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS item_versions (
    id       TEXT PRIMARY KEY,
    item_id  TEXT NOT NULL REFERENCES items (id),
    number   INTEGER NOT NULL CHECK (number >= 1),
    width    REAL NOT NULL CHECK (width > 0),
    height   REAL NOT NULL CHECK (height > 0),
    UNIQUE (item_id, number),
    UNIQUE (id, item_id)
);

CREATE TABLE IF NOT EXISTS comments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id       TEXT NOT NULL REFERENCES rounds (id),
    item_id        TEXT NOT NULL,
    version_id     TEXT NOT NULL,
    box_x          REAL NOT NULL CHECK (box_x >= 0),
    box_y          REAL NOT NULL CHECK (box_y >= 0),
    box_width      REAL NOT NULL CHECK (box_width >= 0),
    box_height     REAL NOT NULL CHECK (box_height >= 0),
    text           TEXT NOT NULL CHECK (length(trim(text)) > 0),
    reviewer_name  TEXT NOT NULL CHECK (length(trim(reviewer_name)) > 0),
    created_at     TEXT NOT NULL,
    FOREIGN KEY (version_id, item_id) REFERENCES item_versions (id, item_id)
);
"""
