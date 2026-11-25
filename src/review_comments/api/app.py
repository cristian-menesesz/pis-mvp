"""HTTP contract for anchored comments.

POST /rounds/{round_id}/comments  201 stored | 404 unknown round/version
                                  409 round closed | 422 invalid input
GET  /comments/{comment_id}       200 | 404
POST /rounds/{round_id}/close     200 (also when already closed) | 404
"""

import os
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from review_comments.application.service import AddCommentCommand, CommentService
from review_comments.domain.errors import (
    DomainError,
    InvalidCommentError,
    NotFoundError,
    RoundClosedError,
)
from review_comments.domain.geometry import Point
from review_comments.domain.models import Comment, Round
from review_comments.infrastructure.sqlite_repository import SqliteCommentRepository


class PointIn(BaseModel):
    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)


class CommentIn(BaseModel):
    item_id: str
    version_id: str
    stroke: list[PointIn]
    text: str
    reviewer_name: str


class RegionOut(BaseModel):
    x: float
    y: float
    width: float
    height: float


class CommentOut(BaseModel):
    id: int
    round_id: str
    item_id: str
    version_id: str
    region: RegionOut
    text: str
    reviewer_name: str
    created_at: datetime

    @classmethod
    def from_domain(cls, comment: Comment) -> "CommentOut":
        r = comment.region
        return cls(
            id=comment.id,
            round_id=comment.round_id,
            item_id=comment.item_id,
            version_id=comment.version_id,
            region=RegionOut(x=r.x, y=r.y, width=r.width, height=r.height),
            text=comment.text,
            reviewer_name=comment.reviewer_name,
            created_at=comment.created_at,
        )


class RoundOut(BaseModel):
    id: str
    status: str
    closed_at: datetime | None

    @classmethod
    def from_domain(cls, round_: Round) -> "RoundOut":
        return cls(id=round_.id, status=round_.status.value, closed_at=round_.closed_at)


_STATUS_BY_ERROR: list[tuple[type[DomainError], int, str]] = [
    (NotFoundError, status.HTTP_404_NOT_FOUND, "not_found"),
    (RoundClosedError, status.HTTP_409_CONFLICT, "round_closed"),
    (InvalidCommentError, status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_comment"),
]


def create_app(service: CommentService | None = None) -> FastAPI:
    """Build the app. Without an explicit service, it uses the SQLite file named
    by REVIEW_DB_PATH (default: review.db)."""
    if service is None:
        repository = SqliteCommentRepository(os.environ.get("REVIEW_DB_PATH", "review.db"))
        repository.initialize()
        service = CommentService(repository)

    app = FastAPI(title="Anchored review comments")

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        for error_type, http_status, code in _STATUS_BY_ERROR:
            if isinstance(exc, error_type):
                return JSONResponse(
                    status_code=http_status, content={"error": code, "detail": str(exc)}
                )
        return JSONResponse(status_code=500, content={"error": "domain_error", "detail": str(exc)})

    @app.post(
        "/rounds/{round_id}/comments",
        status_code=status.HTTP_201_CREATED,
        response_model=CommentOut,
    )
    def add_comment(round_id: str, body: CommentIn) -> CommentOut:
        comment = service.add_comment(
            AddCommentCommand(
                round_id=round_id,
                item_id=body.item_id,
                version_id=body.version_id,
                stroke=[Point(p.x, p.y) for p in body.stroke],
                text=body.text,
                reviewer_name=body.reviewer_name,
            )
        )
        return CommentOut.from_domain(comment)

    @app.get("/comments/{comment_id}", response_model=CommentOut)
    def get_comment(comment_id: int) -> CommentOut:
        return CommentOut.from_domain(service.get_comment(comment_id))

    @app.post("/rounds/{round_id}/close", response_model=RoundOut)
    def close_round(round_id: str) -> RoundOut:
        return RoundOut.from_domain(service.close_round(round_id))

    return app
