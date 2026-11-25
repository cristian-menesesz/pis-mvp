"""Turns a free-hand stroke into the rectangular region that anchors a comment.

Coordinates are in the item version's pixel space: origin at the top-left
corner, x grows to the right, y grows downwards.
"""

import math
from collections.abc import Iterable
from dataclasses import dataclass

from review_comments.domain.errors import (
    EmptyStrokeError,
    NonFiniteCoordinateError,
    RegionOutsideItemError,
)


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


def bounding_box(stroke: Iterable[Point]) -> BoundingBox:
    """Smallest axis-aligned rectangle containing every stroke point.

    A single point (or identical points) yields a zero-size box: the project
    decided to keep it as a point marker instead of rejecting it.
    """
    points = list(stroke)
    if not points:
        raise EmptyStrokeError()
    if not all(math.isfinite(p.x) and math.isfinite(p.y) for p in points):
        raise NonFiniteCoordinateError()

    left = min(p.x for p in points)
    top = min(p.y for p in points)
    right = max(p.x for p in points)
    bottom = max(p.y for p in points)
    return BoundingBox(x=left, y=top, width=right - left, height=bottom - top)


def clip_to_item(box: BoundingBox, item_width: float, item_height: float) -> BoundingBox:
    """Restrict the box to the item's area [0, width] x [0, height].

    Edges are inclusive, so a box touching the item border still anchors to
    it. A box with no point in common with the item anchors to nothing and is
    rejected.
    """
    if box.x > item_width or box.right < 0 or box.y > item_height or box.bottom < 0:
        raise RegionOutsideItemError()

    left = max(box.x, 0.0)
    top = max(box.y, 0.0)
    right = min(box.right, item_width)
    bottom = min(box.bottom, item_height)
    return BoundingBox(x=left, y=top, width=right - left, height=bottom - top)
