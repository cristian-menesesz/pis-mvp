"""CommentRepository contract, run against the in-memory fake AND real SQLite.

The unit tests trust the fake; these tests check that the trust is earned: both
implementations must behave the same for the operations the service relies on.
Referential integrity (foreign keys, CHECKs) is deliberately storage-only and is
verified in tests/failure (F-03), not here.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from review_comments.domain.geometry import BoundingBox
from review_comments.domain.models import ItemVersion, NewComment, Round, RoundStatus
from review_comments.infrastructure import seed
from review_comments.infrastructure.sqlite_repository import SqliteCommentRepository
from tests.conftest import comment_rows
from tests.unit.fakes import InMemoryCommentRepository

pytestmark = pytest.mark.contract

T0 = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


@pytest.fixture(params=["fake", "sqlite"])
def backend(request, db_path) -> tuple[object, Callable[[], int]]:
    """(repository, count_comments) with the same seeded state in both backends."""
    if request.param == "fake":
        repo = InMemoryCommentRepository(
            rounds=[
                Round(id=seed.OPEN_ROUND, status=RoundStatus.OPEN),
                Round(
                    id=seed.CLOSED_ROUND,
                    status=RoundStatus.CLOSED,
                    closed_at=datetime.fromisoformat(seed.CLOSED_AT),
                ),
            ],
            versions=[ItemVersion(id=seed.POSTER_V1, item_id=seed.POSTER, width=1200, height=800)],
        )
        return repo, lambda: len(repo.comments)
    repo = SqliteCommentRepository(db_path)
    seed.seed_demo_data(repo)
    return repo, lambda: len(comment_rows(repo))


def new_comment(round_id: str = seed.OPEN_ROUND, created_at: datetime = T0) -> NewComment:
    return NewComment(
        round_id=round_id,
        item_id=seed.POSTER,
        version_id=seed.POSTER_V1,
        region=BoundingBox(10.25, 20.5, 20.5, 19.625),
        text="  texto original  ",
        reviewer_name="Luis (fictitious)",
        created_at=created_at,
    )


def test_c01_add_on_closed_round_returns_none_and_stores_nothing(backend):
    repo, count = backend
    before = count()

    assert repo.add_comment_if_round_open(new_comment(round_id=seed.CLOSED_ROUND)) is None
    assert count() == before


def test_c02_stored_comment_round_trips_unchanged(backend):
    repo, _ = backend

    stored = repo.add_comment_if_round_open(new_comment())

    fetched = repo.get_comment(stored.id)
    assert fetched == stored
    assert fetched.region == BoundingBox(10.25, 20.5, 20.5, 19.625)
    assert fetched.text == "  texto original  "
    assert fetched.created_at == T0


def test_c03_close_is_idempotent_on_a_round_with_comments(backend):
    repo, count = backend
    repo.add_comment_if_round_open(new_comment(created_at=T0))
    before = count()

    first = repo.close_round(seed.OPEN_ROUND, T0 + timedelta(minutes=1))
    second = repo.close_round(seed.OPEN_ROUND, T0 + timedelta(minutes=9))

    assert first.status is RoundStatus.CLOSED
    assert first.closed_at == T0 + timedelta(minutes=1)
    assert second == first
    assert count() == before


def test_c04_closed_at_is_never_before_the_latest_accepted_comment(backend):
    repo, _ = backend
    repo.add_comment_if_round_open(new_comment(created_at=T0 + timedelta(seconds=1)))

    closed = repo.close_round(seed.OPEN_ROUND, T0)

    assert closed.closed_at == T0 + timedelta(seconds=1)


def test_c05_unknown_ids_return_none(backend):
    repo, _ = backend

    assert repo.get_round("missing") is None
    assert repo.get_version("missing") is None
    assert repo.get_comment(999999) is None
    assert repo.close_round("missing", T0) is None
