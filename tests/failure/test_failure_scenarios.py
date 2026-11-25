"""Failure, repetition and integrity scenarios against the real SQLite storage."""

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from review_comments.api.app import create_app
from review_comments.application.service import AddCommentCommand, CommentService
from review_comments.domain.errors import RoundClosedError
from review_comments.domain.geometry import Point
from review_comments.domain.models import Round
from review_comments.infrastructure import seed
from review_comments.infrastructure.sqlite_repository import SqliteCommentRepository
from tests.conftest import comment_rows

pytestmark = pytest.mark.failure

T0 = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


def test_f01_repeated_close_does_not_change_the_closed_round(sqlite_repo, db_path):
    """RF-03: a retried close request must not move closed_at or touch comments."""
    ticks = iter([T0, T0 + timedelta(minutes=5)])
    client = TestClient(create_app(CommentService(sqlite_repo, clock=lambda: next(ticks))))
    comments_before = comment_rows(sqlite_repo)

    first = client.post(f"/rounds/{seed.OPEN_ROUND}/close")
    second = client.post(f"/rounds/{seed.OPEN_ROUND}/close")

    assert first.status_code == second.status_code == 200
    assert first.json() == {
        "id": seed.OPEN_ROUND,
        "status": "closed",
        "closed_at": "2026-11-24T12:00:00Z",
    }
    assert second.json() == first.json()
    assert SqliteCommentRepository(db_path).get_round(seed.OPEN_ROUND).closed_at == T0
    assert comment_rows(sqlite_repo) == comments_before


class CloseRightAfterCheck:
    """Wraps the real repository and closes the round, through the real storage,
    right after the service has read it as open. This forces deterministically
    the race window between 'check round is open' and 'insert comment' that two
    concurrent requests (reviewer submits / round closes) would open."""

    def __init__(self, real: SqliteCommentRepository) -> None:
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def get_round(self, round_id: str) -> Round | None:
        seen = self._real.get_round(round_id)
        self._real.close_round(round_id, T0)
        return seen


def test_f02_round_closed_during_submission_stores_no_comment(sqlite_repo):
    service = CommentService(CloseRightAfterCheck(sqlite_repo), clock=lambda: T0)
    comments_before = comment_rows(sqlite_repo)

    with pytest.raises(RoundClosedError):
        service.add_comment(
            AddCommentCommand(
                round_id=seed.OPEN_ROUND,
                item_id=seed.POSTER,
                version_id=seed.POSTER_V1,
                stroke=[Point(10, 10), Point(80, 40)],
                text="Comentario enviado mientras se cerraba la ronda",
                reviewer_name="Luis (fictitious)",
            )
        )

    assert comment_rows(sqlite_repo) == comments_before
    assert sqlite_repo.get_round(seed.OPEN_ROUND).is_open is False


def test_f04_closing_time_is_never_earlier_than_an_accepted_comment(sqlite_repo, db_path):
    """DEF-02: the close request reads its clock before its write is serialized,
    so a comment committed in between can carry a later timestamp. The stored
    history must still show every accepted comment at or before closed_at."""
    comment_time = T0 + timedelta(seconds=1)
    CommentService(sqlite_repo, clock=lambda: comment_time).add_comment(
        AddCommentCommand(
            round_id=seed.OPEN_ROUND,
            item_id=seed.POSTER,
            version_id=seed.POSTER_V1,
            stroke=[Point(5, 5)],
            text="Llegó justo antes del cierre",
            reviewer_name="Luis (fictitious)",
        )
    )

    closed = CommentService(sqlite_repo, clock=lambda: T0).close_round(seed.OPEN_ROUND)

    assert closed.closed_at >= comment_time
    stored = SqliteCommentRepository(db_path).get_round(seed.OPEN_ROUND)
    assert stored.closed_at == closed.closed_at


@pytest.mark.parametrize(
    ("column", "value", "constraint"),
    [
        pytest.param("text", "   ", r"CHECK constraint failed: length\(trim\(text\)\)", id="blank-text"),
        pytest.param(
            "version_id", seed.BROCHURE_V1, "FOREIGN KEY constraint failed", id="version-of-other-item"
        ),
        pytest.param("box_width", -1, "CHECK constraint failed: box_width >= 0", id="negative-width"),
    ],
)
def test_f03_storage_rejects_invalid_rows_written_around_the_service(
    sqlite_repo, column, value, constraint
):
    """The schema is the last line of defence for writes that bypass the service."""
    row = {
        "round_id": seed.OPEN_ROUND,
        "item_id": seed.POSTER,
        "version_id": seed.POSTER_V1,
        "box_x": 0,
        "box_y": 0,
        "box_width": 10,
        "box_height": 10,
        "text": "ok",
        "reviewer_name": "Luis (fictitious)",
        "created_at": T0.isoformat(),
        column: value,
    }
    comments_before = comment_rows(sqlite_repo)

    with sqlite_repo.connect() as conn, pytest.raises(sqlite3.IntegrityError, match=constraint):
        conn.execute(
            f"INSERT INTO comments ({', '.join(row)}) VALUES ({', '.join('?' * len(row))})",
            tuple(row.values()),
        )

    assert comment_rows(sqlite_repo) == comments_before
