"""Stress probe for the open-round invariant under real concurrency.

N threads submit comments to the same open round while another thread closes
it, all through the HTTP API and one SQLite file. Afterwards it checks:

- commit order (exact): a probe-only trigger records the highest comment id at
  the moment the round is closed; no comment of the round may have a higher id.
- every 201 corresponds to exactly one stored row.
- history (timestamps): no accepted comment has created_at later than the
  round's closed_at (DEF-02).

Timestamps alone cannot prove commit order: each one is read from the
application clock before its write is serialized by SQLite.

The interleaving is decided by the OS scheduler, so the 201/409 split varies
between runs; the invariant must hold in every run. The deterministic
version of this race is tests/failure (F-02).

Usage: uv run python scripts/concurrency_probe.py [threads] [runs]
"""

import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from review_comments.api.app import create_app
from review_comments.application.service import CommentService
from review_comments.infrastructure import seed
from review_comments.infrastructure.sqlite_repository import SqliteCommentRepository

PAYLOAD = {
    "item_id": seed.POSTER,
    "version_id": seed.POSTER_V1,
    "stroke": [{"x": 10, "y": 10}, {"x": 60, "y": 40}],
    "text": "Comentario concurrente",
    "reviewer_name": "Luis (fictitious)",
}


def run_once(threads: int) -> tuple[dict[int, int], int, int, int]:
    with tempfile.TemporaryDirectory() as tmp:
        repository = SqliteCommentRepository(Path(tmp) / "probe.db")
        seed.seed_demo_data(repository)
        with repository.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE probe_close_log (max_comment_id INTEGER NOT NULL);
                CREATE TRIGGER probe_on_close AFTER UPDATE OF status ON rounds
                WHEN NEW.status = 'closed'
                BEGIN
                    INSERT INTO probe_close_log SELECT coalesce(max(id), 0) FROM comments;
                END;
                """
            )
        client = TestClient(create_app(CommentService(repository)))
        codes: list[int] = []
        lock = threading.Lock()

        def submit() -> None:
            status = client.post(f"/rounds/{seed.OPEN_ROUND}/comments", json=PAYLOAD).status_code
            with lock:
                codes.append(status)

        workers = [threading.Thread(target=submit) for _ in range(threads)]
        closer = threading.Thread(target=lambda: client.post(f"/rounds/{seed.OPEN_ROUND}/close"))
        half = threads // 2
        for t in workers[:half]:
            t.start()
        closer.start()
        for t in workers[half:]:
            t.start()
        for t in [*workers, closer]:
            t.join()

        with repository.connect() as conn:
            rows = conn.execute(
                "SELECT id, created_at FROM comments WHERE round_id = ?", (seed.OPEN_ROUND,)
            ).fetchall()
            closed_at = datetime.fromisoformat(
                conn.execute(
                    "SELECT closed_at FROM rounds WHERE id = ?", (seed.OPEN_ROUND,)
                ).fetchone()[0]
            )
            max_id_at_close = conn.execute("SELECT max_comment_id FROM probe_close_log").fetchone()[0]

    tally = {code: codes.count(code) for code in sorted(set(codes))}
    committed_after_close = sum(1 for r in rows if r[0] > max_id_at_close)
    stamped_after_close = sum(1 for r in rows if datetime.fromisoformat(r[1]) > closed_at)
    mismatch = abs(tally.get(201, 0) - len(rows))
    return tally, committed_after_close, stamped_after_close, mismatch


def main() -> int:
    threads = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    violations = 0
    for i in range(1, runs + 1):
        tally, committed, stamped, mismatch = run_once(threads)
        ok = committed == 0 and stamped == 0 and mismatch == 0 and set(tally) <= {201, 409}
        violations += not ok
        print(
            f"run {i:2}: status={tally} committed_after_close={committed} "
            f"stamped_after_close={stamped} 201_vs_rows_mismatch={mismatch} "
            f"{'OK' if ok else 'VIOLATION'}"
        )
    print(f"\n{runs - violations}/{runs} runs kept the invariant ({threads} threads each)")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
