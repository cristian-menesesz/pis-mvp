from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from review_comments.application.ports import CommentRepository
from review_comments.domain.errors import (
    BlankFieldError,
    NotFoundError,
    RoundClosedError,
    VersionMismatchError,
)
from review_comments.domain.geometry import Point, bounding_box, clip_to_item
from review_comments.domain.models import Comment, NewComment, Round

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class AddCommentCommand:
    round_id: str
    item_id: str
    version_id: str
    stroke: Sequence[Point]
    text: str
    reviewer_name: str


class CommentService:
    """Use cases for anchored comments: register (RF-01, RF-02), retrieve,
    and close a round (RF-03)."""

    def __init__(self, repository: CommentRepository, clock: Clock = utc_now) -> None:
        self._repository = repository
        self._clock = clock

    def add_comment(self, command: AddCommentCommand) -> Comment:
        round_ = self._repository.get_round(command.round_id)
        if round_ is None:
            raise NotFoundError("round", command.round_id)
        if not round_.is_open:
            raise RoundClosedError(round_.id)

        version = self._repository.get_version(command.version_id)
        if version is None:
            raise NotFoundError("version", command.version_id)
        if version.item_id != command.item_id:
            raise VersionMismatchError(command.version_id, command.item_id)

        # Blank checks look at the stripped value, but the reviewer's words are
        # stored exactly as written: the original text is never rewritten.
        if not command.text.strip():
            raise BlankFieldError("text")
        if not command.reviewer_name.strip():
            raise BlankFieldError("reviewer_name")

        region = clip_to_item(bounding_box(command.stroke), version.width, version.height)

        stored = self._repository.add_comment_if_round_open(
            NewComment(
                round_id=round_.id,
                item_id=command.item_id,
                version_id=version.id,
                region=region,
                text=command.text,
                reviewer_name=command.reviewer_name,
                created_at=self._clock(),
            )
        )
        if stored is None:
            # The round was closed between the check above and the write.
            raise RoundClosedError(round_.id)
        return stored

    def get_comment(self, comment_id: int) -> Comment:
        comment = self._repository.get_comment(comment_id)
        if comment is None:
            raise NotFoundError("comment", str(comment_id))
        return comment

    def close_round(self, round_id: str) -> Round:
        closed = self._repository.close_round(round_id, self._clock())
        if closed is None:
            raise NotFoundError("round", round_id)
        return closed
