"""Domain errors. Each class carries one meaning so callers can react precisely
instead of receiving a generic failure."""


class DomainError(Exception):
    """Base class for every rule the domain refuses to break."""


class NotFoundError(DomainError):
    """A referenced round or item version does not exist."""

    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} '{entity_id}' does not exist")
        self.entity = entity
        self.entity_id = entity_id


class RoundClosedError(DomainError):
    """Comments are only accepted while the round is open (RF-02)."""

    def __init__(self, round_id: str) -> None:
        super().__init__(f"round '{round_id}' is closed; no comments are accepted")
        self.round_id = round_id


class InvalidCommentError(DomainError):
    """The comment request itself is malformed; fixing the input fixes it."""


class EmptyStrokeError(InvalidCommentError):
    def __init__(self) -> None:
        super().__init__("the stroke has no points; a region cannot be computed")


class NonFiniteCoordinateError(InvalidCommentError):
    def __init__(self) -> None:
        super().__init__("stroke coordinates must be finite numbers")


class RegionOutsideItemError(InvalidCommentError):
    def __init__(self) -> None:
        super().__init__("the marked region lies completely outside the item")


class BlankFieldError(InvalidCommentError):
    def __init__(self, field: str) -> None:
        super().__init__(f"'{field}' is required and cannot be blank")
        self.field = field


class VersionMismatchError(InvalidCommentError):
    def __init__(self, version_id: str, item_id: str) -> None:
        super().__init__(f"version '{version_id}' does not belong to item '{item_id}'")
