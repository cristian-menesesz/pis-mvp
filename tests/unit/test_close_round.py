"""Unit tests for CommentService.close_round and get_comment (RF-03)."""

from datetime import UTC, datetime, timedelta

import pytest

from review_comments.application.service import CommentService
from review_comments.domain.errors import NotFoundError
from review_comments.domain.models import Round, RoundStatus
from tests.unit.fakes import InMemoryCommentRepository

pytestmark = pytest.mark.unit

T0 = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


def test_u06_closing_twice_keeps_first_closing_time():
    repo = InMemoryCommentRepository(rounds=[Round(id="r1", status=RoundStatus.OPEN)], versions=[])
    ticks = iter([T0, T0 + timedelta(hours=1)])
    service = CommentService(repo, clock=lambda: next(ticks))

    first = service.close_round("r1")
    second = service.close_round("r1")

    assert first == Round(id="r1", status=RoundStatus.CLOSED, closed_at=T0)
    assert second == first


def test_u07_unknown_round_or_comment_is_not_found():
    service = CommentService(InMemoryCommentRepository(rounds=[], versions=[]))

    with pytest.raises(NotFoundError):
        service.close_round("missing")
    with pytest.raises(NotFoundError):
        service.get_comment(999)
