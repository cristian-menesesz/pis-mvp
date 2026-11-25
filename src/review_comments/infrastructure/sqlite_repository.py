import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from review_comments.domain.geometry import BoundingBox
from review_comments.domain.models import Comment, ItemVersion, NewComment, Round, RoundStatus
from review_comments.infrastructure.schema import SCHEMA


def to_db_time(moment: datetime) -> str:
    """Fixed-width UTC text, so comparing stored timestamps as strings in SQL
    gives the same order as comparing the moments themselves."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


class SqliteCommentRepository:
    """CommentRepository backed by a SQLite file.

    Each operation opens its own connection, so the repository can be shared
    by concurrent request threads. Connections run in autocommit mode: every
    statement is its own transaction, which is what makes the conditional
    insert below atomic.
    """

    def __init__(self, db_path: str | Path, timeout_seconds: float = 5.0) -> None:
        self._db_path = str(db_path)
        self._timeout = timeout_seconds

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path, timeout=self._timeout, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def get_round(self, round_id: str) -> Round | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, status, closed_at FROM rounds WHERE id = ?", (round_id,)
            ).fetchone()
        return _to_round(row) if row else None

    def get_version(self, version_id: str) -> ItemVersion | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, item_id, width, height FROM item_versions WHERE id = ?",
                (version_id,),
            ).fetchone()
        if row is None:
            return None
        return ItemVersion(
            id=row["id"], item_id=row["item_id"], width=row["width"], height=row["height"]
        )

    def get_comment(self, comment_id: int) -> Comment | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
        return _to_comment(row) if row else None

    def add_comment_if_round_open(self, comment: NewComment) -> Comment | None:
        # Check-and-write in a single statement: there is no window in which
        # the round can be closed after it was seen open and before the insert.
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO comments (round_id, item_id, version_id,
                                      box_x, box_y, box_width, box_height,
                                      text, reviewer_name, created_at)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                WHERE EXISTS (SELECT 1 FROM rounds WHERE id = ? AND status = 'open')
                """,
                (
                    comment.round_id,
                    comment.item_id,
                    comment.version_id,
                    comment.region.x,
                    comment.region.y,
                    comment.region.width,
                    comment.region.height,
                    comment.text,
                    comment.reviewer_name,
                    to_db_time(comment.created_at),
                    comment.round_id,
                ),
            )
            if cursor.rowcount == 0:
                return None
            comment_id = cursor.lastrowid
        assert comment_id is not None
        return Comment(
            id=comment_id,
            round_id=comment.round_id,
            item_id=comment.item_id,
            version_id=comment.version_id,
            region=comment.region,
            text=comment.text,
            reviewer_name=comment.reviewer_name,
            created_at=comment.created_at,
        )

    def close_round(self, round_id: str, closed_at: datetime) -> Round | None:
        with self.connect() as conn:
            # Only an open round changes; repeating the call keeps the first closed_at.
            # The clock was read before this write was serialized, so a comment
            # committed in between may carry a later timestamp. closed_at takes
            # the later of both, keeping every accepted comment at or before the
            # close in the stored history (DEF-02). One statement: no comment can
            # be inserted between reading max(created_at) and closing.
            conn.execute(
                """
                UPDATE rounds
                SET status = 'closed',
                    closed_at = max(:closed_at,
                                    coalesce((SELECT max(created_at) FROM comments
                                              WHERE round_id = :round_id), :closed_at))
                WHERE id = :round_id AND status = 'open'
                """,
                {"closed_at": to_db_time(closed_at), "round_id": round_id},
            )
            row = conn.execute(
                "SELECT id, status, closed_at FROM rounds WHERE id = ?", (round_id,)
            ).fetchone()
        return _to_round(row) if row else None


def _to_round(row: sqlite3.Row) -> Round:
    closed_at = row["closed_at"]
    return Round(
        id=row["id"],
        status=RoundStatus(row["status"]),
        closed_at=datetime.fromisoformat(closed_at) if closed_at else None,
    )


def _to_comment(row: sqlite3.Row) -> Comment:
    return Comment(
        id=row["id"],
        round_id=row["round_id"],
        item_id=row["item_id"],
        version_id=row["version_id"],
        region=BoundingBox(
            x=row["box_x"], y=row["box_y"], width=row["box_width"], height=row["box_height"]
        ),
        text=row["text"],
        reviewer_name=row["reviewer_name"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
