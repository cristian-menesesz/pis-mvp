from dataclasses import replace
from datetime import datetime

from review_comments.domain.models import (
    Comment,
    ItemVersion,
    NewComment,
    Round,
    RoundStatus,
)


class InMemoryCommentRepository:
    """Fake honouring the CommentRepository contract, so unit tests observe the
    service's effects (what was stored) without a database."""

    def __init__(self, rounds: list[Round], versions: list[ItemVersion]) -> None:
        self.rounds = {r.id: r for r in rounds}
        self.versions = {v.id: v for v in versions}
        self.comments: list[Comment] = []

    def get_round(self, round_id: str) -> Round | None:
        return self.rounds.get(round_id)

    def get_version(self, version_id: str) -> ItemVersion | None:
        return self.versions.get(version_id)

    def get_comment(self, comment_id: int) -> Comment | None:
        return next((c for c in self.comments if c.id == comment_id), None)

    def add_comment_if_round_open(self, comment: NewComment) -> Comment | None:
        round_ = self.rounds.get(comment.round_id)
        if round_ is None or not round_.is_open:
            return None
        stored = Comment(id=len(self.comments) + 1, **_fields(comment))
        self.comments.append(stored)
        return stored

    def close_round(self, round_id: str, closed_at: datetime) -> Round | None:
        round_ = self.rounds.get(round_id)
        if round_ is not None and round_.is_open:
            round_ = replace(round_, status=RoundStatus.CLOSED, closed_at=closed_at)
            self.rounds[round_id] = round_
        return round_


def _fields(comment: NewComment) -> dict:
    return {
        "round_id": comment.round_id,
        "item_id": comment.item_id,
        "version_id": comment.version_id,
        "region": comment.region,
        "text": comment.text,
        "reviewer_name": comment.reviewer_name,
        "created_at": comment.created_at,
    }
