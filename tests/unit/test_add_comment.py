"""Unit tests for CommentService.add_comment (RF-01, RF-02).

The repository is replaced by an in-memory fake: these tests isolate the
service's rules and geometry. Persistence is verified in tests/integration.
"""

from datetime import UTC, datetime

import pytest

from review_comments.application.service import AddCommentCommand, CommentService
from review_comments.domain.errors import (
    BlankFieldError,
    EmptyStrokeError,
    NonFiniteCoordinateError,
    RegionOutsideItemError,
    RoundClosedError,
    VersionMismatchError,
)
from review_comments.domain.geometry import BoundingBox, Point
from review_comments.domain.models import ItemVersion, Round, RoundStatus
from tests.unit.fakes import InMemoryCommentRepository

pytestmark = pytest.mark.unit

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
OPEN = Round(id="r-open", status=RoundStatus.OPEN)
CLOSED = Round(id="r-closed", status=RoundStatus.CLOSED, closed_at=NOW)
POSTER_V1 = ItemVersion(id="poster-v1", item_id="poster", width=1200, height=800)
FLYER_V1 = ItemVersion(id="flyer-v1", item_id="flyer", width=500, height=500)


@pytest.fixture
def repo() -> InMemoryCommentRepository:
    return InMemoryCommentRepository(rounds=[OPEN, CLOSED], versions=[POSTER_V1, FLYER_V1])


@pytest.fixture
def service(repo: InMemoryCommentRepository) -> CommentService:
    return CommentService(repo, clock=lambda: NOW)


def command(**overrides) -> AddCommentCommand:
    fields = {
        "round_id": OPEN.id,
        "item_id": "poster",
        "version_id": "poster-v1",
        "stroke": [Point(100, 50), Point(400, 300), Point(250, 120)],
        "text": "Make the title bigger",
        "reviewer_name": "Luis (fictitious)",
    }
    fields.update(overrides)
    return AddCommentCommand(**fields)


def test_u01_valid_stroke_stores_comment_with_minimal_bounding_box(service, repo):
    comment = service.add_comment(command())

    assert comment.region == BoundingBox(x=100, y=50, width=300, height=250)
    assert (comment.round_id, comment.item_id, comment.version_id) == (
        "r-open",
        "poster",
        "poster-v1",
    )
    assert comment.text == "Make the title bigger"
    assert comment.reviewer_name == "Luis (fictitious)"
    assert comment.created_at == NOW
    assert repo.comments == [comment]


def test_u02_closed_round_rejects_comment_and_stores_nothing(service, repo):
    with pytest.raises(RoundClosedError):
        service.add_comment(command(round_id=CLOSED.id))

    assert repo.comments == []
    assert repo.rounds[CLOSED.id] == CLOSED


def test_u02b_closed_round_is_reported_before_input_problems(service, repo):
    """A closed round is the reason to report: fixing the input would not help.
    Added after mutation M2 survived (no test pinned this precedence)."""
    with pytest.raises(RoundClosedError):
        service.add_comment(command(round_id=CLOSED.id, text="   ", stroke=[]))

    assert repo.comments == []


# U-03: boundaries of the region rule and of the required input.


def test_u03a_single_point_stroke_gives_zero_size_box_at_that_point(service):
    comment = service.add_comment(command(stroke=[Point(300, 200)]))

    assert comment.region == BoundingBox(x=300, y=200, width=0, height=0)


def test_u03b_stroke_crossing_item_edges_is_clipped_to_item(service):
    comment = service.add_comment(command(stroke=[Point(-50, 700), Point(1300, 900)]))

    assert comment.region == BoundingBox(x=0, y=700, width=1200, height=100)


def test_u03c_stroke_touching_item_border_is_accepted_on_the_border(service):
    comment = service.add_comment(command(stroke=[Point(1200, 0), Point(1250, 40)]))

    assert comment.region == BoundingBox(x=1200, y=0, width=0, height=40)


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        pytest.param({"stroke": []}, EmptyStrokeError, id="empty-stroke"),
        pytest.param(
            {"stroke": [Point(1201, 10), Point(1500, 90)]},
            RegionOutsideItemError,
            id="stroke-fully-outside",
        ),
        pytest.param(
            {"stroke": [Point(float("nan"), 10)]}, NonFiniteCoordinateError, id="nan-coordinate"
        ),
        pytest.param({"text": "   "}, BlankFieldError, id="blank-text"),
        pytest.param({"reviewer_name": ""}, BlankFieldError, id="blank-reviewer"),
        pytest.param({"version_id": "flyer-v1"}, VersionMismatchError, id="version-of-other-item"),
    ],
)
def test_u03d_invalid_input_is_rejected_and_nothing_is_stored(service, repo, overrides, error):
    with pytest.raises(error):
        service.add_comment(command(**overrides))

    assert repo.comments == []


def test_u04_reviewer_text_is_stored_exactly_as_written(service):
    original = "  el logo, más grande!!  "

    comment = service.add_comment(command(text=original))

    assert comment.text == original


def test_u05_round_closed_between_check_and_write_is_reported_as_closed(service, repo):
    """The repository refuses the write (round closed concurrently): the service
    must surface RoundClosedError, never a fictitious success."""
    repo.add_comment_if_round_open = lambda _comment: None

    with pytest.raises(RoundClosedError):
        service.add_comment(command())
