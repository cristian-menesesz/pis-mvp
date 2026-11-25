from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from review_comments.api.app import create_app
from review_comments.application.service import CommentService
from review_comments.infrastructure.seed import seed_demo_data
from review_comments.infrastructure.sqlite_repository import SqliteCommentRepository

FIXED_NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """A fresh database file per test; pytest removes tmp_path afterwards."""
    return tmp_path / "review.db"


@pytest.fixture
def sqlite_repo(db_path: Path) -> SqliteCommentRepository:
    repository = SqliteCommentRepository(db_path)
    seed_demo_data(repository)
    return repository


@pytest.fixture
def client(sqlite_repo: SqliteCommentRepository) -> TestClient:
    """Real API -> real service -> real SQLite; only the clock is fixed."""
    service = CommentService(sqlite_repo, clock=lambda: FIXED_NOW)
    return TestClient(create_app(service))


def comment_rows(repository: SqliteCommentRepository) -> list[dict]:
    """Snapshot of the comments table, read through its own connection."""
    with repository.connect() as conn:
        rows = conn.execute("SELECT * FROM comments ORDER BY id").fetchall()
    return [dict(row) for row in rows]
