from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from review_comments.domain.geometry import BoundingBox


class RoundStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class Round:
    id: str
    status: RoundStatus
    closed_at: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.status is RoundStatus.OPEN


@dataclass(frozen=True, slots=True)
class ItemVersion:
    """One uploaded version of an item; comments anchor to a version because
    layout can change between versions."""

    id: str
    item_id: str
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class NewComment:
    round_id: str
    item_id: str
    version_id: str
    region: BoundingBox
    text: str
    reviewer_name: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Comment:
    id: int
    round_id: str
    item_id: str
    version_id: str
    region: BoundingBox
    text: str
    reviewer_name: str
    created_at: datetime
