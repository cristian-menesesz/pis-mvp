"""Small, known, fictitious data set. Rounds, items and versions are created by
features outside this prototype's scope, so they are inserted directly."""

import sqlite3

from review_comments.infrastructure.sqlite_repository import SqliteCommentRepository

OPEN_ROUND = "round-open"
CLOSED_ROUND = "round-closed"
POSTER = "item-poster"
POSTER_V1 = "poster-v1"  # 1200 x 800
BROCHURE = "item-brochure"
BROCHURE_V1 = "brochure-v1"  # 600 x 900
CLOSED_AT = "2026-11-20T18:00:00+00:00"


def insert_round(conn: sqlite3.Connection, round_id: str, closed_at: str | None = None) -> None:
    status = "closed" if closed_at else "open"
    conn.execute(
        "INSERT INTO rounds (id, status, closed_at) VALUES (?, ?, ?)",
        (round_id, status, closed_at),
    )


def insert_item_version(
    conn: sqlite3.Connection,
    item_id: str,
    version_id: str,
    width: float,
    height: float,
    number: int = 1,
) -> None:
    conn.execute("INSERT OR IGNORE INTO items (id, name) VALUES (?, ?)", (item_id, item_id))
    conn.execute(
        "INSERT INTO item_versions (id, item_id, number, width, height) VALUES (?, ?, ?, ?, ?)",
        (version_id, item_id, number, width, height),
    )


def seed_demo_data(repository: SqliteCommentRepository) -> None:
    """Initialize the schema and load the demo data set into an empty database."""
    repository.initialize()
    with repository.connect() as conn:
        insert_round(conn, OPEN_ROUND)
        insert_round(conn, CLOSED_ROUND, closed_at=CLOSED_AT)
        insert_item_version(conn, POSTER, POSTER_V1, width=1200, height=800)
        insert_item_version(conn, BROCHURE, BROCHURE_V1, width=600, height=900)
        # A comment made before the round was closed: rejections must leave it intact.
        conn.execute(
            """
            INSERT INTO comments (round_id, item_id, version_id, box_x, box_y, box_width,
                                  box_height, text, reviewer_name, created_at)
            VALUES (?, ?, ?, 40, 60, 200, 120, 'Make the logo bigger', 'Ana (fictitious)',
                    '2026-11-20T17:30:00+00:00')
            """,
            (CLOSED_ROUND, POSTER, POSTER_V1),
        )
