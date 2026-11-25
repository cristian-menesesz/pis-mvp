from datetime import datetime
from typing import Protocol

from review_comments.domain.models import Comment, ItemVersion, NewComment, Round


class CommentRepository(Protocol):
    """Persistence contract the service depends on. Implementations must make
    `add_comment_if_round_open` atomic: the open-round check and the insert
    happen as one indivisible step."""

    def get_round(self, round_id: str) -> Round | None: ...

    def get_version(self, version_id: str) -> ItemVersion | None: ...

    def get_comment(self, comment_id: int) -> Comment | None: ...

    def add_comment_if_round_open(self, comment: NewComment) -> Comment | None:
        """Store the comment only if its round is open at write time.

        Returns the stored comment, or None when the round was not open,
        in which case nothing is stored."""
        ...

    def close_round(self, round_id: str, closed_at: datetime) -> Round | None:
        """Close the round if it is open; a closed round keeps its original
        `closed_at`. Returns the round as stored, or None if it does not exist."""
        ...
