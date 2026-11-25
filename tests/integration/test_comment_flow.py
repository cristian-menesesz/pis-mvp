"""Integration: HTTP API -> CommentService -> SqliteCommentRepository -> SQLite file.

Nothing is simulated except the clock. State is checked through a separate
connection, not through the object that performed the write.
"""

import pytest

from review_comments.infrastructure import seed
from review_comments.infrastructure.sqlite_repository import SqliteCommentRepository
from tests.conftest import FIXED_NOW, comment_rows

pytestmark = pytest.mark.integration


def test_i01_valid_comment_is_persisted_and_recoverable(client, db_path):
    before = comment_rows(SqliteCommentRepository(db_path))
    payload = {
        "item_id": seed.POSTER,
        "version_id": seed.POSTER_V1,
        "stroke": [{"x": 1100, "y": 700}, {"x": 1350, "y": 860}, {"x": 1150, "y": 760}],
        "text": "Esta esquina se ve vacía",
        "reviewer_name": "Luis (fictitious)",
    }

    response = client.post(f"/rounds/{seed.OPEN_ROUND}/comments", json=payload)

    assert response.status_code == 201
    created = response.json()
    # Stroke crosses the right and bottom edges of the 1200 x 800 poster.
    assert created["region"] == {"x": 1100.0, "y": 700.0, "width": 100.0, "height": 100.0}

    # Recoverable through a brand-new repository instance (fresh connection).
    stored = SqliteCommentRepository(db_path).get_comment(created["id"])
    assert stored is not None
    assert stored.round_id == seed.OPEN_ROUND
    assert (stored.item_id, stored.version_id) == (seed.POSTER, seed.POSTER_V1)
    assert (stored.region.x, stored.region.y, stored.region.width, stored.region.height) == (
        1100,
        700,
        100,
        100,
    )
    assert stored.text == payload["text"]
    assert stored.reviewer_name == payload["reviewer_name"]
    assert stored.created_at == FIXED_NOW

    # Exactly one new row, and the read endpoint returns the same record.
    after = comment_rows(SqliteCommentRepository(db_path))
    assert len(after) == len(before) + 1
    assert client.get(f"/comments/{created['id']}").json() == created


@pytest.mark.parametrize(
    "bad_field",
    [
        pytest.param({"text": "   "}, id="rejected-by-domain"),
        pytest.param({"text": None}, id="rejected-by-request-schema"),
    ],
)
def test_i03_every_422_uses_the_same_error_contract(client, db_path, bad_field):
    """DEF-01: a 422 must have one body shape whatever layer rejected it."""
    before = comment_rows(SqliteCommentRepository(db_path))
    payload = {
        "item_id": seed.POSTER,
        "version_id": seed.POSTER_V1,
        "stroke": [{"x": 10, "y": 10}],
        "text": "ok",
        "reviewer_name": "Luis (fictitious)",
        **bad_field,
    }

    response = client.post(f"/rounds/{seed.OPEN_ROUND}/comments", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "invalid_comment"
    assert isinstance(body["detail"], str) and body["detail"]
    assert comment_rows(SqliteCommentRepository(db_path)) == before


def test_i02_comment_on_closed_round_is_rejected_and_existing_data_is_intact(client, db_path):
    repository = SqliteCommentRepository(db_path)
    comments_before = comment_rows(repository)
    round_before = repository.get_round(seed.CLOSED_ROUND)
    assert len(comments_before) == 1  # precondition: seeded comment on the closed round

    response = client.post(
        f"/rounds/{seed.CLOSED_ROUND}/comments",
        json={
            "item_id": seed.POSTER,
            "version_id": seed.POSTER_V1,
            "stroke": [{"x": 10, "y": 10}, {"x": 50, "y": 50}],
            "text": "Una observación tardía",
            "reviewer_name": "Luis (fictitious)",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"] == "round_closed"
    assert comment_rows(repository) == comments_before
    assert repository.get_round(seed.CLOSED_ROUND) == round_before
